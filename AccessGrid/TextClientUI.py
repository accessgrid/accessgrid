#-----------------------------------------------------------------------------
# Name:        PyText.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: TextClientUI.py,v 1.9 2003-02-28 16:54:36 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import pickle
import string

from wxPython.wx import *
from threading import Thread

from pyGlobus.io import GSITCPSocket
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth
from AccessGrid.Events import ConnectEvent, TextEvent

class SimpleTextProcessor:
    def __init__(self, socket, venueId, textOut):
        """ """
        self.socket = socket
        self.venueId = venueId
        self.textOut = textOut
        self.wfile = self.socket.makefile('wb', 0)
        self.rfile = self.socket.makefile('rb', -1)

        self.outputThread = Thread(target = self.ProcessNetwork)
        self.outputThread.start()

        self.localEcho = 0

    def LocalEcho(self):
        self.localEcho =~ self.localEcho
        
    def Stop(self):
        self.running = 0
        self.outputThread = 0
        
    def Input(self, event):
        """ """
        if self.localEcho:
            self._RawOutput(event.data.data + '\n')
            
        try:
            pdata = pickle.dumps(event)
            lenStr = "%s\n" % len(pdata)
            self.wfile.write(lenStr)
            self.wfile.write(pdata)
        except:
            (name, args, tb) = formatExceptionInfo()
            print "Error trying to send data"
            print "Name: %s Args: %s" % (name, args)
            print "TB:\n", tb

    def Output(self, text):
        """ """
        data = text.data

#        print "TS: %s GDI: %s" % (text.sender, GetDefaultIdentityDN())
        if text.sender == GetDefaultIdentityDN():
            string = "You say, \"%s\"\n" % (data)
        elif text.sender != None:
            name = text.sender
            stuff = name.split('/')
            for s in stuff[1:]:
                (k,v) = s.split('=')
                if k == 'CN':
                    name = v
            string = "%s says, \"%s\"\n" % (name, data)
        else:
            string = "Someone says, \"%s\"\n" % (data)

        self._RawOutput(string)

    def _RawOutput(self, string):
        try:
            wxCallAfter(self.textOut.AppendText, string)
        except:
            self.Stop()
        
    def ProcessNetwork(self):
        """ """
        self.running = 1
        while self.running:
            str = self.rfile.readline()
            size = int(str)
            pdata = self.rfile.read(size, size)
            event = pickle.loads(pdata)
            self.Output(event.data)

class TextClientUIStandAlone(wxFrame):
    aboutText = """PyText 1.0 -- a simple text client in wxPython and pyGlobus.
    This has been developed as part of the Access Grid project."""
    bufferSize = 128
    venueId = None
    location = None
    localEchoId = wxNewId()
    fileCloseId = wxNewId()
    helpAboutId = wxNewId()
        
    def __init__(self, *args, **kwds):
        wxFrame.__init__(self, *args, **kwds)
        # Menu Bar
        self.TextFrame_menubar = wxMenuBar()
        self.SetMenuBar(self.TextFrame_menubar)
        self.File = wxMenu()
        self.File.Append(self.fileCloseId, "Close", "Quit the application.")
        self.TextFrame_menubar.Append(self.File, "File")
        self.Options = wxMenu()
        self.Options.Append(self.localEchoId, "Local Echo",
                           "Echo input locally?", wxITEM_CHECK)
        self.TextFrame_menubar.Append(self.Options, "Options")
        self.Help = wxMenu()
        self.Help.Append(self.helpAboutId, "About",
                        "Open the about dialog box.")
        self.TextFrame_menubar.Append(self.Help, "Help")
        # Menu Bar end

        self.textClient = TextClientUI(self, -1)

        EVT_MENU(self, self.fileCloseId, self.FileClose)
        EVT_MENU(self, self.helpAboutId, self.HelpAbout)
        EVT_MENU(self, self.localEchoId, self.SetLocalEcho)

        self.Show()

    def SetLocation(self, location, id):
        self.textClient.SetLocation(location, id)

    def SetLocalEcho(self, event):
        self.textClient.Processor.LocalEcho()
        
    def FileClose(self, event):
        self.textClient.Stop()
        self.Close()

    def HelpAbout(self, event):
        """ About dialog!"""
        dlg = wxMessageDialog(self, self.aboutText, 'About Box...', wxOK)
        dlg.ShowModal()
        dlg.Destroy()


class TextClientUI(wxPanel):
    aboutText = """PyText 1.0 -- a simple text client in wxPython and pyGlobus.
        This has been developed as part of the Access Grid project."""
    bufferSize = 128
    venueId = None
    location = None
    Processor = None
    
    def __init__(self, *args, **kwds):
        wxPanel.__init__(self, *args, **kwds)
        self.TextOutput = wxTextCtrl(self, wxNewId(), "", style=wxTE_MULTILINE|wxTE_READONLY|wxHSCROLL)
        self.TextOutput.SetToolTipString("Text chat for this venue")
        self.textInputId = wxNewId()
        self.TextInput = wxTextCtrl(self, self.textInputId, "", style=wxTE_PROCESS_ENTER|wxHSCROLL)
        self.TextInput.SetToolTipString("Write your message here")

        self.__set_properties()
        self.__do_layout()

        EVT_TEXT_ENTER(self, self.textInputId, self.LocalInput)

        self.Show(true)

    def SetLocation(self, location, venueId):
        if self.Processor != None:
            self.Processor.Stop()
                  
        self.host = location[0]
        self.port = location[1]
        self.venueId = venueId
        self.attr = CreateTCPAttrAlwaysAuth()
        self.socket = GSITCPSocket()
        self.socket.connect(self.host, self.port, self.attr)

        self.Processor = SimpleTextProcessor(self.socket, self.venueId,
                                             self.TextOutput)
        
        self.Processor.Input(ConnectEvent(self.venueId))
        self.TextOutput.Clear()
        self.TextInput.Clear() 

    def __set_properties(self):
        self.SetSize((375, 225))
        
    def __do_layout(self):
        TextSizer = wxBoxSizer(wxVERTICAL)
        TextSizer.Add(self.TextOutput, 2, wxEXPAND|wxALIGN_CENTER_HORIZONTAL, 0)
        TextSizer.Add(self.TextInput, 0, wxEXPAND|wxALIGN_BOTTOM, 0)
        self.SetAutoLayout(1)
        self.SetSizer(TextSizer)
        self.Layout()
        
    def LocalInput(self, event):
        """ User input """
        if(self.venueId != None):
            textEvent = TextEvent(self.venueId, None, 0, event.GetString())
            self.Processor.Input(textEvent)
            self.TextInput.Clear()
        else:
            text = "Please, go to a venue before using the chat"
            dlg = wxMessageDialog(self, text , 'Not connected to venue', wxOK | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def Stop(self):
        self.Processor.Stop()
        
    def OnCloseWindow(self):
        self.Destroy()
        
if __name__ == "__main__":
    pyText = wxPySimpleApp()
    wxInitAllImageHandlers()
    TextFrame = TextClientUI(None, -1, "", host = sys.argv[1],
                                           port = int(sys.argv[2]))
    pyText.SetTopWindow(TextFrame)
    TextFrame.Show(1)
    pyText.MainLoop()
