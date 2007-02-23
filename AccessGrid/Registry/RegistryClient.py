#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Name:        RegistryClient.py
# Purpose:     This is the client side of the (bridge) Registry
# Created:     2006/01/01
# RCS-ID:      $Id: RegistryClient.py,v 1.30 2007-02-23 21:47:36 turam Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import xmlrpclib
import urllib
import os
import sys
import time
import httplib
import socket

from AccessGrid import Log
from AccessGrid.Platform import IsWindows, IsOSX, IsLinux, IsFreeBSD
from AccessGrid.Descriptions import BridgeDescription
from AccessGrid.BridgeCache import BridgeCache
from AccessGrid.Preferences import Preferences

class TimeoutHTTPConnection(httplib.HTTPConnection):
    def __init__(self, host, port=None, strict=None, timeout=0):
        httplib.HTTPConnection.__init__(self,host,port,strict)
        self.timeout = timeout
    def connect(self):
        """Connect to the host and port specified in __init__."""
        msg = "getaddrinfo returns an empty list"
        for res in socket.getaddrinfo(self.host, self.port, 0,
                                      socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                if self.timeout:
                    self.sock.settimeout(self.timeout)
                if self.debuglevel > 0:
                    print "connect: (%s, %s)" % (self.host, self.port)
                self.sock.connect(sa)
            except socket.error, msg:
                if self.debuglevel > 0:
                    print 'connect fail:', (self.host, self.port)
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
            
class TimeoutHTTP(httplib.HTTP):
    def __init__(self, host='', port=None, strict=None, timeout=0):
    
        # some joker passed 0 explicitly, meaning default port
        if port == 0:
            port = None

        # Note that we may pass an empty string as the host; this will throw
        # an error when we attempt to connect. Presumably, the client code
        # will call connect before then, with a proper host.
        self._setup(TimeoutHTTPConnection(host, port, strict, timeout=timeout))

class TimeoutTransport(xmlrpclib.Transport):
    def __init__(self,timeout):
        self.timeout = timeout
    def make_connection(self, host):
        host, extra_headers, x509 = self.get_host_info(host)
        httpconn = TimeoutHTTP(host,timeout=self.timeout)
        return httpconn
    

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
                tmpServerProxy = xmlrpclib.ServerProxy("http://"+r,
                                    transport=TimeoutTransport(5))
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
                #print "RoundTrip:", time.time(), startTime
                roundTripTime = time.time() - startTime
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
            
    def PingBridge(self,desc):
        pingVal = self.PingBridgeService(
                        xmlrpclib.ServerProxy("http://%s:%s" % (desc.host, desc.port),
                            transport=TimeoutTransport(1)) )
        if pingVal >= 0.0:
            desc.rank = pingVal
        else:
            desc.rank = BridgeDescription.UNREACHABLE

    def PingHost(self, host):
        try:
            pingVal = self._ping(host)
            return pingVal
        except:
            return -1
                    
    def LookupBridge(self):
        '''
        Query registry for a list of bridges.

        @return: command output
        @rtype: string
        '''
        self._connectToRegistry()
        bridges = self.serverProxy.LookupBridge()
                   
        # Create real bridge descriptions
        self.bridges = []
        for b in bridges:
            if 'portMin' not in b.keys():
                b['portMin'] = 0
                b['portMax'] = 0
            desc = BridgeDescription(b["guid"], b["name"], b["host"],
                                     b["port"], b["serverType"],
                                     b["description"],
                                     b["portMin"],
                                     b["portMax"])
            self.bridges.append(desc)
            
        return self.bridges
                                   
    def _readPeerList(self,url):
        if url.startswith("file://"):
            filename = url[7:]
            f = open(filename, "r")
        else:
            preferences = Preferences()
            proxyHost = preferences.GetPreference(Preferences.PROXY_HOST)
            proxyPort = preferences.GetPreference(Preferences.PROXY_PORT)
            proxyURL = None
            if proxyHost:
                if proxyPort:
                    proxyURL = "http://%s:%s" % (proxyHost, proxyPort)
                else:
                    proxyURL = "http://%s" % (proxyHost)
            if proxyURL:
                proxyList = {'http': proxyURL}
                f = urllib.urlopen(url, proxies=proxyList)
            else:
                f = urllib.urlopen(url)
        contents = f.read()
        f.close()
        registryPeers = contents.split()
        # Simplistic validation - just want a single peer.
        # For now, we assume any more than that to be an error
        # from (e.g.) some sort of error message (or page)
        # - Removed by AGDR as breaks AGSC bridge registry!
        #if len(registryPeers) > 1:
        #    registryPeers = []
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

    import sys
    rankBridges = 0
    if len(sys.argv) > 1:
        rankBridges = int(sys.argv[1])

    # Lookup bridges using the RegistryClient
    bridgeDescList = rc.LookupBridge(rankBridges=rankBridges)
    
    bridgeDescList.sort(lambda x,y: cmp(x.rank,y.rank))
    for b in bridgeDescList:
        print 'name: '+b.name+'  host: '+b.host+"  port: "+str(b.port) +"  dist:"+str(b.rank)
