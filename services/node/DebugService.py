#-----------------------------------------------------------------------------
# Name:        DebugService.py
# Purpose:     Generic debug service as an example of how to build and use
#              node services.
# Created:     2003/31/03
# RCS-ID:      
# Copyright:   (c) 2003-2004
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import os

from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.GUID import GUID

from AccessGrid.hosting import SecureServer as Server
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

class DebugService:
   """
   Simple service that prints out configuration information. It claims to be
   a video and audio producer and consumer just to get information.
   """
   def __init__(self):
      self.id = str(GUID())

      # a fictional debug level
      self.level = 0

   def SetLevel(self, level):
      self.level = level

   def GetLevel(self):
      return self.level

   def Start(self):
      pass

   def Stop(self):
      pass

   def ConfigureStream(self, streamDescription):
      if self.level > 0:
         print streamDescription

   def SetResource(self, resource):
      pass

   def SetIdentity(self, profile):
      if self.level > 0:
         print profile
         
class DebugServiceI(SOAPInterface):
   """
   Interface wrapper for the Debug Service implementation, so you can for
   example turn the verbosity up and down, or perhaps in the future redirect
   logging to someplace interesting.
   """
   def __init__(self, impl):
      SOAPInterface.__init__(self, impl)

   def _authorize(self, *args, **kw):
      return 1

   def GetLevel(self):
      return self.impl.GetLevel()

   def SetLevel(self, level):
      return self.impl.SetLevel(level)
      
   def Start(self):
      return self.impl.Start()

   def Stop(self):
      return self.impl.Stop()

   def ConfigureStream(self, streamDescription):
      # This needs to unmarshal the data
      # lucky we aren't using this yet
      return self.impl.ConfigureStream(streamDescription)
   
   def SetResource(self, resource):
      # This needs to unmarshal the data
      # lucky we aren't using this yet
      return self.impl.SetResource(resource)

   def SetIdentity(self, profile):
      # This needs to unmarshal the data
      # lucky we aren't using this yet
      return self.impl.SetIdentity(profile)

class DebugServiceIW(SOAPIWrapper):
   def __init__(self, url):
      SOAPIWrapper.__init__(self, url)

   def GetLevel(self):
      return self.proxy.GetLevel()

   def SetLevel(self, level):
      return self.proxy.SetLevel(level)
   
   def Start(self):
      return self.proxy.Start()

   def Stop(self):
      return self.proxy.Stop()

   def ConfigureStream(self, streamDescription):
      return self.proxy.ConfigureStream(streamDescription)
   
   def SetResource(self, resource):
      return self.proxy.SetResource(resource)

   def SetIdentity(self, profile):
      return self.proxy.SetIdentity(profile)

if __name__ == '__main__':
   from AccessGrid.Toolkit import CmdlineApplication
   import pprint

   # Do env init
   app = CmdlineApplication()
   app.Initialize("DebugServiceTest")
   
   # Create a local hosting environment
   hn = app.GetHostname()
   
   if len(sys.argv) == 2:
      testPort = int(sys.argv[1])
   else:
      testPort = 1300

   server = Server((hn, testPort))

   # Create the display service
   debugService = DebugService()

   # Then it's interface
   debugServiceI = DebugServiceI(debugService)

   # Then register the display service with the hosting environment
   service = server.RegisterObject(debugServiceI, path = "/DebugService")

   # Get the url and print it
   url = server.FindURLForObject(debugService)
   print "Starting server at", url

   # run the hosting environment until interrupted
   server.RunInThread()

   # Create a client
   debugClient = DebugServiceIW(url)

   testLevel = 5

   print "Original Level: ", debugClient.GetLevel()
   print "Set Level to %d" % testLevel
   debugClient.SetLevel(testLevel)
   print "New Level: ", debugClient.GetLevel()

   if debugClient.GetLevel() != testLevel:
      print "Error, levels don't match."
      
   # Shutdown the service
   server.Stop()
