#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        NodeManagement.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: NodeManagement.py,v 1.13 2003-02-28 18:00:33 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import copy
import time, thread
import pprint
import urlparse
from wxPython.wx import *

from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame

class MyApp(wxApp):
    def OnInit(self):
        frame = NodeManagementClientFrame(NULL, -1, "Access Grid Node Management")
        try:
            frame.AttachToNode( "https://localhost:11000/NodeService" )
            frame.Update()
        except:
            pass
        frame.Show(true)
        self.SetTopWindow(frame)
        return true

wxInitAllImageHandlers()

app = MyApp(0)

app.MainLoop()
