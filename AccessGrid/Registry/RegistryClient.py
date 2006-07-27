#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Name:        RegistryClient.py
# Purpose:     This is the client side of the (bridge) Registry
# Created:     2006/01/01
# RCS-ID:      $Id: RegistryClient.py,v 1.24 2006-07-27 14:40:20 turam Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import xmlrpclib
import urllib
import os
import sys
import time

from AccessGrid import Log
from AccessGrid.Platform import IsWindows, IsOSX, IsLinux, IsFreeBSD
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
            try:
                tmpServerProxy = xmlrpclib.ServerProxy("http://"+r)
                if self.PingRegistryPeer(tmpServerProxy) > -1:
                    self.serverProxy = tmpServerProxy
                    foundServer = 1
                    break
            except Exception,e:
                self.log.exception("Failed to connect to registry %s"%(r))
            
        if not foundServer:
            # Throw exception!
            self.log.info("No bridge registry peers reachable")
            #raise Exception("No bridge registry peers reachable")
   
    def RegisterBridge(self, registeredServerInfo):
        self._connectToRegistry()
        return self.serverProxy.RegisterBridge(registeredServerInfo)

    def PingRegistryPeer(self, serverProxy):
        startTime = serverProxy.Ping(time.time())
        roundTripTime = time.time() - startTime
        #print "RoundTrip:", roundTripTime
        return roundTripTime

    def PingBridgeService(self, bridgeProxy):
        try:
            try: # Temporary try/except until all Bridges have the "Ping" method
                startTime = bridgeProxy.Ping(time.time())
                roundTripTime = time.time() - startTime
                #print "RoundTrip:", roundTripTime
                return roundTripTime
            except xmlrpclib.Fault, e:  # Temporary until all Bridges have the "Ping" method
                if 'method "Ping" is not supported' in e.faultString:
                    self.log.info('Using deprecated ping for older bridge interface to %s',
                                  bridgeProxy._ServerProxy__host)
                    host = bridgeProxy._ServerProxy__host.split(":")[0]
                    return self.PingHost(host)
                else:
                    raise
        except:
            self.log.exception('Exception pinging bridge')
            return -1

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
                if 'portMin' not in b.keys():
                    b['portMin'] = 5000
                    b['portMax'] = 5100
                desc = BridgeDescription(b["guid"], b["name"], b["host"],
                                         b["port"], b["serverType"],
                                         b["description"],
                                         b["portMin"],
                                         b["portMax"])
                self.bridges.append(desc)

            # Sort the bridges
            self.bridges = self._sortBridges(maxToReturn)
                        
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
                pingVal = self.PingBridgeService(xmlrpclib.ServerProxy("http://%s:%s" % (desc.host, desc.port)))
                if pingVal > 0:
                    desc.rank = pingVal
                else:
                    desc.rank = 100000
                bridgeDescriptions.append(desc)
            except:
                self.log.exception("Failed to ping bridge %s (%s:%s)"%(desc.name,desc.host,str(desc.port)))
                
        return bridgeDescriptions
                                   
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
        
        if IsOSX() or IsLinux() or IsFreeBSD():
            # osx and linux ping command have the
            # same output format
            
            # time out after 10 sec
            if IsOSX() or IsFreeBSD():
                cmd = 'ping -o -t 1 %s'%(host)
            else:
                cmd = 'ping -c 1 -w 1 %s'%(host)

            ret = self._execCmd(cmd)
            
            if ret.find('unknown host')>-1:
                self.log.info("Ping: Host %s not found"%(host))
                raise Exception, "Ping: Host %s not found"%(host)

            if ret.find('100%')>-1:
                self.log.info("Ping: Host %s timed out"%(host))
                raise Exception, "Ping: Host %s timed out"%(host)
        
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
                raise Exception, "Ping: Host %s not found"%(host)

            # windows times out automatically
            if ret.find('timed out')>-1:
                self.log.info("Ping: Host %s timed out"%(host))
                raise Exception, "Ping: Host %s timed out"%(host)
            
            # Find average round trip time
            a = ret.find('Average')
            ret = ret[a:]
            val = ret.split('=')[1]
            val = filter(lambda x: x.isdigit(), val)
            val = float(val)

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

    # Disable bridge registration so we can just test the registry client
    # Register a bridge using the RegistryClient
    #info = BridgeDescription(guid=GUID(), name="defaultName", host="localhost", port="9999", serverType=QUICKBRIDGE_TYPE, description="")
    #rc.RegisterBridge(info)
    
    # Lookup a bridge using the RegistryClient
    bridgeDescList = rc.LookupBridge()
    for b in bridgeDescList:
        print 'name: '+b.name+'  host: '+b.host+"  port: "+str(b.port) +"  dist:"+str(b.rank)
        
