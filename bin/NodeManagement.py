#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        NodeManagement.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: NodeManagement.py,v 1.18 2003-08-14 21:22:32 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os
import sys
from wxPython.wx import *

from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame
from AccessGrid import Toolkit

class MyApp(wxApp):
    def OnInit(self):
        frame = NodeManagementClientFrame(NULL, -1, "Access Grid Node Management")
        try:
            frame.AttachToNode( "https://localhost:11000/NodeService" )
            # Avoid UI errors if fail to attach to node.
            if frame.nodeServiceHandle().IsValid():
                frame.UpdateUI()
        except:
            pass
        frame.Show(true)
        self.SetTopWindow(frame)
        return true

wxInitAllImageHandlers()

Toolkit.WXGUIApplication().Initialize()

nodeMgmtApp = MyApp(0)
nodeMgmtApp.MainLoop()
