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
        self.registryPeers = self._readPeerList(url=self.url)
        self.sortedRegistryPeers = self._getSortedRegistryPeers()
        self.serverProxy = xmlrpclib.ServerProxy("http://" + self.sortedRegistryPeers[0])
   
    def RegisterBridge(self, registeredServerInfo):
        return self.serverProxy.RegisterBridge(registeredServerInfo)
       
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
        # TODO, retry with other nodes on failure?

        bridges = self.serverProxy.LookupBridge(maxToReturn)
        bridgeDescriptions = []

        # Create real bridge descriptions
        for b in bridges:
            desc = BridgeDescription(b["guid"], b["name"], b["host"],
                                     b["port"], b["serverType"],
                                     b["description"])
            bridgeDescriptions.append(desc)
            
        if sort:
            bridgeDescriptions = self._getSortedBridges(bridgeDescriptions)
        
        return bridgeDescriptions

    def _getSortedBridges(self, bridges):
        '''
        Sort a list of bridges based on ping values.

        @param bridges: list of bridges
        @type bridges: [AccessGrid.Descriptions.BridgeDescription]
        @return: list of sorted bridges
        @rtype: [AccessGrid.Descriptions.BridgeDescription]
        '''
        bridgeDescriptions = []
        pingValsDict = {}
                      
        for desc in bridges:
            try:
                pingVal = self._ping(desc.host)
                pingValsDict[desc] = pingVal
                
            except:
                #
                # log exception
                #
                pass

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
        return selection

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
            i = ret.find('=')
            ret = ret[i]
            ret = ret.split('=')[1]
            ret = ret.split('/')[1]
        
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
    rc = RegistryClient(url="file://../../tests/localhost_registry_nodes.txt")
    from AccessGrid.GUID import GUID
    from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE

    # Register a bridge using the RegistryClient
    info = BridgeDescription(guid=GUID(), name="defaultName", host="localhost", port="9999", serverType=QUICKBRIDGE_TYPE, description="")
    rc.RegisterBridge(info)
    
     # Lookup a bridge using the RegistryClient
    print "Found:", rc.LookupBridge()    # or rc.Lookup(10)
