#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.22 2003-08-13 20:59:57 lefvert Exp $
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
from wxPython.lib.throbber import Throbber
from wxPython.wx import *
from wxPython.lib.imagebrowser import *
from AccessGrid import icons

from AccessGrid.Utilities import SubmitBug
from AccessGrid.Utilities import formatExceptionInfo


class MessageDialog:
    def __init__(self, frame, text, text2 = "", style = wxOK|wxICON_INFORMATION):
        messageDialog = wxMessageDialog(frame, text, text2, style)
        messageDialog.ShowModal()
        messageDialog.Destroy()
      
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
        wxDialog.__init__(self, parent, -1, "Comment for Bug Report")
        self.text = wxStaticText(self, -1, "Please, enter a description of the problem you are experiencing.", style=wxALIGN_LEFT)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
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

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 5)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER | wxBOTTOM, 5) 
            
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
        

class ProgressDialog(wxProgressDialog):
    count = 1

    def __init__(self, title, message, maximum):
        wxProgressDialog.__init__(self, title, message, maximum, style = wxPD_AUTO_HIDE| wxPD_APP_MODAL)
            
    def UpdateOneStep(self):
        self.Update(self.count)
        self.count = self.count + 1

class AboutDialog(wxDialog):
    version = "AGTk 2.1"
        
    def __init__(self, parent):
        wxDialog.__init__(self, parent, -1, self.version)
        self.panel = wxPanel(self, -1)
        self.version = "AGTk 2.1"
        
        bmp = icons.getAboutBitmap()

        info = "Version: %s \nCopyright@2001-2003 by University of Chicago, \nAll rights reserved\nPlease visit www.accessgrid.org for more information" %self.version
        self.panel.SetSize(wxSize(bmp.GetWidth()-2,bmp.GetHeight()-2))
        image = wxStaticBitmap(self.panel, -1, bmp)
        text = wxStaticText(self.panel, -1, info, pos = wxPoint(80,100))
        self.SetSize(wxSize(bmp.GetWidth()-2,bmp.GetHeight()-2))
        self.__layout()

    def __layout(self):
        box = wxBoxSizer(wxVERTICAL)
        box.Add(self.panel)
        self.SetAutoLayout(1)
        self.SetSizer(box)
        self.Layout()
                       
    def ProcessLeftDown(self, evt):
        self.Hide()
        return false

class AppSplash(wxSplashScreen):
    def __init__(self):
        bmp = icons.getAboutBitmap()
        
        wxSplashScreen.__init__(self, bmp,
                                wxSPLASH_CENTRE_ON_SCREEN|
                                wxSPLASH_NO_TIMEOUT , 4000, None,
                                -1, style=wxSIMPLE_BORDER|
                                wxFRAME_NO_TASKBAR
                                |wxSTAY_ON_TOP)

        self.info = wxStaticText(self, -1, "Loading Venue Client\nPlease be patient.")
        self.__layout()
        EVT_CLOSE(self, self.OnClose)

    def __layout(self):
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.info)
        
        self.SetAutoLayout(1)
        self.SetSizer(box)
        self.Layout()
                
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
                    parts = stuff[k2].split('.')
                    if len(parts) > 1:
                        ext = "." + parts[1]
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

def ProgressDialogTest():
    max = 100
     
    dlg = ProgressDialog("Start up", "Loading Venue Client. Please be patient.", max)
    dlg.Show()
  
    keepGoing = True
    count = 0
    while keepGoing and count < max:
        count = count + 1
        wxSleep(1)

        if count == max / 2:
            keepGoing = dlg.Update(count, "Half-time!")
        else:
            keepGoing = dlg.Update(count)

    dlg.Destroy()

def AboutDialogTest():
    dlg = AboutDialog(None)
    dlg.ShowModal()
    dlg.Destroy()
   
if __name__ == "__main__":
    app = wxPySimpleApp()

    #ProgressDialogTest()
    AboutDialogTest()

    app.MainLoop()
