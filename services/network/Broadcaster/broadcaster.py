#-----------------------------------------------------------------------------
# Name:        broadcaster.py
# Purpose:     
# Created:     2005/05/01
# RCS-ID:      $Id: broadcaster.py,v 1.3 2005-01-27 21:24:09 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
This program delivers .sdp files via http. It also starts up multicast
to unicast bridges to deliver the content that's described by the sdp
file.
"""
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.NetworkLocation import MulticastNetworkLocation

from wxPython.wx import *
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.Venue import VenueIW 
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator

from optparse import Option
import signal

import os
import sys
import socket
import shutil
import threading
import time

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from bridge import RTPReceiver

global bridge


class Broadcaster:
    """
    After retreiving media streams from a venue, the broadcaster
    down-samples, transcodes, and mixes the audio into ulaw-8kHz format
    recognized by other media players. It also lets you select one video
    stream to forward. 
    """

    def __init__(self, name, app):
        self.flag = 1

        self.app = app
        self.processManager = ProcessManager()

        # Initiate multicast address allocator.
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.multicastAddressAllocator.SetAllocationMethod(
            MulticastAddressAllocator.RANDOM)
        self.multicastAddressAllocator.SetBaseAddress(MulticastAddressAllocator.SDR_BASE_ADDRESS)
        self.multicastAddressAllocator.SetAddressMask(MulticastAddressAllocator.SDR_MASK_SIZE)

        # Set host and port options
        self.toVideoHost = self.multicastAddressAllocator.AllocateAddress()
        self.toVideoPort = 8000
        self.toAudioHost = self.multicastAddressAllocator.AllocateAddress()
        self.toAudioPort = 6000
        self.middleAudioHost = self.toAudioHost
        self.middleAudioPort = int(self.toAudioPort) + 2
        
        # Register signal handling for clean shutdown of service.
        signal.signal(signal.SIGINT, self.StopSignalLoop)
        signal.signal(signal.SIGTERM, self.StopSignalLoop)

        self.StartProcesses()
                         
    def StartSignalLoop(self):
        '''
        Start loop that can get interrupted from signals and
        shut down service properly.
        '''
        
        self.flag = 1
        while self.flag:
            try:
                time.sleep(0.5)
            except IOError:
                self.flag = 0
                self.log.debug("Broadcaster.StartSignalLoop: Signal loop interrupted, exiting.")

    def StopSignalLoop(self, signum, frame):
        '''
        Signal callback that shuts down the service cleanly. 
        '''
        self.flag = 0
        self.StopProcesses()
    
    def StopProcesses(self):
        '''
        Shutdown all processes.
        '''
        self.processManager.TerminateAllProcesses()
        
    def StartProcesses(self):
        '''
        Start rat for audio mixing and selector for video selection.
        '''              
        fromVideoHost = 0
        fromVideoPort = 0
        fromAudioHost = 0
        fromAudioPort = 0
               
        # Create venue proxy 
        venueUrl = self.app.options.venueUrl
        vProxy = venueProxy = VenueIW(venueUrl) 

        # Get stream information from venue
        producerStreams = filter(lambda s: s.capability.role == "producer", vProxy.GetStreams())

        for stream in producerStreams:
            if stream.capability.type == "video":
                fromVideoHost = stream.location.host
                fromVideoPort = stream.location.port 
            if stream.capability.type == "audio":
                fromAudioHost = stream.location.host
                fromAudioPort = stream.location.port  


        if fromVideoHost == 0 or fromVideoPort == 0:
            print "Video stream is not received from venue, you will not receive video"

        if fromAudioHost == 0 or fromAudioPort == 0:
            print "Audio stream is not received from venue, you will not receive audio"

        # We may receive odd ports from the venue (bug), so make
        # sure rtp only uses even ports .
        if fromVideoPort % 2 == 1:
            fromVideoPort = fromVideoPort -1

        if fromAudioPort % 2 == 1:
            fromAudioPort = fromAudioPort -1
        
        # Create commands to execute

        # Start audio down-sampler (linear16 kHz -> linear8 kHz)
        downSampExec = sys.executable
        dOptions = []
        dOptions.append("l16_to_l8_transcoder.py")
        dOptions.append("%s"%(fromAudioHost))
        dOptions.append("%d"%(fromAudioPort))
        dOptions.append("%s"%(self.middleAudioHost))
        dOptions.append("%d"%(self.middleAudioPort))

        print "********* START down-sampler", downSampExec, dOptions, '\n'
        self.processManager.StartProcess(downSampExec, dOptions)


        print "****************** BEFORE RAT", self.toAudioPort
        
        # Start audio transcoder (rat linear -> ulaw)
        ratExec = os.path.join(os.getcwd(), 'rat')
        roptions = []
        roptions.append("-T")
        roptions.append("%s/%d/127"%(self.middleAudioHost, self.middleAudioPort))
        roptions.append("%s/%d/127/pcm"%(self.toAudioHost, int(self.toAudioPort)))
              
        print "********* START transcoder ", ratExec, roptions, '\n'
        self.processManager.StartProcess(ratExec, roptions)

        selectorExec = os.path.join(os.getcwd(), 'Selector')
        soptions = []
        soptions.append("%s"%fromVideoHost)
        soptions.append("%d"%fromVideoPort)
        soptions.append("%s"%self.toVideoHost)
        soptions.append("%d"%int(self.toVideoPort))

        # Start video selector
        print "********* START selector with options = ", soptions, '\n'
        self.processManager.StartProcess(selectorExec, soptions)

        print "----------------------------------------"
        print "*** Video from %s/%d is forwarded to %s/%d"%(fromVideoHost, fromVideoPort,
                                                            self.toVideoHost, self.toVideoPort)
        print "*** Audio from %s/%d is forwarded to %s/%d"%(fromAudioHost, fromAudioPort,
                                                            self.toAudioHost, self.toAudioPort)
        print "----------------------------------------"

        # Start the bridge
        
        #global bridge
        #bridge = Bridge("224.2.159.7", 57712,
        #                    "224.2.166.28", 64270, 9999)
        #
        #print "audio", "224.2.159.57712/57712"
        #print "video", "224.2.166.28/64270"
        #
        #bridge.start()
        # 
        # try:
        #     while bridge.is_active():
        #         time.sleep(2)
        # except KeyboardInterrupt, k:
        #     print "Keyboard interrupt, quitting..."
        #     bridge.stop()


class BridgeRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bridge
        # The address of the other end of the client is self.client_address
        # which is a tuple (address, port)
        fname = self.path[1:]

        print "this is f name", fname
        
        if os.path.exists(fname):
            try:
                f = open(fname)
                lines = f.readlines()
                my_ip = bridge.get_host()
                aport = bridge.get_aport()
                vport = bridge.get_vport()
                
                bridge.add_client(self.client_address[0])
                
                self.send_response(200)
                self.send_header("Content-type", "application/sdp")
                self.send_header("Content-Length", str(os.fstat(f.fileno())[6]))
                self.send_header("Connection", "close")
                self.end_headers()
                
                print "MYIPADDR", my_ip
                print "MYAUDIOPORT", aport
                print "MYVIDEOPORT", vport
                
                for line in lines:
                    line = line.replace("MYIPADDR", str(my_ip))
                    line = line.replace("MYAUDIOPORT", str(aport))
                    line = line.replace("MYVIDEOPORT", str(vport))
                    print line[:-1]
                                        
                    self.wfile.write(line[:])
                    #    print "after write"

                print "after for"

            except:
                self.send_error(500, "stupid error")
        else:
            self.send_error(404, "File %s not found" % fname)

    def log_message(self, format, *args):
        pass

class Bridge:
    def __init__(self, audio_addr, a_port, video_addr, v_port, http_port):
        self.audio_addr = audio_addr
        self.a_port = a_port
        self.video_addr = video_addr
        self.v_port = v_port
        self.http_port = http_port

        self.http = HTTPServer(('', http_port), BridgeRequestHandler)
        self.http_thread = threading.Thread(target=self.http.serve_forever,
                                            name="HTTP Thread")

        self.host = socket.gethostbyname(socket.gethostname())

        print "this is http host and port", self.host, "/", http_port
        
        self.abridge = RTPReceiver(self.host, a_port)
        self.abridge.add_client(self.audio_addr, self.a_port, 1)
        
        self.vbridge = RTPReceiver(self.host, v_port)
        self.vbridge.add_client(self.video_addr, self.v_port, 1)

    def start(self):
        self.http_thread.start()
        self.abridge.start()
        self.vbridge.start()
        
    def stop(self):
        self.abridge.stop()
        self.vbridge.stop()
        self.http_thread.stop()

    def get_host(self):
        return self.host

    def get_aport(self):
        return self.a_port

    def get_vport(self):
        return self.v_port

    def add_client(self, addr):
        self.abridge.add_client(addr, int(self.a_port), 1)
        self.vbridge.add_client(addr, int(self.v_port), 1)
        
    def is_active(self):
        if self.vbridge.is_active() or self.abridge.is_active():
            return 1
        else:
            return 0

if __name__ == "__main__":
    # Start broadcaster

    if len(sys.argv) < 2:
        print "\nUsage: Broadcaster.py  --venueUrl <venueUrl>"
        sys.exit(1)

    # We need the simple wx app for when the
    # app.HaveValidProxy() call opens a
    # passphrase dialog.
    wxapp = wxPySimpleApp()
    
    # Initialize AG environment
    app = WXGUIApplication() 


    app.AddCmdLineOption(Option("-v", "--venueUrl",
                                dest="venueUrl",
                                help="Connect to venue located at this url."))
        
    try:
        app.Initialize("Broadcaster")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)
  
    if not app.certificateManager.HaveValidProxy():
        sys.exit(-1)

    # Create the network service.
    bcaster = Broadcaster('Broadcaster', app)
    
    # Start signal loop to make it possible to exit cleanly
    bcaster.StartSignalLoop()
    
    # Stop broadcaster
    bcaster.StopProcesses()
    
            

