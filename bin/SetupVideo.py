#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SetupVideo.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: SetupVideo.py,v 1.4 2003-02-13 15:31:22 leggett Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os

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

# modify path to include current dir
os.environ["PATH"] = "." + os.pathsep + os.environ["PATH"]

# write tcl script
tclScriptFile="tclScript"
f = open( tclScriptFile, "w" )
f.write(tclScript)
f.close()

# run vic to generate video device file
os.system('vic -u %s 224.2.2.2/2000' % (tclScriptFile) )

# remove the script file
os.unlink(tclScriptFile)

