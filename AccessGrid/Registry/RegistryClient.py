#!/usr/bin/env python

import xmlrpclib
import urllib
import os
import sys

from AccessGrid import Log
from AccessGrid.Platform import IsWindows, IsOSX, IsLinux
from AccessGrid.Descriptions import BridgeDescription
from AccessGrid.BridgeCache import BridgeCache

class RegistryClient:
    def __init__(self, url):
        self.url = url
        self.serverProxy = None
        self.registryPeers = None
        self.bridges = None
        self.bridgeCache = BridgeCache()
        self.log = Log.GetLogger('RegistryClient')
       
    def _connectToRegistry(self):
        if not self.registryPeers:
            self.registryPeers = self._readPeerList(url=self.url)
         
        # Connect to the first reachable register according to ping
        foundServer = 0

        for r in self.registryPeers:
            host = r.split(':')[0]
            if self.PingHost(host) > -1:
                try:
                    url = "http://"+r 
                    self.serverProxy = xmlrpclib.ServerProxy("http://"+r)
                    foundServer = 1
                    break
                except Exception,e:
                    self.log.exception("Failed to connect to registry %s"%(r))
            
        if not foundServer:
            # Throw exception!
            self.log.info("No bridge registry peers reachable")
   
    def RegisterBridge(self, registeredServerInfo):
        self._connectToRegistry()
        return self.serverProxy.RegisterBridge(registeredServerInfo)

    def PingHost(self, host):
        try:
            pingVal = self._ping(host)
            return pingVal
        except:
            return -1
                    
    def LookupBridge(self, maxToReturn=10):
        '''
        Query registry for a list of bridges. If user cache exists it
        is used instead of a network query.

        @keyword maxToReturn: number of bridges to return, default 10
        @type maxToReturn: int
        @return: command output
        @rtype: string
        '''
        if self.bridges:
            # We have bridges, return
            return self.bridges[0:maxToReturn]
        #else:
        #    # Get bridges from cache on local file
        #    self.bridges = self.bridgeCache.GetBridges()
                    
        if not self.bridges:
            # If the cache does not exist, query registry
            self._connectToRegistry()
            bridges = self.serverProxy.LookupBridge()
            self.bridges = []
                       
            # Create real bridge descriptions
            for b in bridges:
                desc = BridgeDescription(b["guid"], b["name"], b["host"],
                                         b["port"], b["serverType"],
                                         b["description"])
                self.bridges.append(desc)

            # Sort the bridges
            self._sortBridges(maxToReturn)
                        
            # Store bridges in cache
            self.bridgeCache.StoreBridges(self.bridges)
                       
        return self.bridges
            
    def _sortBridges(self, maxToReturn):
        '''
        Sort a list of bridges based on ping values. Bridges
        that can not be reached will be ignored.

        @param maxToReturn number of bridges to return
        @type maxToReturn int
        @return: list of sorted bridges
        @rtype: [AccessGrid.Descriptions.BridgeDescription]
        '''
        bridgeDescriptions = []
                         
        for desc in self.bridges[0:maxToReturn]:
            try:
                pingVal = self._ping(desc.host)
                desc.rank = pingVal
                bridgeDescriptions.append(desc)
            except Exception,e:
                self.log.exception("Failed to ping bridge %s"%(desc.name))
                                   
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
                cmd = 'ping -o -t 1 %s'%(host)
            else:
                cmd = 'ping -c 1 -w 1 %s'%(host)

            ret = self._execCmd(cmd)
            
            if ret.find('unknown host')>-1:
                self.log.info("Ping: Host %s not found"%(host))
                raise "Ping: Host %s not found"%(host)

            if ret.find('100%')>-1:
                self.log.info("Ping: Host %s timed out"%(host))
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
                self.log.info("Ping: Host %s not found"%(host))
                raise "Ping: Host %s not found"%(host)

            # windows times out automatically
            if ret.find('timed out')>-1:
                self.log.info("Ping: Host %s timed out"%(host))
                raise "Ping: Host %s timed out"%(host)
            
            # Find average round trip time
            a = ret.find('Average')
            ret = ret[a:]
            val = ret.split('=')[1]
            val = filter(lambda x: x.isdigit(), val)

        return val
       
    def _execCmd(self, cmd):
        '''
        Execute a command using popen, returns the output string.
        
        @param cmd: command to execute
        @type cmd: string
        @return: command output
        @rtype: string
        '''
        ret = ''
        try:
            f = os.popen(cmd, 'r')
            ret = f.read()
        finally:
            f.close()
        return ret


if __name__=="__main__":
    rc = RegistryClient(url="http://www.accessgrid.org/registry/peers.txt")
    from AccessGrid.GUID import GUID
    from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE

    # Register a bridge using the RegistryClient
    info = BridgeDescription(guid=GUID(), name="defaultName", host="localhost", port="9999", serverType=QUICKBRIDGE_TYPE, description="")
    rc.RegisterBridge(info)
    
    # Lookup a bridge using the RegistryClient
    bridgeDescList = rc.LookupBridge()
    for b in bridgeDescList:
        print 'name: '+b.name+'host '+b.host+"port: "+b.port
        
