#-----------------------------------------------------------------------------
# Name:        Platform.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/09/02
# RCS-ID:      $Id: Platform.py,v 1.1 2003-02-10 21:02:34 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os

WinGPI = "wgpi.exe"
LinuxGPI = "grid-proxy-init"

def GPI():
    GlobusBin = os.path.join(os.environ['GLOBUS_LOCATION'], 'bin')
    files = os.listdir(GlobusBin)
    for f in files:
        print "File: %s" % f
        if f == WinGPI:
            print "WINDOWS: %s" % os.path.join(GlobusBin, f)
            os.spawnv(os.P_WAIT, os.path.join(GlobusBin, f), [])
        elif f == LinuxGPI:
            print "LINUX %s" % os.path.join(GlobusBin, f)