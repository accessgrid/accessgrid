#-----------------------------------------------------------------------------
# Name:        TextService.py
# Purpose:     
#
# Author:      Thomas D. uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: TextService.py,v 1.2 2003-02-06 14:44:55 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.AGService import *
from AccessGrid.AGParameter import *


class TextService( AGService ):

   def __init__( self ):
      print self.__class__, ".init"
      AGService.__init__( self )

      self.capabilities = [ Capability( Capability.CONSUMER, Capability.TEXT ) ]
#CHECKME - can java path be fully specified?  clearly not, since must be cross-platform
      self.executable = "f:/windows/system32/java"

      #
      # Set configuration parameters
      #
      self.configuration["IGChat Jar path"] = ValueParameter( "IGChat Jar path", "igchat.jar" ) 

   def Start( self, connInfo ):
      __doc__ = """Start service"""
      try:

         # 
         # Start the service; in this case, store command line args in a list and let
         # the superclass _Start the service
         print "Start service"
         print "Location : ", self.location.host, self.location.port, self.location.ttl
         options = []
         options.append( "-jar" )
         options.append( self.configuration["IGChat Jar path"].value )
#FIXME - chat app needs username
         name = connInfo.get_remote_name()
         index = name.find("CN=")
         username = name[index+3:]
         username = username.replace(" ","_")

         options.append( username )
         options.append( "-group" )
         options.append( self.location.host )
         options.append( "-port" )
         options.append( '%d' % ( self.location.port ) )
         options.append( "-ttl" )
         options.append( '%d' % ( self.location.ttl ) )
         self._Start( options )
         print "pid = ", self.childPid
      except:
         print "Exception ", sys.exc_type, sys.exc_value
   Start.soap_export_as = "Start"
   Start.pass_connection_info = 1


   def ConfigureStream( self, connInfo, streamDescription ):
      """Configure the Service according to the StreamDescription, and stop and start app"""
      print "in AudioService.ConfigureStream"
      AGService.ConfigureStream( self, connInfo, streamDescription )

      # restart app, since this is the only way to change the 
      # stream location (for now!)
      if self.started:
         self.Stop( connInfo )
         self.Start( connInfo )
   ConfigureStream.soap_export_as = "ConfigureStream"
   ConfigureStream.pass_connection_info = 1


if __name__ == '__main__':

   agService = TextService()
   server = Server( 0 )
   service = server.create_service_object()
   agService._bind_to_service( service )

   thread.start_new_thread( Client.Handle( sys.argv[2] ).get_proxy().RegisterService, 
                            ( sys.argv[1], agService.get_handle() ) )

   print "Starting server at", agService.get_handle()
   server.run()
