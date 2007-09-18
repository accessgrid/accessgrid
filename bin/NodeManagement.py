#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        NodeManagement.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: NodeManagement.py,v 1.33 2007-09-18 20:45:22 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os
import sys

import wx

from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame
from AccessGrid.Toolkit import WXGUIApplication, MissingDependencyError
from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW
from AccessGrid.UIUtilities import MessageDialog

log = None
app = None

class MyApp(wx.App):
    global log
    global app

    defNSUrl = "http://localhost:11000/NodeService"

    def OnInit(self):
        frame = NodeManagementClientFrame(NULL, -1,
                                          "Access Grid Node Management")

        try:
            nodeService = AGNodeServiceIW(self.defNSUrl)
            frame.AttachToNode(nodeService)
            # Avoid UI errors if fail to attach to node.
            if frame.nodeServiceHandle.IsValid():
                frame.UpdateUI()
        except:
            if log is not None:
                log.exception("Error connecting to Node Service: %s",
                              self.defNSUrl)

        frame.Show(true)
        self.SetTopWindow(frame)

        return true
        

def main():
    global log
    global app
    
    wx.InitAllImageHandlers()

    app = WXGUIApplication()

    nodeMgmtApp = MyApp(0)
    try:
        app.Initialize("NodeManagement")
    except MissingDependencyError, e:
        if e.args[0] == 'SSL':
            msg = "The installed version of Python has no SSL support.  Check that you\n"\
                  "have installed Python from python.org, or ensure SSL support by\n"\
                  "some other means."
        else:
            msg = "The following dependency software is required, but not available:\n\t%s\n"\
                    "Please satisfy this dependency and restart the software"
            msg = msg % e.args[0]
        MessageDialog(None,msg, "Initialization Error",
                      style=wx.ICON_ERROR )
        sys.exit(-1)
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        MessageDialog(None,
                      "The following error occurred during initialization:\n\n\t%s %s" % (e.__class__.__name__,e), 
                      "Initialization Error",
                      style=wx.ICON_ERROR )
        sys.exit(-1)

    log = app.GetLog()
    
    nodeMgmtApp.MainLoop()

if __name__ == "__main__":
    main()
