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
        if frame.Connected():
            frame.Update()
        frame.Show(true)
        self.SetTopWindow(frame)
        return true

wxInitAllImageHandlers()

app = MyApp(0)

app.MainLoop()
