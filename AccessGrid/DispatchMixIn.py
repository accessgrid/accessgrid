

def NullFunc(*args,**kwargs):
    pass


class DispatchObj:
    def __init__(self,description):
    
        if not hasattr(description,'serviceIWClass'):
            raise Exception('Description class %s lacks necessary attribute: serviceClassIW' % description.__class__ )
        elif not hasattr(description,'uri'):
            raise Exception('Description class %s lacks necessary attribute: uri' % description.__class__ )

        self.description = description
        self.localObject = None
        
    def SetObject(self,localObject):
        self.localObject = localObject
        
    def __getattr__(self,name):
        obj = self.localObject or self.description.serviceIWClass(self.description.uri)
        if obj:
            attr = getattr(obj,name)
        else:
            attr = NullFunc
        return attr

class DispatchMixIn:
    """
    Class to add some object indirection support to description classes.
    This will essentially make description objects callable.  Descriptions
    typically describe an RPC endpoint reachable at the uri included in the
    description.  This class will make it possible to call the RPC endpoint
    at that URI implicitly.  The big value, however, is that if a local
    object is assigned to the description, /it/ will be used instead,
    saving the overhead of a network call.
    
    Requires:  ServiceDescription class must have the following attributes:
        uri:            the address of the RPC endpoint
        serviceIWClass: the interface wrapper class used to call the endpoint
        
    Typical Use:  See example below.
    """
    
    __slots__ = ['__obj','__dispatchObj']
    def __init__(self):
        self.obj = DispatchObj(self)
    def SetObject(self,localObject):
        self.obj.SetObject(localObject)
    def GetObject(self):
        return self.obj


if __name__ == '__main__':
        
    class Obj:
        def func(self,a):
            return 'Obj.func'

    class ServiceIW:
        def __init__(self,uri):
            self.uri = uri
        def func(self,a):
            return 'Proxy.func ' + self.uri

    class Description(DispatchMixIn):
        def __init__(self,uri=None):
            self.serviceIWClass = ServiceIW
            self.uri = uri
            DispatchMixIn.__init__(self)

    # Calls against the obj attribute in this description will go over RPC
    pd = Description('http://server:port/servicename')
    print pd.obj.func(1)

    # Calls against the obj attribute in this description will be made internally
    od = Description('http://server:port/servicename')
    od.SetObject(Obj())
    print od.obj.func(1)

