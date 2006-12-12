from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid import Log
log = None

class BridgeFactory:
    """
    The BridgeFactory class is used to create and manage Bridges.
    If multiple bridges are requested for a multicast group, they
    use the same, single bridge.  When the reference count on a
    Bridge goes to zero, the Bridge is actually stopped and 
    deleted
    """

    class Bridge:
        """
        The Bridge class encapsulates execution of the bridge software
        """
        def __init__(self, qbexec,id, maddr, mport, mttl, uaddr, uport, processManager, deathCallback=None):
            self.qbexec = qbexec
            self.id = id
            self.maddr = maddr
            self.mport = mport
            self.mttl = mttl
            self.uaddr = uaddr
            self.uport = uport
            self.processManager = processManager
            self.deathCallback = deathCallback
            self.pid = 0

        def Start(self):
            """
            Start the Bridge (actually execute the bridge process)
            """
            log.info("Method Bridge.Start called")

            # Log detail about bridge being started
            log.info("Starting bridge:")
            log.info("  [maddr,mport,mttl] = %s %d %d", 
                           self.maddr, self.mport, self.mttl)
            log.info("  [uaddr,uport] = %s %s", self.uaddr, 
                           str(self.uport))

            # Start the process
            args = [
                    "-g", self.maddr,
                    "-m", '%d' % (self.mport,),
                    "-u", '%s' % (str(self.uport),),
                    "-i", '10', # temporarily hard-coded inactivity timeout
                   ]
            log.info("Starting bridge: %s %s", self.qbexec, str(args))
            self.pid = self.processManager.StartProcess(self.qbexec,args)
            return self.pid

        def Stop(self):
            """
            Stop stops the bridge, terminating bridge processes
            """
            log.info("Method Bridge.Stop called")
            self.processManager.TerminateAllProcesses()
            
        def IsRunning(self):
            return self.processManager.IsRunning(self.pid)

    def __init__(self, qbexec, portRange=None, logger=Log.GetLogger("BridgeFactory")):
        self.qbexec = qbexec
        self.portRange = portRange
        global log
        log = logger

        self.bridges = dict()
        self.processManager = ProcessManager()
        self.processManager.WaitForChildren(self.OnBridgeDeath)
        
        self.bridgesByPid = {}

        self.addressAllocator = NetworkAddressAllocator()
        
        # Use the port range if given
        if portRange:
            log.info("Allocator using port range: %s" % (portRange,))
            self.SetPortMin(portRange[0])
            self.SetPortMax(portRange[1])

    def SetBridgeExecutable(self,qbexec):
        self.qbexec = qbexec
        
    def SetPortMin(self,portMin):
        log.info("BridgeFactory.SetPortMin %d", portMin)
        self.addressAllocator.SetPortBase(portMin)
        
    def SetPortMax(self,portMax):
        log.info("BridgeFactory.SetPortMax %d", portMax)
        self.addressAllocator.SetPortMax(portMax)
        
    def GetPortMin(self):
        return self.addressAllocator.GetPortBase()
        
    def GetPortMax(self):
        return self.addressAllocator.GetPortMax()

    def CreateBridge(self,id,maddr,mport,mttl,uaddr,uport):
        """
        This method returns an existing bridge for the given maddr/mport,
        or a new one
        """

        log.info("Method CreateBridge called")

        if not uport:
            # Allocate a port
            allocateEvenPort = 1
            uport = self.addressAllocator.AllocatePort(allocateEvenPort)
            log.info("Allocated port = %s", str(uport))

        retBridge = None

        # - Check for an existing bridge with the given multicast addr/port
        for bridge,refcount in self.bridges.values():
            if bridge.maddr == maddr and bridge.mport == mport:
                if bridge.IsRunning() == 1:
                    log.info("- using existing bridge")
                    retBridge = bridge
                    refcount += 1
                    key = "%s%d" % (maddr,mport)
                    self.bridges[key] = (retBridge,refcount)
                    break
                else:
                    self.OnBridgeDeath(self.processManager, self.bridges[key].pid)

        # - If bridge does not exist; create one
        if not retBridge:
            # Instantiate a new bridge
            log.info("- creating new bridge")
            retBridge = BridgeFactory.Bridge(self.qbexec,id,maddr,mport,
                                             mttl,uaddr,uport,
                                             self.processManager,
                                             self.OnBridgeDeath)
            pid = retBridge.Start()
   
            # Add the bridge to the list of bridges
            key = "%s%s" % (retBridge.maddr,retBridge.mport)
            self.bridges[key] = (retBridge,1)
            
            self.bridgesByPid[pid] = retBridge

        return retBridge


    def DestroyBridge(self,bridge):
        """
        DestroyBridge deletes the specified bridge from the list of bridges
        """

        log.info("Method DestroyBridge called")

        key = "%s%d" % (bridge.maddr,bridge.mport)
        if self.bridges.has_key(key):
            bridge,refcount = self.bridges[key]
            refcount -= 1
            self.bridges[key] = (bridge,refcount)

            # if the refcount is 0,
            # stop and delete the bridge
            if refcount == 0:
                log.info("- Refcount zero; stopping and deleting bridge")
                bridge.Stop()
                try:
                    self.addressAllocator.RecyclePort(bridge.uport)
                except ValueError:
                    log.warn('Port has already been recycled')
                try:
                    del self.bridges[key]
                except KeyError:
                    log.warn('Bridge has already been stopped')
                
    def OnBridgeDeath(self,pm,pid):
        bridge = None
        if pid in self.bridgesByPid.keys():
            bridge = self.bridgesByPid[pid]
            
        if not bridge:
            log.warn("Bridge for pid %d not found" % (pid,))
            return
            
        log.info("Removing bridge following death of bridge process (%s/%d)",
                bridge.maddr, bridge.mport)
        key = "%s%d" % (bridge.maddr,bridge.mport)
        if self.bridges.has_key(key):
            log.info("Removing bridge following death of bridge process (%s/%d)",
                    bridge.maddr, bridge.mport)
            try:
                self.addressAllocator.RecyclePort(bridge.uport)
            except ValueError:
                log.warn('Port has already been recycled')
            try:
                del self.bridges[key]
            except KeyError:
                log.warn('Bridge has already been stopped')

        else:
            log.warn("Attempt to handle death of bridge which is not known to BridgeFactory (%s/%d)" % (bridge.maddr,bridge.mport))

        try:    
            del self.bridgesByPid[pid]
        except KeyError:
            log.warn("Attempt to handle death of bridge which is not known to BridgeFactory")
        except:
            log.exception("Exception removing bridge from bridgelist")

    def GetBridges(self):
        # return only the bridge objects themselves, not the
        # (bridge,refcount) tuples
        return map( lambda x: x[0], self.bridges.values())

                
if __name__ == '__main__':
    
    
    import time
    
    bf = BridgeFactory('./QuickBridge')
    b = bf.CreateBridge(1,'224.2.2.4',20302,127,'140.221.34.85',50222)
    b.Start()
    
    
    while 1:
        time.sleep(1)
