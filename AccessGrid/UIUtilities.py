#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.18 2003-06-17 21:40:14 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import mailcap
import string

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

from AccessGrid.Utilities import SubmitBug
from AccessGrid.Utilities import formatExceptionInfo


class MessageDialog:
    def __init__(self, frame, text, text2 = "", style = wxOK|wxICON_INFORMATION):
        errorDialog = wxMessageDialog(frame, text, text2, style)
        errorDialog.ShowModal()
        errorDialog.Destroy()
      
class ErrorDialog:
    def __init__(self, frame, text, text2 = "", style =  wxICON_ERROR |wxYES_NO | wxNO_DEFAULT):
        info = text + "\n\nDo you wish to send an automated error report?"
        errorDialog = wxMessageDialog(frame, info, text2, wxICON_ERROR |wxYES_NO | wxNO_DEFAULT)
        
        if(errorDialog.ShowModal() == wxID_YES):
            # The user wants to send an error report
            bugReportCommentDialog = BugReportCommentDialog(frame)

            if(bugReportCommentDialog.ShowModal() == wxID_OK):
                # Submit the error report to Bugzilla
              
                SubmitBug(bugReportCommentDialog.GetComment())
                bugFeedbackDialog = wxMessageDialog(frame, "Your error report has been sent, thank you.",
                                                    "Error Reported", style = wxOK|wxICON_INFORMATION)
                bugFeedbackDialog.ShowModal()
                bugFeedbackDialog.Destroy()       

            bugReportCommentDialog.Destroy()
            errorDialog.Destroy()

class BugReportCommentDialog(wxDialog):
    def __init__(self, parent):
        wxDialog.__init__(self, parent, -1, "Comment for Bug Report", style =  wxOK)
        self.text = wxStaticText(self, -1, "Please, enter a description of the problem you are experiencing.", style=wxALIGN_LEFT)
        self.button = wxButton(self, wxID_OK, "Ok")
        self.commentBox = wxTextCtrl(self, -1, "", size = wxSize(300,100), style = wxTE_MULTILINE)
        self.line = wxStaticLine(self, -1)
        self.Centre()
        self.Layout()
        
    def GetComment(self):
        return self.commentBox.GetValue()

    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.text, 0, wxALL, 10)
        sizer.Add(self.commentBox, 0, wxALL | wxEXPAND, 10)
        sizer.Add(self.line, 0, wxALL | wxEXPAND, 10)
        sizer.Add(self.button, 0, wxALL | wxALIGN_CENTER, 10)
            
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
class ErrorDialogWithTraceback:
    def __init__(self, frame, text, text2 = "", style = wxOK | wxICON_ERROR):
        
       (name, args, traceback_string_list) = formatExceptionInfo()

       tbstr = ""
       for x in traceback_string_list:
           print(x)
           tbstr += x + "\n"

       print sys.exc_type
       print sys.exc_value
       info = text + "\n\n"+"Type: "+str(sys.exc_type)+"\n"+"Value: "+str(sys.exc_value) + "\nTraceback:\n" + tbstr
       errorDialog = wxMessageDialog(frame, info, text2, style)
       errorDialog.ShowModal()
       errorDialog.Destroy()
        
#class BugReportDialog:
#    def __init__(self, frame, profile):
#        reportDialog = wxMessageDialog(frame, 'BUG REPORT', '', wxOK)
#        reportDialog.ShowModal()
#        reportDialog.Destroy()

class AboutDialog(wxPopupTransientWindow):
    version = "Agtk 2.0"
        
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
             
        self.image = wxStaticBitmap(self.panel, -1, bmp, wxPoint(2, 2), \
                            wxSize(bmp.GetWidth(), bmp.GetHeight()))
        self.text = wxStaticText(self.panel, -1,
                                 "Version: %s \nCopyright@2001-2003 by University of Chicago, \nAll rights reserved\nPlease visit www.accessgrid.org for more information" %self.version, wxPoint(80,105))
        self.panel.SetBackgroundColour('WHITE')
        self.panel.SetSize(panelSize)
        self.panel.SetPosition(wxPoint(1, 1))
        self.SetBackgroundColour('BLACK')
        self.SetSize(wxSize(panelWidth + 2, panelHeight + 2))
        self.SetPosition(winPos + wxPoint(diffWidth, diffHeight))
               
    def ProcessLeftDown(self, evt):
        self.Hide()
        return false

class AppSplash(wxSplashScreen):
    def __init__(self):
        wxSplashScreen.__init__(self, bmp,
                                wxSPLASH_CENTRE_ON_SCREEN|wxSPLASH_TIMEOUT,
                                4000, None, -1,
                                style=wxSIMPLE_BORDER|wxFRAME_NO_TASKBAR
                                |wxSTAY_ON_TOP)
        EVT_CLOSE(self, self.OnClose)
        
    def OnClose(self, evt):
        
        evt.Skip()

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
    
def GetMimeCommands(filename = None, type = None, ext = None):
    """
    This function returns anything in the local mime type database for the
    type or extension specified.
    """
    cdict = dict()
    
    if type != None:
        fileType = mtm.GetFileTypeFromMimeType(type)
    elif ext != None:
        fileType = mtm.GetFileTypeFromExtension(ext)

    if fileType != None and filename != None:
        mimeType = fileType.GetMimeType()
        if mimeType != None:
            cmds = fileType.GetAllCommands(filename, mimeType)
            if None == cmds:
                verbs = []
                cmdlines = []
            else:
                verbs, cmdlines = cmds
            for i in range(0, len(verbs)):
                cdict[string.lower(verbs[i])] = cmdlines[i]
        else:
            cdict = None
    else:
        cdict = None

    return cdict

