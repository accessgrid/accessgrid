import Server
import ServiceBase

class C(ServiceBase.ServiceBase):
    def meth(self, cinfo, x, **kargs):
        print "Got meth ", cinfo, x, kargs
        return ('you sent', cinfo, x)

    meth.pass_connection_info = 1
    meth.soap_export_as = "method"

if __name__ == "__main__":

    server = Server.Server(8000)

    s = server.create_service(C)

    print "Have %s %s" % (s, s.get_handle())

    server.run()
