import os
import string
import sys


def Which( file ):
   paths = string.split( os.environ['PATH'], os.pathsep )
   if sys.platform == "win32" and string.find( file, ".exe" ) == -1:
      file = file + ".exe"
   for path in paths:
      testfile = os.path.join( path, file )
      if os.path.exists( testfile ):
         return testfile

   return None

from AccessGrid.Types import Capability, AGResource

def GetResourceList():
   """
   -- not yet implemented --
   Placeholder method for resource interrogation.  
   """

   print "GetResourceList() : not yet implemented"
   
   resources = []

   resources.append( AGResource( Capability.VIDEO, "/dev/video0" ) )
   resources.append( AGResource( Capability.VIDEO, "/dev/video1" ) )
   resources.append( AGResource( Capability.VIDEO, "/dev/video2" ) )
   resources.append( AGResource( Capability.VIDEO, "/dev/video3" ) )
   resources.append( AGResource( Capability.AUDIO, "/dev/audio" ) )

   return resources