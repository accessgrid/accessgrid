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

from AccessGrid.hosting import SecureServer as Server
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.GUID import GUID
from AccessGrid.AGService import AGService, AGServiceI, AGServiceIW, RunService
from AccessGrid.Types import Capability

class DebugService(AGService):
   """
   Simple service that prints out configuration information. It claims to be
   a video and audio producer and consumer just to get information.
   """
   def __init__(self):
      AGService.__init__(self)
      
      self.id = str(GUID())

      # a fictional debug level
      self.level = 0
      
      self.capabilities = [ Capability( Capability.CONSUMER, Capability.AUDIO ),
                            Capability( Capability.CONSUMER, Capability.VIDEO ),
                            Capability( Capability.PRODUCER, "debug" ) ]

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

   def SetIdentity(self, profile):
      if self.level > 0:
         print profile
         
class DebugServiceI(AGServiceI):
   """
   Interface wrapper for the Debug Service implementation, so you can for
   example turn the verbosity up and down, or perhaps in the future redirect
   logging to someplace interesting.
   """
   def __init__(self, impl):
      AGServiceI.__init__(self, impl)

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
   
   def SetIdentity(self, profile):
      # This needs to unmarshal the data
      # lucky we aren't using this yet
      return self.impl.SetIdentity(profile)

class DebugServiceIW(AGServiceIW):
   def __init__(self, url):
      AGServiceIW.__init__(self, url)

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
   
   def SetIdentity(self, profile):
      return self.proxy.SetIdentity(profile)

if __name__ == '__main__':
   if len(sys.argv) == 1:
      doTest = 1
      import pprint
      port = 1300
   else:
      port = int(sys.argv[1])
      
   # Create the display service
   debugService = DebugService()

   # Then it's interface
   debugServiceI = DebugServiceI(debugService)

   RunService(debugService, debugServiceI, port)

