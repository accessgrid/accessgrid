import time
import os
from AccessGrid.hosting import AccessControl
from AccessGrid.hosting.pyGlobus import Server, ServiceBase

class C(ServiceBase.ServiceBase):
    def meth(self, x):

        print "Got meth: ", x

        sm = AccessControl.GetSecurityManager()

        print "Executing as subject name: ", sm.GetSubject()

        raise Exception("foo")

#        ident = "/O=Grid/OU=Access Grid/OU=mcs.anl.gov/CN=Bob Olson"
#        if not sm.ValidateUser(ident):
#            raise Exception("Invalid user!")
        
        return ('you sent', x)
    

    meth.pass_connection_info = 0
    meth.soap_export_as = "method"

def cb(server, g_handle, remote_user, context):
    print "%s Got cb %s" % (clk(), remote_user)
    return 1

if __name__ == "__main__":

    server = Server.Server(8000, auth_callback = cb)

    s = server.create_service(C)

    print "Have %s %s" % (s, s.get_handle())

    server.run_in_thread()

    try:
        while 1:
            time.sleep(1)

    except Exception, e:
        print "gotkeybaord int", e
        os._exit(0)
        print "Exit done"
                                    
