#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.5 2003-02-10 22:12:45 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from wxPython.wx import *
from wxPython.lib.imagebrowser import *
from AccessGrid import icons

from AccessGrid.Utilities import formatExceptionInfo

class ErrorDialog:
    def __init__(self, frame, text):
        (name, args, traceback_string_list) = formatExceptionInfo()
##        for x in traceback_string_list:
##            print(x)       
        errorDialog = wxMessageDialog(frame, text, '', wxOK)
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
