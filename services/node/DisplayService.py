#-----------------------------------------------------------------------------
# Name:        DisplayService.py
# Purpose:     Generic display service for use on Win32/X11 displays
# Created:     2003/31/03
# RCS-ID:      
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import socket
import os

from wxPython.wx import wxGetDisplaySize;

from AccessGrid.hosting.Server import Server
from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter
from AccessGrid.AGParameter import RangeParameter

from AccessGrid.Platform import isWindows, isLinux, isOSX
from AccessGrid.NetUtilities import GetHostname

class DisplayService( AGService ):
   name = "display"
   locationStr = "Location"
   widthStr = "Width"
   heightStr = "Height"
   depthStr = "Depth"
   sizeStr = "Size"
   
   def __init__( self ):
      AGService.__init__( self )

      tmpCapability=Capability(Capability.CONSUMER, self.name)
      tmpCapability.parms[self.locationStr]=self.getLocation()
      tmpCapability.parms[self.sizeStr]=self.getSize()
      self.capabilities = [ tmpCapability ]
      self.executable = None

      # Set configuration parameters

   def getLocation( self ):
      hn = GetHostname()
      if isWindows()
         return "Win32://" + hn
      elif isLinux():
         if os.getenv("DISPLAY"):
            return "X11://" + hn + ":" + os.getenv("DISPLAY").split(":")[-1]
         else:
            return "X11://" + hn + ":0.0"
      else:
         return "Unknown://hn"
      
   def getSize( self ):
      myDisplaySize=wxGetDisplaySize()
      return "%dx%d"%(myDisplaySize.GetWidth(),myDisplaySize.GetHeight())

   def Start( self ):
      """Start service"""
      #self.started = 1
      try:
         self.options=["Starting Display Service..."]
         self._start(options)
      except:
         print "Exception in AudioService.Start", sys.exc_type, sys.exc_value
         raise Exception("Failed to start service")
   Start.soap_export_as = "Start"

   def ConfigureStream( self, streamDescription ):
      """
      Configure the Service according to the StreamDescription, and
      stop and start app
      """
      AGService.ConfigureStream( self, streamDescription )

      # restart app, since this is the only way to change the 
      # stream location (for now!)
      if self.started:
         self.Stop()
         self.Start()
   ConfigureStream.soap_export_as = "ConfigureStream"

def AuthCallback(server, g_handle, remote_user, context):
   return 1

if __name__ == '__main__':
   from AccessGrid.hosting.pyGlobus import Client
   import thread

   agService = DisplayService()
   server = Server( int(sys.argv[1]), auth_callback=AuthCallback )
   service = server.create_service_object("Service")
   agService._bind_to_service( service )

   print "Starting server at", agService.get_handle()
   server.run()
