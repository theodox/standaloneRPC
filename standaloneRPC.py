'''
standaloneRPC

Cheapass server to control a remote instance of maya.standalone using a bare-bones RPC setup.

To use as a server, execute this file from the MayaPy interpeter:

    mayapy.exe   path/to/standaloneRPC.py

to connect to a server and issue commands:

    import standaloneRPC as srpc
    cmd = srpc.CMD('cmds.ls', type='transform')
    srpc.send_command(cmd)
    >>> {success:True, result:[u'persp', u'top', u'side', u'front'}

See the CMD class and send_command methods for details.


IMPORTANT

This is NOT an attempt at a full-blown rpc server!  It's a quick way for maya users
to control a maya standalone instance without the commandPort!

As such, this provides NO security so anyone who knew that an instance was
running will have complete control over the target machine! This is DANGEROUS.
Do not expose a standlone running this directly to the internet!

This also makes no effort to providing proxy services or marshalling - only basic data 
types can be sent and received. 

To drive these points home, we do not use the standard JSON-RPC protocol. That is to make sure
this doesn't get confused with a real, robust, and secure  RPC serrver.

If you want something more robust, sophisticated and general you should check out 

    JSON-RPC https://pypi.python.org/pypi/json-rpc 
or

    TINYRPC https://pypi.python.org/pypi/tinyrpc/0.5.

or 

    RPYC    http://rpyc.readthedocs.org/en/latest/

'''

import sys
import json
import urlparse
import socket
import urllib2
import traceback
from wsgiref.simple_server import make_server
import urllib
import maya.cmds as cmds




class CMD(str):
    '''
    turn a command with arguments and keywords into a web-friendly encoded string
    
    print CMD('cmds.ls', type='transform')
    'command=cmds.ls&kwargs=%7B%22type%22%3A+%22transform%22%7D'

    pass this to send_command so you don't have to manually create query strings
    '''
    def __new__(cls, cmd, *args, **kwargs):
        result = {'command': str(cmd)}
        if args:
            result['args'] = json.dumps(args)
        if kwargs:
            result['kwargs'] = json.dumps(kwargs)
        return urllib.urlencode(result)


def send_command(cmd, address = '127.0.0.1', port = 8000):
    '''
    send the CMD object 'cmd' to the server at <address>:<port>.  Returns the
    json-decoded results
    
    The return value will always be a json object with the keyword 'succes'. If
    'success' is true, the command executed; if it is false, it excepted on the
    server side.
    
    For successful queries, the object will include a field called 'results'
    containg a json-encoded version of the results:
        
        cmd = CMD('cmds.ls', type='transform')
        print send_command(cmd)
        >>> {success:True, result:[u'persp', u'top', u'side', u'front'}
    
    For failed queries, the result includes the exception and a traceback string:

        cmd = CMD('cmds.fred')  # nonexistent command
        print send_command(cmd)
        >>> {"exception": "<type 'exceptions.AttributeError'>", 
             "traceback": "Traceback (most recent call last)... #SNIP#",
             "success": false, 
             "args": "[]", 
             "kwargs": "{}", 
             "cmd_name": "cmds.fred"}

    Sending the string 'shutdown' on its own as the command (not encoded as a
    CMD) will request the server to quit.
    '''
    
    url = "http://{address}:{port}/?{cmd}".format(address = address, port = port, cmd = cmd)
    q= urllib2.urlopen(url)
    raw = q.read()
    try:
        results = json.loads(raw)
        return results
    except:
        raise ValueError ("Could not parse server responss", raw)
                          


def handle_command  (environ, response):
        '''
        look for a query string with 'command' in it; eval the string and
        execute. Args and KWargs can be passed as json objects. The command will
        be evaluated in the global namespace.
        
        This can be done by hand in a browser address bar, but it's easies to
        use the CMD class
        
        http://192.168.1.105:8000/?command=cmds.ls
        http://192.168.1.105:8000/?command=cmds.ls&kwargs{"type":"transform"}

        If the query string command is 'shutdown', quit maya.standalone
        '''

        if not environ.get('QUERY_STRING'):
            status = '404 Not Found'
            headers = [('Content-type', 'text/plain')]
            response(status, headers)
            return ["You must supply a command as a query string"]

        query = urlparse.parse_qs( environ['QUERY_STRING'] )
        status = '200 OK'
        headers = [('Content-type', 'text/plain')]
        response(status, headers)

        cmds_string = query.get('command')
        if not cmds_string:
            return ['No recognized command']
        
        cmd_name = "-"
        args = "-"
        kwargs = "-"
                        
        try:
            cmd_name = cmds_string[0]
            args = query.get('args') or []
            if args: 
                args = json.loads(args[0])

            kwargs = query.get('kwargs') or {}
            if kwargs: 
                # convert json dictionary to a string rather than unicode keyed dict
                unicode_kwargs = json.loads(kwargs[0])
                kwargs = dict( ( str(k), v) for k, v in unicode_kwargs.items())

            cmd_proc = eval(cmd_name)
            if cmd_name == 'shutdown':
                try:
                    return ['SERVER SHUTTING DOWN']
                finally:
                    cmd_proc()
            
            result = cmd_proc(*args, **kwargs)
            result_js = {'success':True, 'result': result }
            return [json.dumps(result_js)]
        
        except:
            result_js = {"success": False,
                         "cmd_name": cmd_name, 
                      "args": str(args) or "-", 
                      "kwargs" : str(kwargs)or "-", 
                      "exception": str(sys.exc_info()[0]),
                      "traceback": traceback.format_exc()}
            return [json.dumps(result_js)]
        
        
        

                               

def create_server(port=None):
    '''
    create a server instance
    '''
    port = port or 8000
    address = socket.gethostbyname(socket.gethostname())
    server = make_server(address, port, handle_command)    
    return server, address, port



#===============================================================================
# #Run the server when run as a script        
#===============================================================================
if __name__ == '__main__':
    import maya.standalone
    maya.standalone.initialize()
    server_instance, address, port = create_server()       

    # defined here so we don't need a global server reference...    
    def shutdown():
        print  "*" * 80
        print "shutting down"
        print "*" * 80
        cmds.quit(force=True)
        server_instance.shutdown()
        raise sys.exit(0)
        
    print "=" * 80
    print ("starting server on %s:%s" % (address,port)).center(80)
    print "=" * 80

    server_instance.serve_forever()
      