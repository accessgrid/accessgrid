import os
import thread
import zipfile
import socket

import SimpleHTTPServer
import SocketServer

from AGParameter import *


class AGResource:
   def __init__( self, type=None, resource=None ):
      self.type = type
      self.resource = resource
      self.inUse = False

   def GetType( self ):          
      return self.type
   def SetType( self, type ):    
      self.type = type
   
   def GetResource( self ):      
      return self.type
   def SetResource( self, resource ): 
      self.resource = resource


class Capability:
   
   PRODUCER = "producer"
   CONSUMER = "consumer"

   AUDIO = "audio"
   VIDEO = "video"
   TEXT  = "text"

   def __init__( self, role=None, type=None ):
      self.role = role
      self.type = type
      self.parms = dict()

class AGServiceManagerDescription:
   def __init__( self, name=None, description=None, uri=None ):
      self.name = name
      self.description = description
      self.uri = uri

class AGServiceDescription:
   def __init__( self, name=None, description=None, uri=None, capabilities=None, 
                 resource=None, serviceManagerUri=None, executable=None ):
      self.name = name
      self.description = description
      self.uri = uri
      self.capabilities = capabilities
      self.resource = resource
      self.serviceManagerUri = serviceManagerUri
      self.executable = executable



# consider using this as the description of the service implementation
# at the NodeService, passing the url of the executable to the ServiceManager.
# Only the executable would reside on the ServiceManager
class AGServiceImplementation:
   def __init__( self, name=None, description=None, uri=None, 
                 capabilities=None, commandLineArgs=None ):
      self.name = name                 # user
      self.description = description   # user
      self.uri = uri                   # for system to retrieve executable
      self.capabilities = capabilities # user
      self.executable = None           # system, but can be determined from package content


   def GetServiceDescription( self, file ):

      import ConfigParser
      import string

      #
      # examine service package content
      #
      zf = zipfile.ZipFile( file, "r" )
      files = zf.namelist()
      descfile = None
      exefile = None
      for file in files:
         if file.endswith(".svc"):
            descfile = file
         else:
            exefile = file
            if exefile.endswith(".py"):
               self.isPython = True
      
      #
      # extract executable file from zip
      #
      exefilecontent = zf.read( exefile )
      if self.isPython:
         f = open( "local_services/"+exefile, "w" )
      else:
         f = open( "local_services/"+exefile, "wb" )
      f.write( exefilecontent )
      f.close()

      #
      # extract description file from zip
      #
      descfilecontent = zf.read( descfile )
      f = open( "local_services/"+descfile, "w" )
      f.write( descfilecontent )
      f.close()

      c = ConfigParser.ConfigParser()
      c.read( "local_services/"+descfile )
      
      # error checking

      #
      # read sections and massage into data structure
      #
      print "----- sections ", c.sections()

      capabilities = []
      capabilitySectionsString = c.get( "ServiceDescription", "capabilities" )
      capabilitySections = string.split( capabilitySectionsString, ' ' )
      for section in capabilitySections:
         cap = Capability( c.get( section, "role" ), c.get( section, "type" ) )
         capabilities.append( cap )
      serviceDescription = AGServiceDescription( c.get( "ServiceDescription", "name" ),
                                               c.get( "ServiceDescription", "description" ),
                                               None,
                                               capabilities,
                                               None,
                                               None,
                                               "local_services/" + c.get( "ServiceDescription", "executable" ) )
      return serviceDescription


def FindFreePort( startport ):
   port = startport
   while 1:
      try:
         s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
         s.bind(("", port ) )
         s.close()
      except socket.error:
         port = port + 1
         continue

      break
   return port


class AGServiceImplementationRepository:

   def __init__( self, port=FindFreePort(900) ):
      self.httpd_port = port
      self.__ReadServiceImplementations()
      thread.start_new_thread( self.__StartWebServer, () )

   def __ReadServiceImplementations( self ):
      self.serviceImplementations = []

# FIXME - location of services should be configurable by clients
      files = os.listdir("services")
      for file in files:
         """
         serviceImpl = AGServiceImplementation()
         serviceImpl.ReadServiceImplementationFile( "services/"+file )
         self.serviceImplementations.append( serviceImpl )
         """
         self.serviceImplementations.append( 'http://%s:%d/services/%s' % 
            ( socket.gethostname(), self.httpd_port, file ) )


   def GetServiceImplementations( self ):
      __doc__ = """Get list of local service implementations"""
      return self.serviceImplementations

   def __StartWebServer( self ):
      print "Starting web server on port ", self.httpd_port
      self.httpd = SocketServer.TCPServer(("",self.httpd_port), SimpleHTTPServer.SimpleHTTPRequestHandler )
      self.httpd.serve_forever()



class ServiceConfiguration:
   def __init__( self, resource, executable, parameters ):
      self.executable = executable
      self.resource = resource
      self.parameters = map( lambda parm: CreateParameter( parm ), parameters )

