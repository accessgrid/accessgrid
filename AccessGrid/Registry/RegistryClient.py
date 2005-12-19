#!/usr/bin/env python

import xmlrpclib
import urllib
import os
import sys

from AccessGrid.Platform import IsWindows, IsOSX, IsLinux
from AccessGrid.Descriptions import BridgeDescription

class RegistryClient:
    def __init__(self, url):
        self.url = url
        self.serverProxy = None
        self.registryPeers = self._readPeerList(url=self.url)
        #self.sortedRegistryPeers = self._getSortedRegistryPeers()

        # Connect to the first reachable register according to ping
        for r in self.registryPeers:
            host = r.split(':')[0]
            if self.PingHost(host) > -1:
                self.serverProxy = xmlrpclib.ServerProxy("http://" + r[0])
        else:
            # Throw exception!
            print '============= no registry peers reachable'
   
    def RegisterBridge(self, registeredServerInfo):
        return self.serverProxy.RegisterBridge(registeredServerInfo)

    def PingHost(self, host):
        try:
            pingVal = self._ping(host)
            return pingVal
        except:
            return -1
                 
    def LookupBridge(self, maxToReturn=10, sort = False):
        '''
        Query registry for a list of bridges

        @keyword maxToReturn: number of bridges to return, default 10
        @type maxToReturn: int
        @keyword sort: if True, sort based on ping values.
        @type sort: boolean
        @return: command output
        @rtype: string
        '''

        bridges = []
        self.bridges = []
         
        if self.serverProxy:
            bridges = self.serverProxy.LookupBridge()
       
        # Create real bridge descriptions
        for b in bridges:
            desc = BridgeDescription(b["guid"], b["name"], b["host"],
                                     b["port"], b["serverType"],
                                     b["description"])
            self.bridges.append(desc)
                
        if sort:
            return self._getSortedBridges(maxToReturn)
        else:
            return self.bridges

    def _getSortedBridges(self, maxToReturn):
        '''
        Sort a list of bridges based on ping values. Bridges
        that can not be reached will be ignored.

        @param maxToReturn number of bridges to return
        @type maxToReturn int
        @return: list of sorted bridges
        @rtype: [AccessGrid.Descriptions.BridgeDescription]
        '''
        bridgeDescriptions = []
        pingValsDict = {}
                      
        for desc in self.bridges[0:maxToReturn]:
            try:
                pingVal = self._ping(desc.host)
                pingValsDict[desc] = pingVal
                #print desc.name, desc.host, pingVal
              
            except Exception,e:
                #
                # log exception
                #
                print 'exception:', e

        # Sort bridges based on ping values
        values = pingValsDict.values()          
        values.sort()
               
        for val in values:
            for key in pingValsDict.keys():
                if val == pingValsDict[key]:
                    bridgeDescriptions.append(key)
                    del pingValsDict[key]
                    
        return bridgeDescriptions

               
    def _getSortedRegistryPeers(self, maxToReturn=5):
        # TODO, ping (and cache) and sort registries.
        selection = self.registryPeers[:maxToReturn]
        print len(selection)
        sortedSelection = []
        pingValsDict = {}
        
        for registry in selection:
            #try:
            print registry
            pingVal = self._ping(registry.split(':')[0])
            pingValsDict[registry] = pingVal
                
            #except:
            #    # TODO, retry with other nodes on failure?
            #    print '=========== can not reach registry'
            #    #
            #    # log exception
            #    #
            #    pass

        # Sort registries based on ping values
        values = pingValsDict.values()          
        values.sort()
               
        for val in values:
            for key in pingValsDict.keys():
                if val == pingValsDict[key]:
                    sortedSelection.append(key)
                    del pingValsDict[key]

        print len(sortedSelection)
        return sortedSelection

    def _readPeerList(self,url):
        if url.startswith("file://"):
            filename = url[7:]
            f = open(filename, "r")
        else:
            opener = urllib.FancyURLopener({})
            f = opener.open(url)
        contents = f.read()
        f.close()
        registryPeers = contents.split()
        return registryPeers

    def _ping(self, host):
        '''
        Invoke system ping command to host

        @param host: machine to ping
        @type host: string
        @return: average time for ping command  
        @rtype: string
        '''
        
        if IsOSX() or IsLinux():
            # osx and linux ping command have the
            # same output format
            
            # time out after 10 sec
            if IsOSX():
                cmd = 'ping -o -t 10 %s'%(host)
            else:
                cmd = 'ping -c 1 -w 10 %s'%(host)

            ret = self._execCmd(cmd)
            
            if ret.find('unknown host')>-1:
                print "Ping: Host %s not found"%(host)
                raise "Ping: Host %s not found"%(host)

            if ret.find('100%')>-1:
                print "Ping: Host %s timed out"%(host)
                raise "Ping: Host %s timed out"%(host)
        
            # Find average round trip time
            i = ret.find('time')
            ret = ret[i:]
            ret = ret.split('=')[1]
            ret = ret.split()[0]
            val = float(ret)
        
        if IsWindows():
            cmd = 'ping -n 1 %s'%(host)
            ret = self._execCmd(cmd)
            
            if ret.find('could not find')>-1:
                print "Ping: Host %s not found"%(host)
                raise "Ping: Host %s not found"%(host)

            # windows times out automatically
            if ret.find('timed out')>-1:
                print "Ping: Host %s timed out"%(host)
                raise "Ping: Host %s timed out"%(host)
            
            # Find average round trip time
            a = ret.find('Average')
            ret = ret[a:]
            val = ret.split('=')[1]
            val = filter(lambda x: x.isdigit(), val)

        self.file.close()
        return val
       
    def _execCmd(self, cmd):
        '''
        Execute a command using popen, returns the output string.
        
        @param cmd: command to execute
        @type cmd: string
        @return: command output
        @rtype: string
        '''
        self.file = os.popen(cmd, 'r')
        ret = self.file.read()
        return ret


if __name__=="__main__":
    rc = RegistryClient(url="http://www.accessgrid.org/registry/peers.txt")
    from AccessGrid.GUID import GUID
    from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE

    # Register a bridge using the RegistryClient
    info = BridgeDescription(guid=GUID(), name="defaultName", host="localhost", port="9999", serverType=QUICKBRIDGE_TYPE, description="")
    rc.RegisterBridge(info)
    
    # Lookup a bridge using the RegistryClient
    bridgeDescList = rc.LookupBridge(sort=1)
    for b in bridgeDescList:
        print b.name, b.host, b.port, b.description
        
