#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        SetupVideo.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: SetupVideo.py,v 1.9 2004-03-12 05:23:12 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the script that searches for video devices and gets them ready for
the node to use.
"""

__revision__ = "$Id: SetupVideo.py,v 1.9 2004-03-12 05:23:12 judson Exp $"
__docformat__ = "restructuredtext en"

import os
from AccessGrid.Platform.Config import AGTkConfig

tclScript = """set id [ open "videoresources" "w" ]
if { [ info exists inputDeviceList] == 1 } { 
   foreach d $inputDeviceList {
       set nick [$d nickname]
       if { $nick == "still" } {
       continue
       }
       set attr [$d attributes]
       if { $attr == "disabled" } {
       continue
       }

       set portnames [attribute_class $attr port]
       puts $id "device: $nick"
       puts $id "portnames: $portnames"
   }
}
close $id
adios
"""

agtkConf = AGTkConfig.instance()

# modify path to include install dir so vic is found
installDir = agtkConf.GetInstallDir()
os.environ["PATH"] = installDir + os.pathsep + os.environ["PATH"]

# change directory to config dir so videoresources file gets written there
os.chdir( agtkConf.GetConfigDir() )

# write tcl script
tclScriptFile = "tclScript"
tfptr = open( tclScriptFile, "w" )
tfptr.write(tclScript)
tfptr.close()

# run vic to generate video device file
os.system('vic -u %s 224.2.2.2/2000' % (tclScriptFile) )

# remove the script file
os.unlink(tclScriptFile)

