#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.7 2003-03-11 22:12:10 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from wxPython.wx import *
from wxPython.lib.imagebrowser import *
from AccessGrid import icons

from AccessGrid.Utilities import formatExceptionInfo

class MessageDialog:
    def __init__(self, frame, text, text2 = "", style = wxOK|wxICON_INFORMATION):
        errorDialog = wxMessageDialog(frame, text, text2, style)
        errorDialog.ShowModal()
        errorDialog.Destroy()

class MyLog(wxPyLog):
    ERROR = 1
    WARNING = 2
    MESSAGE = 3
    INFO = 5
    DEBUG = 6
            
    def __init__(self, log):
        wxPyLog.__init__(self)
        self.log = log
              
    def DoLog(self, level, message, timeStamp):
        if level  == self.ERROR:
            self.log.exception(message)

        elif level  == self.MESSAGE:
            self.log.info(message)
            
        elif level  == self.DEBUG:
            self.log.debug(message)

        elif level  == self.INFO:
            self.log.info(message)

        elif level  == self.WARNING:
            self.log.info(message)

class ErrorDialog:
    def __init__(self, frame, text, text2 = "", style = wxOK | wxICON_ERROR):
       (name, args, traceback_string_list) = formatExceptionInfo()
       for x in traceback_string_list:
           print(x)       

       print sys.exc_type
       print sys.exc_value
       info = text + "\n\n"+"Type: "+str(sys.exc_type)+"\n"+"Value: "+str(sys.exc_value)
       errorDialog = wxMessageDialog(frame, info, text2, style)
       errorDialog.ShowModal()
       errorDialog.Destroy()
        
class BugReportDialog:
    def __init__(self, frame, profile):
        reportDialog = wxMessageDialog(frame, 'BUG REPORT', '', wxOK)
        reportDialog.ShowModal()
        reportDialog.Destroy()

class AboutDialog(wxPopupTransientWindow):
    def __init__(self, parent, style):
        wxPopupTransientWindow.__init__(self, parent, style)
        self.panel = wxPanel(self, -1)

        bmp = icons.getAboutBitmap()

        panelWidth = bmp.GetWidth() + 4
        panelHeight = bmp.GetHeight() + 4
        panelSize = wxSize(panelWidth, panelHeight )
        winWidth = parent.GetSize().GetWidth()
        winHeight = parent.GetSize().GetHeight()
        winPos = parent.GetPosition()
        diffWidth = (winWidth - panelWidth)/2.0
        diffHeight = (winHeight - panelHeight)/2.0
             
        self.text = wxStaticBitmap(self.panel, -1, bmp, wxPoint(2, 2), \
                            wxSize(bmp.GetWidth(), bmp.GetHeight()))
        self.panel.SetBackgroundColour("WHITE")
        self.panel.SetSize(panelSize)
        self.panel.SetPosition(wxPoint(1, 1))
        self.SetBackgroundColour('BLACK')
        self.SetSize(wxSize(panelWidth + 2, panelHeight + 2))
        self.SetPosition(winPos + wxPoint(diffWidth, diffHeight))
        
    def ProcessLeftDown(self, evt):
        self.Hide()
        return false
