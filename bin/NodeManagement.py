#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        NodeManagement.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: NodeManagement.py,v 1.21 2004-02-19 17:59:02 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
from AccessGrid.hosting.pyGlobus import Client
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

app = Toolkit.WXGUIApplication()
nodeMgmtApp = MyApp(0)
app.Initialize()
app.InitGlobusEnvironment()

nodeMgmtApp.MainLoop()
