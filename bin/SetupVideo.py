#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SetupVideo.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: SetupVideo.py,v 1.5 2003-03-14 16:31:42 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os
from AccessGrid import Platform

tclScript = """set id [ open "videoresources" "w" ]
if { [ info exists inputDeviceList] == 1 } { 
   foreach d $inputDeviceList {
       set nick [$d nickname]
       if { $nick == "still"  || $nick == "x11" } {
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

# modify path to include install dir so vic is found
installDir = Platform.GetInstallDir()
os.environ["PATH"] = installDir + os.pathsep + os.environ["PATH"]

# change directory to config dir so videoresources file gets written there
os.chdir( Platform.GetSystemConfigDir() )

# write tcl script
tclScriptFile="tclScript"
f = open( tclScriptFile, "w" )
f.write(tclScript)
f.close()

# run vic to generate video device file
os.system('vic -u %s 224.2.2.2/2000' % (tclScriptFile) )

# remove the script file
os.unlink(tclScriptFile)

