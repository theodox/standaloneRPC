standaloneRPC
=============

Provides a simple RPC server for controlling a maya.standalone instance remotely.

To use as a server, execute this file from the MayaPy interpeter:

    mayapy.exe   path/to/standaloneRPC.py

to connect to a server and issue commands:

    import standaloneRPC as srpc
    cmd = srpc.CMD('cmds.ls', type='transform')
    srpc.send_command(cmd)
    >>> {success:True, result:[u'persp', u'top', u'side', u'front'}

See the CMD class and send_command methods for details.


IMPORTANT
=========

This module is NOT an attempt to provide a full-blown rpc server!  It's a quick way 
for maya users to control a maya standalone instance without the commandPort!

As such, this provides **NO security** so anyone who knew that an instance was
running will have complete control over the target machine! This is **DANGEROUS** 
outside of controlled conditions! Do not expose a standalone running this to
the internet.

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
    

### Update 4/12/14

I've added  a separate branch with minimal password security. It won't stop real hackers but it should suffice to keep your coworkers from pranking you.  Its in the [more secure](https://github.com/theodox/standaloneRPC/tree/more-secure) branch
