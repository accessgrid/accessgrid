#-----------------------------------------------------------------------------
# Name:        NetworkAddressAllocator.py
# Purpose:     This class manages multicast address allocation.
# Created:     2002/12/12
# RCS-ID:      $Id: NetworkAddressAllocator.py,v 1.7 2005-10-05 20:05:12 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetworkAddressAllocator.py,v 1.7 2005-10-05 20:05:12 lefvert Exp $"
__docformat__ = "restructuredtext en"

import socket
from random import Random

class NoFreePortsError(Exception):
    pass

class NetworkAddressAllocator:
    """
    This class provides a clean API for allocating general network
    addresses. For typical unicast networks this devolves to picking
    port numbers. So that's all that's done here.
    """
    RANDOM = "random"
    INTERVAL = "interval"
    
    def __init__(self, portBase = 49152, portMax=65535):
        """
        We only need to initialize port information.
        """
        self.portBase = portBase
        self.portMax = portMax
        
        self.allocatedPorts = []
        self.random = Random()

        self.allocationMethod = NetworkAddressAllocator.RANDOM
        
    def SetAllocationMethod( self, method ):
        self.allocationMethod = method
        return self.allocationMethod
    
    def GetAllocationMethod( self ):
        return self.allocationMethod

    def SetPortBase(self, portBase):
        self.portBase = portBase

    def SetPortMax(self, portMax):
        self.portMax = portMax

    def AllocatePort(self, even = 0):
        """
        if the even flag is set we allocate only an even port to support
        RTP standard use cases.
        """
        
        port = self.AllocatePortInRange(even,self.portBase,self.portMax)
        return port
        
    def AllocatePortInRange(self, even, portBase, portMax):
        if even:
            evenPortBase = portBase + portBase % 2
            evenPortMax = portMax - portMax % 2
            diff = evenPortMax - evenPortBase
            numEvenPorts = diff / 2 + 1
            if len(self.allocatedPorts) >= numEvenPorts:
                raise NoFreePortsError
        else:
            numPorts = portMax - portBase + 1
            if len(self.allocatedPorts) >= numPorts:
                raise NoFreePortsError
        # Check to see if port is used
        if even:
            modulus = 2
        else:
            modulus = 1
        while 1:
            if even:
                port = self.random.randrange(evenPortBase, evenPortMax+1, modulus)
            else:
                port = self.random.randrange(portBase, portMax+1, modulus)
            
            if port in self.allocatedPorts:
                continue
            
            try:
                s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                s.bind(("", port ) )
                s.close()
                break
            except socket.error:
                continue
            
        self.allocatedPorts.append(port)
        return port
    
        
    def RecyclePort(self, port):
        self.allocatedPorts.remove(port)
        return port
    
if __name__ == "__main__":
    
    def NumEvenPorts(portBase,portMax):
        evenPortBase = portBase + portBase % 2
        evenPortMax = portMax - portMax % 2
        diff = evenPortMax - evenPortBase
        numPorts = diff / 2 + 1
        return numPorts

    def runTest(mn,mx,even=0, verbose=False):
        print "Testing [%d,%d],even=%d" %( mn, mx, even)
        if even:
            iter = NumEvenPorts(mn,mx)
        else:
            iter = mx - mn + 1
        print "\t%d ports: " % (iter )
        netAdd = NetworkAddressAllocator(mn,mx)
        ports = list()
        for i in range(0, iter ):
            port = netAdd.AllocatePort(even=even)
            if verbose:
                ports.append(port)
        if verbose:
            print "\t",ports
        try:
            port = netAdd.AllocatePort(even=even)
            if verbose:
                ports.append(port)
        except NoFreePortsError:
            print "\tCorrectly raised NoFreePortsError"
        else:
            raise Exception("\tDidn't raise \"NoFreePortsError\"")

    netAdd = NetworkAddressAllocator(1000, 8000)
    print 'even or odd', netAdd.AllocatePort(0)
    print 'even or odd', netAdd.AllocatePort(0)
    print 'even or odd', netAdd.AllocatePort(0)
    print 'even or odd', netAdd.AllocatePort(0)
    print 'even or odd', netAdd.AllocatePort(0)
    print 'even or odd', netAdd.AllocatePort(0)
    print 'even or odd', netAdd.AllocatePort(0)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)
    print 'even', netAdd.AllocatePort(1)

    
    #print
    #runTest(20001, 20011, even=0, verbose=True)
    #
    #runTest(20001, 20011, even=1, verbose=True)
    #runTest(20002, 20011, even=1, verbose=True)
    #runTest(20003, 20011, even=1, verbose=True)
    #runTest(20004, 20011, even=1, verbose=True)
    #
    #runTest(20001, 20012, even=1, verbose=True)
    #runTest(20001, 20013, even=1, verbose=True)
    #runTest(20001, 20014, even=1, verbose=True)
    #runTest(20001, 20015, even=1, verbose=True)

