#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/23/01
# RCS-ID:      $Id: Utilities.py,v 1.4 2003-01-23 14:28:42 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os
import string
import sys
import traceback

def formatExceptionInfo(maxTBlevel=5):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb)

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
