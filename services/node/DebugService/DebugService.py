#-----------------------------------------------------------------------------
# Name:        DebugService.py
# Purpose:     Generic debug service as an example of how to build and use
#              node services.
# Created:     2003/31/03
# RCS-ID:      
# Copyright:   (c) 2003-2004
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys

from AccessGrid.GUID import GUID
from AccessGrid.AGService import AGService, RunService
from AccessGrid.interfaces.AGService_client import AGService as AGServiceI
from AccessGrid.Types import Capability
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter
from AccessGrid.AGParameter import RangeParameter, TextParameter

class DebugService(AGService):
   """
   Simple service that prints configuration information. It claims to be
   a video and audio producer and consumer just to get information.
   """
   
   def __init__(self):
      AGService.__init__(self)
      self.log.debug("DebugService.__init__: Init Service")
      self.id = str(GUID())

      # Set capabilities
      self.capabilities = [ Capability( Capability.CONSUMER, Capability.AUDIO ),
                            Capability( Capability.CONSUMER, Capability.VIDEO ),
                            Capability( Capability.PRODUCER, "debug" ) ]
      # Set executable
      self.executable = None
      
      # Set configuration parameters
      self.param1 = OptionSetParameter( "Configuration Parameter 1: ", "On", ["On", "Off"] )
      self.param2 = RangeParameter( "Configuration Parameter 2: ", 0, 0, 100 )
      self.param3 = TextParameter( "Configuration Parameter 3: ", "DebugService" )
      self.param4 = ValueParameter( "Configuration Parameter 4: ", 25 )

      # Append parameters to the configuration list
      self.configuration.append(self.param1)
      self.configuration.append(self.param2)
      self.configuration.append(self.param3)
      self.configuration.append(self.param4)

   # -------------------------------------------------------------------
   # Overidden methods inherited from AGService
   # -------------------------------------------------------------------
            
   def Start(self):
      self.log.debug("DebugService.Start")
      
   def Stop(self):
      self.log.debug("DebugService.Stop")
            
   def ConfigureStream(self, streamDescription):
      self.log.debug("DebugService.ConfigureStream %s "%streamDescription)
      if self.param1.value == "On":
         self.log.info("DebugService.ConfigureStream: value parameter is on!")

   def SetIdentity(self, profile):
      self.log.debug("DebugService.Set Identity %s"%profile)
      if self.param1.value == "On":
         self.log.info("DebugService.SetIdentity: value parameter is on!")


if __name__ == '__main__':
   
   # The port argument should always be set to sys.argv[1]
   port = int(sys.argv[1])
                
   # Create the display service
   debugService = DebugService()

   # Create the SOAP interface for the service
   debugServiceI = AGServiceI(debugService)
  
   # Start the service
   RunService(debugService, debugServiceI, port)

