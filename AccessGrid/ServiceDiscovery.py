#!/usr/bin/python
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Service Advertisement and Discovery module
#
# This module provides a mechanism for advertising services
# and discovering them.  At present, it uses rendezvous to 
# do this.  An alternative model could use local network
# broadcast; in fact, it'd be a good idea to implement this
# alternative to fall back to when rendezvous is not available.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import threading
import select
import time

from AccessGrid import Log

class PublisherError(Exception):  pass
class BrowserError(Exception):    pass

# No-op classes to use in absence of rendezvous
class _Publisher:
    def __init__(self,serviceName,regtype,url,port=9999):   
        pass
    def Stop(self): 
        pass
    def IsRegistered(self):
        pass
class _Browser:
    def __init__(self,serviceType,browseCallback=None):
        pass
    def Start(self):
        pass
    def Stop(self):
        pass
    def Run(self):
        pass
    def IsRunning(self):
        pass
    def GetServices(self):
        pass

log = Log.GetLogger('ServiceDiscovery')

try:
    import rendezvous

    class RendezvousPublisher:

        def __init__(self,serviceName,regtype,url,port=9999):

            if port == 0:
                raise PublisherError('Service registered with invalid port %d' % (port,))

            self.serviceRef = None

            self.registerFlag = threading.Event()

            # Allocate a text record
            txtRecord = rendezvous.AllocateTXTRecordRef()
            rendezvous.pyTXTRecordCreate(txtRecord)
            rendezvous.pyTXTRecordSetValue(txtRecord,"url",url)
            txtRecordLen = rendezvous.pyTXTRecordGetLength(txtRecord)
            txtRecordBytes = rendezvous.pyTXTRecordGetBytesPtr(txtRecord)

            # Allocate a service discovery reference and register the specified service
            self.serviceRef = rendezvous.AllocateDNSServiceRef()
            ret = rendezvous.pyDNSServiceRegister(self.serviceRef, 
                                          0,                  
                                          0,                  
                                          serviceName,        
                                          regtype,            
                                          'local.',           
                                          'munich',           
                                          port,               
                                          txtRecordLen,       
                                          txtRecordBytes,     
                                          self.__RegisterCallback,   
                                          None)

            if ret != rendezvous.kDNSServiceErr_NoError:
                raise PublisherError(ret)
                
            # Get the socket and loop
            fd = rendezvous.DNSServiceRefSockFD(self.serviceRef)
            ret = select.select([fd],[],[])
            if ret[0]:
                ret = rendezvous.DNSServiceProcessResult(self.serviceRef)

        def __RegisterCallback(self,sdRef,flags,errorCode,name,regtype,domain,userdata):
            self.registerFlag.set()

        def Stop(self):
            # Deallocate the service discovery ref
            if self.serviceRef:
                rendezvous.DNSServiceRefDeallocate(self.serviceRef)

        def IsRegistered(self):
            return self.registerFlag.isSet()




    class RendezvousBrowser:

        ADD = 1
        DELETE = 2

        def __init__(self,serviceType,browseCallback=None):
            """

            browseCallback: a function to be called on changes to the 
                            browsed services.  
            """
            self.serviceType = serviceType
            self.browseCallback = browseCallback
            self.serviceRef = None
            self.serviceUrls = dict()
            self.lock = threading.Lock()

            # Timeout to use in select loop, to permit
            # loop to check for shutdown
            self.timeout = 2

        def __del__(self):
            # Deallocate the service discovery ref
            if self.serviceRef:
                rendezvous.DNSServiceRefDeallocate(self.serviceRef)

        def __BrowseCallback(self,sdRef,flags,interfaceIndex,
                           errorCode,serviceName,regtype,
                           replyDomain,userdata):

            if flags & rendezvous.kDNSServiceFlagsAdd:
                sdRef2 = rendezvous.AllocateDNSServiceRef()
                ret = rendezvous.pyDNSServiceResolve(sdRef2,
                                                  0,
                                                  0,
                                                  serviceName,
                                                  regtype,
                                                  replyDomain,
                                                  self.__ResolveCallback,
                                                  serviceName );

                rendezvous.DNSServiceProcessResult(sdRef2)
                rendezvous.DNSServiceRefDeallocate(sdRef2)

            elif flags == 0:
                self.lock.acquire()
                del self.serviceUrls[serviceName]
                self.lock.release()

                # Call callback (if registered) to signal delete
                if self.browseCallback:
                    self.browseCallback(self.DELETE,serviceName)

        def __ResolveCallback(self,sdRef,flags,interfaceIndex,
                            errorCode,fullname,hosttarget,
                            port,txtLen,txtRecord,userdata):

            # Get service info and add to list
            serviceName = userdata
            url = rendezvous.pyTXTRecordGetValue(txtLen,txtRecord,"url")

            self.lock.acquire()
            self.serviceUrls[serviceName] = url
            self.lock.release()

            # Call callback (to signal add), if registered
            if self.browseCallback:
                self.browseCallback(self.ADD,serviceName,url)


        def Start(self):
            t = threading.Thread(target=self.Run)
            t.start()

        def Run(self):

            self.running = 1

            # Allocate a service discovery ref and browse for the specified service type
            self.serviceRef = rendezvous.AllocateDNSServiceRef()
            ret = rendezvous.pyDNSServiceBrowse(self.serviceRef,  
                                          0,                   
                                          0,                   
                                          self.serviceType,                
                                          'local.',            
                                          self.__BrowseCallback,      
                                          None)
            if ret != rendezvous.kDNSServiceErr_NoError:
                print "ret = %d; exiting" % ret
                raise BrowserError('browse',ret)

            # Get socket descriptor                      
            fd = rendezvous.DNSServiceRefSockFD(self.serviceRef)

            if fd <= 0:
                raise BrowserError('fd',fd)

            # Loop
            while self.IsRunning():
                # print "do select"
                ret = select.select([fd],[],[],self.timeout)
                if ret[0]:  
                    #print "do process result"
                    ret = rendezvous.DNSServiceProcessResult(self.serviceRef)
                    if ret != rendezvous.kDNSServiceErr_NoError:
                        raise BrowserError('processresult',ret)

        def Stop(self):
            self.running = 0

        def IsRunning(self):
            return self.running

        def GetServices(self):
            self.lock.acquire()
            urls = self.serviceUrls
            self.lock.release()
            return urls
            
            
    Publisher = RendezvousPublisher
    Browser = RendezvousBrowser
except ImportError,e:
    log.info("Failed to import rendezvous; service discovery disabled")
    Publisher = _Publisher
    Browser = _Browser


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Main
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

deleteFlag = threading.Event()

def BrowseCB(op,serviceName,url=None):
    if op == Browser.ADD:
        print "Added service:", serviceName, url
    elif op == Browser.DELETE:
        print "Deleted service:", serviceName
        deleteFlag.set()
    

if __name__ == "__main__":

    serviceName = 'myservice'
    serviceType = '_ftp._tcp'
    serviceUrl  = 'http://localhost:9876/my/service'

    print "* Registering service: ", serviceName, serviceType
    p = Publisher(serviceName,serviceType,serviceUrl,port=9876)
    
    print "* Browsing for service: "
    b = Browser(serviceType,BrowseCB)
    b.Start()
    
    timeToSleep = 3
    print "* Wait a bit (%ds) to delete service" % (timeToSleep,)
    now = time.time()
    while time.time() - now < timeToSleep:
        time.sleep(1)
        
    print "* Test GetServices"
    services = b.GetServices()
    if services:
        print "Found services:"
        for name,url in services.items():
            print "  ", name,url
        
    print "* Deleting service"
    p.Stop()
    
    print "Waiting for browser to detect deleted service"
    while not deleteFlag.isSet():
        time.sleep(1)

    print "* Stopping browser"
    b.Stop()
