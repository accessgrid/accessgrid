#-----------------------------------------------------------------------------
# Name:        broadcaster.py
# Purpose:     
# Created:     2005/05/01
# RCS-ID:      $Id: broadcaster.py,v 1.7 2005-02-11 20:51:58 lefvert Exp $
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
from l16_to_l8_transcoder import L16_to_L8
from VideoSelector import VideoSelector
from SelectorGUI import SelectorGUI

bridge = None

debug = 0

class Broadcaster:
    """
    After retreiving media streams from a venue, the broadcaster
    down-samples, transcodes, and mixes the audio into ulaw-8kHz format
    recognized by other media players. It also lets you select one video
    stream to forward. 
    """

    def __init__(self, name, app, mixAudio):
        global bridge
        
        self.flag = 1
        self.app = app
        self.processManager = ProcessManager()
        self.log = app.GetLog()

        self.selectAudio = 1
        
        if mixAudio:
            self.selectAudio = 0
    
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
        self.transcoderHost = self.toAudioHost
        self.transcoderPort = int(self.toAudioPort) + 2
        
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
        print "Exiting..."
        self.flag = 0
        bridge.stop()
        self.tcoder.Stop()
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
        global bridge
        
        fromVideoHost = 0
        fromVideoPort = 0
        fromAudioHost = 0
        fromAudioPort = 0
               
        # Create venue proxy
        venueUrl = self.app.options.venueUrl
        if venueUrl:
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

        else:
            fromVideoHost = self.app.options.videoHost
            fromVideoPort = int(self.app.options.videoPort)
            fromAudioHost = self.app.options.audioHost
            fromAudioPort = int(self.app.options.audioPort)
            
        if debug:
            print "video multicast: ", fromVideoHost, fromVideoPort
            print "audio multicast: ", fromAudioHost, fromAudioPort

        if fromVideoHost == 0 or fromVideoPort == 0:
            if debug: print "Video stream is not received from venue, you will not receive video"

        if fromAudioHost == 0 or fromAudioPort == 0:
            if debug: print "Audio stream is not received from venue, you will not receive audio"

        # We may receive odd ports from the venue (bug), so make
        # sure rtp only uses even ports .
        if fromVideoPort % 2 == 1:
            fromVideoPort = fromVideoPort -1

        if fromAudioPort % 2 == 1:
            fromAudioPort = fromAudioPort -1
        
        # Create commands to execute

        # Start audio down-sampler (linear16 kHz -> linear8 kHz)

        if debug: print "****************** START DOWN-SAMPLER", fromAudioHost, "/", fromAudioPort, "  ",self.transcoderHost, "/", self.transcoderPort
        self.tcoder = L16_to_L8(fromAudioHost,fromAudioPort,
                                self.transcoderHost,self.transcoderPort, self.selectAudio)
        self.tcoder.Start()

        wxapp = wxPySimpleApp()

        if self.selectAudio:
            audioSelectorUI = SelectorGUI("Audio Selector", self.tcoder)
       
        if debug: print "****************** BEFORE RAT", self.toAudioPort
        
        # Start audio transcoder (rat linear -> ulaw)
        ratExec = os.path.join(os.getcwd(), 'rat')
        roptions = []
        roptions.append("-T")
        roptions.append("%s/%d/127/l16"%(self.transcoderHost, int(self.transcoderPort)))
        roptions.append("%s/%d/127/pcm"%(self.toAudioHost, int(self.toAudioPort)))
              
        if debug: print "********* START transcoder ", ratExec, roptions, '\n'
        self.processManager.StartProcess(ratExec, roptions)


        self.vselector = VideoSelector(fromVideoHost, int(fromVideoPort),
                                       self.toVideoHost, int(self.toVideoPort), 1)
        self.vselector.Start()

        videoSelectorUI = SelectorGUI("VideoSelector", self.vselector)
        
        # Start video selector
        if debug: print "****************** START VIDEO SELECTOR", fromVideoHost, "/", fromVideoPort, "  ",self.toVideoHost, "/", self.toVideoPort
        
        if debug: print "----------------------------------------"
        if debug: print "*** Video from %s/%d is forwarded to %s/%d"%(fromVideoHost, fromVideoPort,
                                                            self.toVideoHost, self.toVideoPort)
        if debug: print "*** Audio from %s/%d is forwarded to %s/%d"%(fromAudioHost, fromAudioPort,
                                                            self.toAudioHost, self.toAudioPort)
        if debug: print "----------------------------------------"

        # Start the bridge
        print "Server URL: http://%s:%d" % (socket.gethostbyname(socket.gethostname()),9999)
        bridge = Bridge(self.toAudioHost, int(self.toAudioPort),
                        self.toVideoHost, int(self.toVideoPort), 9999)
         
        bridge.start()

        wxapp.SetTopWindow(videoSelectorUI)
        if self.selectAudio:
            audioSelectorUI.Show()
        videoSelectorUI.Show()
        wxapp.MainLoop()
        
         

class BridgeRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        global bridge

        # The address of the other end of the client is self.client_address
        # which is a tuple (address, port)
        fname = self.path[1:]

        if debug: print "************* this is f name", fname
        
        if os.path.exists(fname):
            try:
                if debug: print "fname does exist....."

                          
                f = open(fname)
                if debug: print "after open ", fname
                lines = f.readlines()
                if debug: print 'after read lines'
                my_ip = bridge.get_host()
                aport = bridge.get_aport()
                vport = bridge.get_vport()

                if debug: print "add client", self.client_address[0], self.client_address[1]
                
                bridge.add_client(self.client_address[0])

                # Modify sdp data with address/port info
                # Note: this changes the length, so compute the length
                # of the modified sdp
                length = 0
                mlines = []
                for line in lines:
                    line = line.replace("MYIPADDR", str(my_ip))
                    line = line.replace("MYAUDIOPORT", str(aport))
                    line = line.replace("MYVIDEOPORT", str(vport))
                    length += len(line)
                    mlines.append(line)

                # Send the http header
                if debug: print "after add client"
                self.send_response(200)
                self.send_header("Content-type", "application/sdp")
                self.send_header("Content-Length", str(length))
                self.send_header("Connection", "close")
                self.end_headers()
                
                if debug: print "MYIPADDR", my_ip
                if debug: print "MYAUDIOPORT", aport
                if debug: print "MYVIDEOPORT", vport
                
                # Send the modified sdp data
                for line in mlines:
                    self.wfile.write(line[:])

                if debug: print "after for; wrote ", length

            except:
                log.exception("this is an exception")
                self.send_error(500, "stupid error")
        else:
            log.exception("this is an exception")
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

        print "bridge audio: %s/%d" % (audio_addr, a_port)
        print "bridge video: %s/%d" % (video_addr, v_port)

        self.http = HTTPServer(('', http_port), BridgeRequestHandler)
        self.http_thread = threading.Thread(target=self.http.serve_forever,
                                            name="HTTP Thread")
        self.http_thread.setDaemon(1)

        self.host = socket.gethostbyname(socket.gethostname())

        if debug: print "this is http host and port", self.host, "/", http_port

        CHECK_TIMEOUT = 15
                
        self.abridge = RTPReceiver(self.host, a_port, CHECK_TIMEOUT)
        self.vbridge = RTPReceiver(self.host, v_port, CHECK_TIMEOUT)
        
    def start(self):
        self.http_thread.start()
        self.abridge.start()
        self.vbridge.start()

        self.abridge.add_client(self.audio_addr, self.a_port, 1)
        self.vbridge.add_client(self.video_addr, self.v_port, 1)
        if debug: print "********************* end of start"
        
    def stop(self):
        self.abridge.stop()
        self.vbridge.stop()
        self.http.server_close()

    def get_host(self):
        if debug: print "get host", self.host
        return self.host

    def get_aport(self):
        if debug: print "get a port", self.a_port
        return self.a_port

    def get_vport(self):
        if debug: print "get v port", self.v_port
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

    # We need the simple wx app for when the
    # app.HaveValidProxy() call opens a
    # passphrase dialog.
    wxapp = wxPySimpleApp()
    
    # Initialize AG environment
    app = WXGUIApplication() 
    log = app.GetLog()


    app.AddCmdLineOption(Option("-v", "--venueUrl",
                                dest="venueUrl",
                                help="Connect to venue located at this url."))
    app.AddCmdLineOption(Option("--videoHost",
                                dest="videoHost",
                                help="Host address for video source"))
    app.AddCmdLineOption(Option("--videoPort",
                                dest="videoPort",
                                help="Port for video source"))
    app.AddCmdLineOption(Option("--audioHost",
                                dest="audioHost",
                                help="Host address for audio source"))
    app.AddCmdLineOption(Option("--audioPort",
                                dest="audioPort",
                                help="Port for audio source"))
    app.AddCmdLineOption(Option("--mixAudio",
                                dest = "mixAudio", action = "store_true", default = 0,
                                help ="Try mixing all audio sources (High failure rate)"))
    
    if debug: print "initializing"
    try:
        app.Initialize("Broadcaster")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    if not  app.options.venueUrl:
        if  (app.options.videoHost and
             app.options.videoPort and
             app.options.audioHost and
             app.options.audioPort):
            pass
        else:
            print "\nUsage: Broadcaster.py  --venueUrl <venueUrl>"
            sys.exit(1)

    debug = app.options.debug
    
    if not app.certificateManager.HaveValidProxy():
        sys.exit(-1)


    print app.options.mixAudio
    mix = 0
    if app.options.mixAudio:
        mix = 1

    # Create the network service.
    bcaster = Broadcaster('Broadcaster', app, mix)
    
    # Start signal loop to make it possible to exit cleanly
    bcaster.StartSignalLoop()
    
    # Stop broadcaster
    bcaster.StopProcesses()
    
    
            

