#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.42 2003-11-06 23:01:30 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: UIUtilities.py,v 1.42 2003-11-06 23:01:30 lefvert Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid.Platform import isWindows, isLinux, isOSX
import string

try:
    import _winreg
except:
    pass

#from wxPython.wx import wxTheMimeTypesManager as mtm
from wxPython.wx import wxFileTypeInfo
from wxPython.lib.throbber import Throbber
from wxPython.wx import *
from wxPython.lib.imagebrowser import *
from AccessGrid import icons

from AccessGrid.Utilities import SubmitBug, VENUE_CLIENT_LOG
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Version import GetVersion
from AccessGrid.Platform import GetUserConfigDir, GetSharedDocDir
from AccessGrid.ClientProfile import ClientProfile

class MessageDialog:
    def __init__(self, frame, text, text2 = "", style = wxOK|wxICON_INFORMATION):
        messageDialog = wxMessageDialog(frame, text, text2, style)
        messageDialog.ShowModal()
        messageDialog.Destroy()

class ErrorDialog:
    def __init__(self, frame, text, text2 = "",
                 style =  wxICON_ERROR |wxYES_NO | wxNO_DEFAULT, logFile = VENUE_CLIENT_LOG):
        
        info = text + "\n\nDo you wish to send an automated error report?"
        errorDialog = wxMessageDialog(frame, info, text2, wxICON_ERROR |wxYES_NO | wxNO_DEFAULT)

        if(errorDialog.ShowModal() == wxID_YES):
            # The user wants to send an error report
            bugReportCommentDialog = BugReportCommentDialog(frame)

            if(bugReportCommentDialog.ShowModal() == wxID_OK):
                # Submit the error report to Bugzilla
                comment = bugReportCommentDialog.GetComment()
                profile = bugReportCommentDialog.GetProfile()
                email = bugReportCommentDialog.GetEmail()

                SubmitBug(comment, profile, email, logFile)
                bugFeedbackDialog = wxMessageDialog(frame, "Your error report has been sent, thank you.",
                                                    "Error Reported", style = wxOK|wxICON_INFORMATION)
                bugFeedbackDialog.ShowModal()
                bugFeedbackDialog.Destroy()       

            bugReportCommentDialog.Destroy()

        errorDialog.Destroy()


class BugReportCommentDialog(wxDialog):
    def __init__(self, parent):
        wxDialog.__init__(self, parent, -1, "Bug Report")
        self.text = wxStaticText(self, -1, "Please, enter a description of the problem you are experiencing.  You may \nreceive periodic mailings from us with information on this problem.  If you \ndo not wish to be contacted, please leave the 'E-mail' field blank.", style=wxALIGN_LEFT)
        
        self.commentBox = wxTextCtrl(self, -1, "", size = wxSize(300,100), style = wxTE_MULTILINE, validator = TextValidator())
        self.line = wxStaticLine(self, -1)
        
        # I have to add this due to a wxPython bug. A wxTextCtrl that has wxTE_MULTILINE
        # flag set ignores focus of next child. If I don't have tmp, the email text ctrl
        # will never get focus when you use the TAB key.
        # --
        if isWindows():
            temp = wxBitmapButton(self, -1, wxEmptyBitmap(1,1), size = wxSize(1,1))
        # --
        
        self.commentText =  wxStaticText(self, -1, "Comment:")
        self.emailText = wxStaticText(self, -1, "E-mail:")
        self.emailBox =  wxTextCtrl(self, -1, "")
        self.infoText = wxStaticText(self, -1, "For more information on bugs, visit http://bugzilla.mcs.anl.gov/AccessGrid ")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.GetClientProfile()
        self.Centre()
        self.Layout()

    def GetClientProfile(self):
        accessGridPath = GetUserConfigDir()
        profileFile = os.path.join(accessGridPath, "profile" )
        profile = ClientProfile(profileFile)

        if profile.IsDefault():
            # This is the default profile and we do not want to
            # use values from it.
            self.profile = None

        else:
            self.profile = profile
      
        # If we have a profile and the email is filled in properly,
        # use email as default.
        if (self.profile
            and self.profile.email != ClientProfile.defaultProfile["ClientProfile.email"]):
            self.emailBox.SetValue(self.profile.email)

    def GetProfile(self):
        return self.profile
    
    def GetEmail(self):
        return self.emailBox.GetValue()
        
    def GetComment(self):
        return self.commentBox.GetValue()

    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.text, 0, wxALL, 10)
        sizer.Add(self.commentText, 0, wxLEFT| wxRIGHT | wxEXPAND, 10)
        sizer.Add(self.commentBox, 0,  wxLEFT| wxRIGHT | wxEXPAND, 10)
        sizer.Add(10,10)
        sizer.Add(self.emailText, 0, wxLEFT| wxRIGHT | wxEXPAND, 10)
        sizer.Add(self.emailBox, 0,  wxLEFT| wxRIGHT | wxBOTTOM | wxEXPAND, 10)
        sizer.Add(self.infoText, 0, wxLEFT | wxRIGHT | wxTOP |  wxEXPAND, 10)
        sizer.Add(self.line, 0, wxALL | wxEXPAND, 10)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 5)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER | wxBOTTOM, 5) 
            
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


class TextValidator(wxPyValidator):
    def __init__(self):
        wxPyValidator.__init__(self)
            
    def Clone(self):
        return TextValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        if val == "":
            MessageDialog(NULL, "Please, enter a comment.")
            return false
       
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.
        
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
        self.message = message
        wxProgressDialog.__init__(self, title, message, maximum,
                                  style = wxPD_AUTO_HIDE| wxPD_APP_MODAL)
            
    def UpdateOneStep(self, msg=""):
        if len(msg) > 0:
            self.Update(self.count, msg)
        else:
            self.Update(self.count)
        self.count = self.count + 1

class AboutDialog(wxDialog):
            
    def __init__(self, parent):
        wxDialog.__init__(self, parent, -1, str(GetVersion()) )
        print 'in about dialog'
        version = str(GetVersion())       
        bmp = icons.getAboutBitmap()
        info = "Version: %s \nPlease visit www.accessgrid.org for more information" %version
        self.ReadLicenseFile()

        print bmp.GetWidth()
        
        self.SetSize(wxSize(bmp.GetWidth()+20, 400))
        
        self.panel = wxPanel(self, -1, size = wxSize(bmp.GetWidth()+20, 400))
        self.image = wxStaticBitmap(self.panel, -1, bmp,
                                    size = wxSize(bmp.GetWidth(), bmp.GetHeight()))
        self.text = wxStaticText(self.panel, -1, info)
        self.text.SetBackgroundColour("WHITE")
        self.license = wxTextCtrl(self.panel, -1, self.licenseText,
                                  size = wxSize(bmp.GetWidth()-10, 200),
                                  style = wxTE_MULTILINE)
        self.okButton = wxButton(self.panel, wxID_OK, "Ok" )
        self.panel.SetBackgroundColour("WHITE")

        self.okButton.SetDefault()
        self.okButton.SetFocus()

        self.__layout()

    def ReadLicenseFile(self):
        '''
        Read COPYING.txt file from shared document directory.
        '''
        path = os.path.join(GetSharedDocDir(), '../COPYING.txt')
        licenseFile = file(os.path.normpath(path))
        self.licenseText = licenseFile.read() 
        licenseFile.close()
               
    def __layout(self):
        '''
        Handle UI layout.
        '''
        sizer = wxBoxSizer(wxHORIZONTAL)
        self.SetSizer(sizer)
        sizer.Add(self.panel)
        
        boxSizer = wxBoxSizer(wxVERTICAL)
        boxSizer.Add(5,5)
        boxSizer.Add(self.image, 0 ,wxALIGN_CENTER)
        boxSizer.Add(self.text, 0 ,wxALIGN_LEFT | wxALL, 10)
        boxSizer.Add(self.license, 1 ,wxALIGN_CENTER |wxEXPAND| wxLEFT | wxRIGHT| wxBOTTOM, 10)
        boxSizer.Add(wxStaticLine(self.panel, -1), 0, wxALL | wxEXPAND, 10)
        boxSizer.Add(self.okButton, 0, wxALIGN_CENTER|wxBOTTOM, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(boxSizer)
        boxSizer.Fit(self)
        
        
class AppSplash(wxSplashScreen):
    def __init__(self):
        bmp = icons.getAboutBitmap()
        
        wxSplashScreen.__init__(self, bmp,
                                wxSPLASH_CENTRE_ON_SCREEN|
                                wxSPLASH_NO_TIMEOUT , 4000, None,
                                -1, style=wxSIMPLE_BORDER|
                                wxFRAME_NO_TASKBAR
                                |wxSTAY_ON_TOP)

        self.info = wxStaticText(self, -1, "Loading Venue Client.")
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
    
# def GetMimeCommands(filename = None, type = None, ext = None):
#      """
#      This function returns anything in the local mime type database for the
#      type or extension specified.
#      """
#      cdict = dict()
    
#      if type != None:
#          fileType = mtm.GetFileTypeFromMimeType(type)
#      elif ext != None:
#          fileType = mtm.GetFileTypeFromExtension(ext)

#      if fileType != None and filename != None:
#          mimeType = fileType.GetMimeType()
#          if mimeType != None:
#              cmds = fileType.GetAllCommands(filename, mimeType)
#              if None == cmds:
#                  verbs = []
#                  cmdlines = []
#              else:
#                  verbs, cmdlines = cmds
#              for i in range(0, len(verbs)):
#                  cdict[string.lower(verbs[i])] = cmdlines[i]
#          else:
#              cdict = None
#      else:
#          cdict = None

#      return cdict

def ProgressDialogTest():
    max = 100
     
    dlg = ProgressDialog("Start up", "Loading Venue Client.", max)
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


    # Test for bug report
    #b = BugReportCommentDialog(None)
    #b.ShowModal()
    #b.Destroy()

    # Test for error dialog (includes bug report)
    #e = ErrorDialog(None, "test", "Enter Venue Error",
    #                style = wxOK  | wxICON_ERROR)
    
    
    app.MainLoop()
    
