#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.8 2003-04-28 18:26:55 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
try:
    import _winreg
    from AccessGrid.Platform import Win32RegisterMimeType
except:
    pass

from wxPython.wx import wxTheMimeTypesManager as mtm
from wxPython.wx import wxFileTypeInfo

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

def InitMimeTypes(file):
    """
    This function is used to load in our AG specific mimetypes.
    """
    success = 0

    # This only works for augmenting the mailcap entries on Linux
    if os.path.isfile(file):
        success = mtm.ReadMailcap(file, 1)
    else:
        return 0
    
    # For windows we have cope with the fact that it's the registry
    # that's dealt with during the "creating new associations" sequence
    # for now we load the mailcap file and stuff things in the registry
    if sys.platform == 'win32':
        fp = open(file)
        caps = mailcap.readmailcapfile(fp)
        fp.close()

        ftl = []
        for k in caps.keys():
            opencmd = u""
            printcmd = u""
            desc = u""
            ext = None
            cmds = []
            stuff = caps[k][0]
            for k2 in stuff.keys():
                if k2 == 'view':
                    cmds.append(('open', stuff[k2].replace('%s', '%1'), ''))
                elif k2 == 'description':
                    desc = stuff[k2]
                elif k2 == 'nametemplate':
                    ext = "." + stuff[k2].split('.')[1]
                elif k2 == 'print':
                    cmds.append((k2, stuff[k2].replace('%s', '%1'), ''))

            fileType = k.split('/')[1]
            fileType.replace('-', '.')
            Win32RegisterMimeType(k, ext, fileType, desc, cmds)
                    
    return success
    
