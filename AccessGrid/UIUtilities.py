#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.56 2004-04-26 20:43:31 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: UIUtilities.py,v 1.56 2004-04-26 20:43:31 lefvert Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid.Platform import IsWindows
import string
import struct
import os

try:
    import _winreg
except:
    pass

from wxPython.wx import wxFileTypeInfo
from wxPython.lib.throbber import Throbber
from wxPython.wx import *
from wxPython.lib.imagebrowser import *

from AccessGrid import icons
from AccessGrid.Utilities import SubmitBug, VENUE_CLIENT_LOG
from AccessGrid.Version import GetVersion
from AccessGrid.Platform.Config import UserConfig, AGTkConfig
from AccessGrid.Platform import Config

class MessageDialog:
    def __init__(self, frame, text, text2 = "", style = wxOK|wxICON_INFORMATION):
        messageDialog = wxMessageDialog(frame, text, text2, style)
        messageDialog.ShowModal()
        messageDialog.Destroy()

class ErrorDialog:
    def __init__(self, frame, text, text2 = "",
                 style =  wxICON_ERROR |wxYES_NO | wxNO_DEFAULT, logFile = VENUE_CLIENT_LOG):
        info = text + "\n\nDo you wish to send an automated error report?"
        errorDialog = wxMessageDialog(frame, info, text2, style)

        if(errorDialog.ShowModal() == wxID_YES):
            # The user wants to send an error report
            bugReportCommentDialog = BugReportCommentDialog(frame)

            if(bugReportCommentDialog.ShowModal() == wxID_OK):
                # Submit the error report to Bugzilla
                comment = bugReportCommentDialog.GetComment()
                email = bugReportCommentDialog.GetEmail()

                SubmitBug(comment,  email, logFile, Config.UserConfig.instance())
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
        if IsWindows():
            temp = wxBitmapButton(self, -1, wxEmptyBitmap(1,1), size = wxSize(1,1))
        # --
        
        self.commentText =  wxStaticText(self, -1, "Comment:")
        self.emailText = wxStaticText(self, -1, "E-mail:")
        self.emailBox =  wxTextCtrl(self, -1, "")
        self.infoText = wxStaticText(self, -1, "For more information on bugs, visit http://bugzilla.mcs.anl.gov/AccessGrid ")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
    
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
        sizer.Add(self.emailText, 0, wxLEFT| wxRIGHT | wxTOP| wxEXPAND, 10)
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
        
def formatExceptionInfo(maxTBlevel=5):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb)


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
        version = str(GetVersion())       
        bmp = icons.getAboutBitmap()
        info = "Version: %s \nPlease visit www.accessgrid.org for more information" %version
        self.ReadLicenseFile()

        
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
        config = AGTkConfig.instance()
        path = os.path.join(config.GetDocDir(), '../COPYING.txt')
        licenseFile = file(os.path.normpath(path))
        self.licenseText = licenseFile.read() 
        licenseFile.close()
               
    def __layout(self):
        '''
        Handle UI layout.
        '''
        sizer = wxBoxSizer(wxHORIZONTAL)
        
        sizer.Add(self.panel, 1, wxEXPAND)
        
        boxSizer = wxBoxSizer(wxVERTICAL)
        boxSizer.Add(5,5)
        boxSizer.Add(self.image, 0 ,wxALIGN_CENTER)
        boxSizer.Add(self.text, 0 ,wxALIGN_LEFT | wxALL, 10)
        boxSizer.Add(self.license, 1 ,wxALIGN_CENTER |wxEXPAND| wxLEFT | wxRIGHT| wxBOTTOM, 10)
        boxSizer.Add(wxStaticLine(self.panel, -1), 0, wxALL | wxEXPAND, 10)
        boxSizer.Add(self.okButton, 0, wxALIGN_CENTER|wxBOTTOM, 10)

        self.panel.SetSizer(boxSizer)
        boxSizer.Fit(self.panel)

        sizer.Fit(self)
        
        
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
       

class FileLocationWidget(wxPanel):
    """
    A FileLocationWidget has a label, text field, and browse button.

    It is configured with a list of tuples (wildcard description, wildcard) which
    will be used to configure the file browser dialog.

    The selected path is available via the GetPath() method.
    """

    def __init__(self, parent, title, label, wildcardDesc, fileSelectCB):
        wxPanel.__init__(self, parent, -1, style = 0)

        self.title = title
        self.fileSelectCB = fileSelectCB
        self.wildcardDesc = wildcardDesc
        self.path = ""
        self.lastFilterIndex = 0
        
        sizer = self.sizer = wxBoxSizer(wxHORIZONTAL)
        t = wxStaticText(self, -1, label)
        sizer.Add(t, 0, wxALIGN_CENTER_VERTICAL)
        
        self.text = wxTextCtrl(self, -1, style = wxTE_PROCESS_ENTER)
        sizer.Add(self.text, 1, wxALIGN_CENTER_VERTICAL)
        EVT_TEXT_ENTER(self, self.text.GetId(), self.OnTextEnter)
        EVT_KILL_FOCUS(self.text, self.OnTextLoseFocus)
        
        b = wxButton(self, -1, "Browse")
        sizer.Add(b, 0)
        EVT_BUTTON(self, b.GetId(), self.OnBrowse)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        self.Fit()

    def GetPath(self):
        return self.path

    def OnTextEnter(self, event):
        self.path = self.text.GetValue()
        if self.fileSelectCB is not None:
            self.fileSelectCB(self, self.path)

    def OnTextLoseFocus(self, event):
        self.path = self.text.GetValue()
        if self.fileSelectCB is not None:
            self.fileSelectCB(self, self.path)

    def OnBrowse(self, event):
        path = self.path
        dir = file = ""
        
        if path != "":
            if os.path.isdir(path):
                dir = path
            elif os.path.isfile(path):
                dir, file = os.path.split(path)
            else:
                #
                # User entered an invalid file; point the browser
                # at the directory containing that file.
                #
                dir, file = os.path.split(path)
                file = ""

        wildcard = "|".join(map(lambda a: "|".join(a), self.wildcardDesc))
        dlg = wxFileDialog(self, self.title,
                           defaultDir = dir,
                           defaultFile = file,
                           wildcard = wildcard,
                           style = wxOPEN)
        dlg.SetFilterIndex(self.lastFilterIndex)

        rc = dlg.ShowModal()

        if rc != wxID_OK:
            dlg.Destroy()
            return

        self.lastFilterIndex = dlg.GetFilterIndex()

        self.path = path = dlg.GetPath()
        self.text.SetValue(path)
        self.text.SetInsertionPointEnd()

        if self.fileSelectCB is not None:
            self.fileSelectCB(self, self.path)

class SecureTextCtrl(wxTextCtrl):
    """
    Securely read passwords.

    "Securely" means that the password is never present
    as a python string, since once creatd, strings hang around in memory
    even after being garbage collected.

    Instead, maintain the text as a list of character codes.

    """
    
    def __init__(self, parent, id, size = wxDefaultSize):

        wxTextCtrl.__init__(self, parent, id,
                            style = wxTE_RICH2,
                            size = size)

        EVT_TEXT_ENTER(self, self.GetId(), self.OnEnter)
        EVT_CHAR(self, self.OnChar)
        EVT_KEY_DOWN(self, self.OnKeyDown)

        self.chars = []

    def GetChars(self):
        """
        Return the current value of the text.

        """
        
        return self.chars[:]

    def FlushChars(self):
        """
        Clear the control and erase the stored password.
        """
        
        for i in range(len(self.chars)):
            self.chars[i] = 0

        del self.chars
        self.chars = []
        self.Clear()

    def CanPaste(self):
        return 0

    def OnEnter(self, event):
        pass

    def OnPaste(self, event):
        self.doPaste()

    def doPaste(self):
        wxTheClipboard.Open()
        data = wxTextDataObject()
        wxTheClipboard.GetData(data)
        wxTheClipboard.Close()
        txt = str(data.GetText())
        for k in txt:
            ch, = struct.unpack('b', k)
            self.insertChar(ch)

    def deleteSelection(self, sel):
        del self.chars[sel[0]: sel[1]]
        self.Remove(sel[0], sel[1])
        
    def insertChar(self, k):
        sel = self.GetSelection()
        pos = self.GetInsertionPoint()

        if sel[0] < sel[1]:
            self.deleteSelection(sel)
            
        # ch = k ^ 0x80
        ch = struct.pack('b', k)

        self.Replace(pos, pos, "*")
        self.chars.insert(pos, ch)
        self.SetInsertionPoint(pos + 1)
    
    def OnKeyDown(self, event):
        t = event.GetEventObject()
        k = event.GetKeyCode()

        #
        # We only worry about control keys here.
        #
        if not event.ControlDown():
            event.Skip()
            return
        
        if k == ord('V'):
            #
            # Ctl-V
            #
            self.doPaste()

        elif k == ord('C'):
            #
            # Ctl-C
            #
            # Don't do anything - disallow copying password.
            #
            pass

        else:
            event.Skip()

    def OnChar(self, event):
        t = event.GetEventObject()
        k = event.GetKeyCode()
        kr = event.GetRawKeyCode()

        if k == WXK_BACK:
            sel = self.GetSelection()

            if sel[0] < sel[1]:
                self.deleteSelection(sel)
            else:
                pos = self.GetInsertionPoint()
                if pos > 0:
                    del self.chars[pos - 1 : pos]
                    self.Remove(pos - 1, pos)
        elif k == WXK_RETURN:
            event.Skip()
            return
        elif k == WXK_TAB:
            event.Skip()
            return
        elif k == WXK_DELETE:
            sel = self.GetSelection()
            pos = self.GetInsertionPoint()

            if sel[0] < sel[1]:
                self.deleteSelection(sel)
            else:
                if pos < self.GetLastPosition():
                    del self.chars[pos : pos + 1]
                    self.Remove(pos , pos + 1)
        elif k < 127 and k >= 32:
            self.insertChar(k)
                         
        elif k == WXK_LEFT:
            pos = self.GetInsertionPoint()
            if pos > 0:
                self.SetInsertionPoint(pos - 1)
        elif k == WXK_RIGHT:
            pos = self.GetInsertionPoint()
            if pos < self.GetLastPosition():
                self.SetInsertionPoint(pos + 1)
        elif k == ord('V') - 64:
            #
            # Ctl-V
            #
            self.doPaste()
        else:
            event.Skip()

class PassphraseDialog(wxDialog):
    """
    Dialog to retrieve a passphrase from  the user.

    Uses SecureTextCtrl so the returned passphrase is a list of integers.
    """
    
    def __init__(self, parent, message, caption, size = wxSize(400,400)):
        """
        Create passphrase dialog.

        @param parent: parent widget
        @param message: message to show on the dialog.
        @param caption: string to show in window title.
        """

        wxDialog.__init__(self, parent, -1, caption,
                          style = wxDEFAULT_DIALOG_STYLE,
                          size = size)

        topsizer = wxBoxSizer(wxVERTICAL)

        ts = self.CreateTextSizer(message)
        topsizer.Add(ts, 0, wxALL, 10)

        self.text = SecureTextCtrl(self, -1, size = wxSize(300, -1))
        topsizer.Add(self.text, 0, wxEXPAND | wxLEFT | wxRIGHT, 15)

        buttons = self.CreateButtonSizer(wxOK | wxCANCEL)
        topsizer.Add(buttons, 0, wxCENTRE | wxALL, 10)

        EVT_BUTTON(self, wxID_OK, self.OnOK)
        EVT_CLOSE(self, self.OnClose)
        
        self.text.SetFocus()
        
        self.SetSizer(topsizer)
        self.SetAutoLayout(1)
        self.Fit()

    def __del__(self):
        self.FlushChars()
        
    def OnClose(self, event):
        self.FlushChars()
        self.EndModal(wxID_CANCEL)
        self.Destroy()

    def OnOK(self, event):
        self.EndModal(wxID_OK)

    def GetChars(self):
        return self.text.GetChars()

    def FlushChars(self):
        return self.text.FlushChars()

class PassphraseVerifyDialog(wxDialog):
    """
    Dialog to retrieve a passphrase from user. It requires the
    user to type the passphrase twice to verify it.

    Uses SecureTextCtrl so the returned passphrase is a list of integers.
    """
    
    def __init__(self, parent, message1, message2, caption,
                 size = wxSize(400,400)):
        """
        Create passphrase dialog.

        @param parent: parent widget
        @param message1: message to show on the dialog before the first text input field.
        @param message2: message to show on the dialog before the second text input field.
        @param caption: string to show in window title.
        """

        wxDialog.__init__(self, parent, -1, caption,
                          size = size,
                          style = wxDEFAULT_DIALOG_STYLE)

        #
        # Need to create a panel so that tab traversal works properly.
        # Should be fixed in wx 2.5.
        #
        # http://lists.wxwidgets.org/cgi-bin/ezmlm-cgi?11:mss:26416:200403:laipomedjcjdlbblliki
        #
        
        panel = wxPanel(self, -1, style = wxTAB_TRAVERSAL)
        topsizer = wxBoxSizer(wxVERTICAL)

        #
        # can't do this with the intervening panel 
        #ts = self.CreateTextSizer(message1)
        #topsizer.Add(ts, 0, wxALL, 10)

        txt = wxStaticText(panel, -1, message1)
        topsizer.Add(txt, 0, wxALL, 10)

        self.text1 = SecureTextCtrl(panel, -1, size = wxSize(300, -1))
        topsizer.Add(self.text1, 0, wxEXPAND | wxLEFT | wxRIGHT, 15)

        #ts = self.CreateTextSizer(message2)
        #topsizer.Add(ts, 0, wxALL, 10)

        txt = wxStaticText(panel, -1, message2)
        topsizer.Add(txt, 0, wxALL, 10)

        self.text2 = SecureTextCtrl(panel, -1, size = wxSize(300, -1))

        topsizer.Add(self.text2, 0, wxEXPAND | wxLEFT | wxRIGHT, 15)

        # buttons = self.CreateButtonSizer(wxOK | wxCANCEL)
        # topsizer.Add(buttons, 0, wxCENTRE | wxALL, 10)

        b = wxButton(panel, wxID_OK, "OK")
        topsizer.Add(b, 0, wxALIGN_RIGHT | wxALL, 10)

        EVT_BUTTON(self, wxID_OK, self.OnOK)
        EVT_CLOSE(self, self.OnClose)
        
        self.text1.SetFocus()
        
        panel.SetSizer(topsizer)
        panel.SetAutoLayout(1)
        panel.Fit()
        self.SetAutoLayout(1)
        self.Fit()

    def __del__(self):
        self.FlushChars()
        
    def OnClose(self, event):
        self.FlushChars()
        self.EndModal(wxID_CANCEL)
        self.Destroy()

    def OnOK(self, event):

        #
        # Doublecheck to see if the passphrases match.
        #
        
        if self.text1.GetChars() != self.text2.GetChars():
            dlg = wxMessageDialog(self,
                                  "Entered passphrases do not match.",
                                  "Verification error.",
                                  style = wxOK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.EndModal(wxID_OK)

    def GetChars(self):
        return self.text1.GetChars()

    def FlushChars(self):
        self.text1.FlushChars()
        self.text2.FlushChars()

def PassphraseDialogTest():
    
    a = wxPySimpleApp()

    d = PassphraseDialog(None, "Message", "Caption")

    print d.ShowModal()
    chars = d.GetChars()
    d.FlushChars()
    d.Destroy()

    print chars
        
def PassphraseVerifyDialogTest():
    
    a = wxPySimpleApp()

    d = PassphraseVerifyDialog(None, "Message", "And again", "Caption")

    print d.ShowModal()
    chars = d.GetChars()
    d.FlushChars()
    d.Destroy()

    print chars
   
############################################################################
# Add URL Base Dialog

class AddURLBaseDialog(wxDialog):
       
    def __init__(self, parent, id, name, type = 'venue'):
        wxDialog.__init__(self, parent, id, "Add current venue")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.type = type
        self.Centre()
        info = "Current %s will be added to your list of %s."%(self.type,self.type)
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.addressText = wxStaticText(self, -1, "Name: ", style=wxALIGN_LEFT)
        self.address = wxTextCtrl(self, -1, name, size = wxSize(300,20))
        self.Layout()
                        
    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 20)

        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.addressText, 0)
        sizer2.Add(self.address, 1, wxEXPAND)

        sizer1.Add(sizer2, 0, wxEXPAND | wxALL, 20)

        sizer3 =  wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)

        sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
        sizer.Add(sizer3, 0, wxALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
    def GetValue(self):
        return self.address.GetValue()


################################################################################
#
# Edit URL Base Dialog

class EditURLBaseDialog(wxDialog):
    ID_DELETE = wxNewId() 
    ID_RENAME = wxNewId()
    ID_LIST = wxNewId()
    listWidth = 500
    listHeight = 200
    currentItem = 0
             
    def __init__(self, parent, id, title, myUrlsDict, type = 'venue'):
        wxDialog.__init__(self, parent, id, title)
        self.parent = parent 
        self.dictCopy = myUrlsDict.copy()
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        self.type = type
        info = "Please, right click on the %s you want to edit and choose from the \noptions available in the menu."%(self.type)
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.myUrlsList= wxListCtrl(self, self.ID_LIST, 
                                       size = wxSize(self.listWidth, self.listHeight), 
                                       style=wxLC_REPORT)
        self.myUrlsList.InsertColumn(0, "Name")
        self.myUrlsList.SetColumnWidth(0, self.listWidth * 1.0/3.0)
        self.myUrlsList.InsertColumn(1, "Url ")
        self.myUrlsList.SetColumnWidth(1, self.listWidth * 2.0/3.0)
        
        self.menu = wxMenu()
        self.menu.Append(self.ID_RENAME,"Rename", "Rename selected %s" %self.type)
        self.menu.Append(self.ID_DELETE,"Delete", "Delete selected %s" %self.type)
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.Layout()
        self.__PopulateList()
        self.__SetEvents()
        
    def __SetEvents(self):
        EVT_RIGHT_DOWN(self.myUrlsList, self.OnRightDown)
        EVT_LIST_ITEM_SELECTED(self.myUrlsList, self.ID_LIST, self.OnItemSelected)
        EVT_MENU(self.menu, self.ID_RENAME, self.OnRename)
        EVT_MENU(self.menu, self.ID_DELETE, self.OnDelete)
               
    def __PopulateList(self):
        i = 0
        self.myUrlsList.DeleteAllItems()
        for name in self.dictCopy.keys():
            self.myUrlsList.InsertStringItem(i, name)
            self.myUrlsList.SetStringItem(i, 1, self.dictCopy[name])
            i = i + 1

    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 10)
        sizer1.Add(self.myUrlsList, 1, wxALL, 10)

        sizer3 =  wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)

        sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
        sizer.Add(sizer3, 0, wxALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

    def OnDelete(self, event):
        print "Deleting ",self.currentItem
        if(self.dictCopy.has_key(self.currentItem)):
            del self.dictCopy[self.currentItem]
            self.__PopulateList()
            print " dict copy = ", self.dictCopy
        else:
            text = "Please, select the %s you want to delete"%self.type
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)

    def OnRename(self, event):
        if(self.dictCopy.has_key(self.currentItem)):
            renameDialog = RenameDialog(self, -1, "Rename %s"%self.type, type = self.type)
            
        else:
            text = "Please, select the %s you want to rename"%self.type
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)

    def DoesNameExist(self, name):
        return self.dictCopy.has_key(name)
                        
    def Rename(self, name):
        if(self.dictCopy.has_key(self.currentItem)):
            self.dictCopy[name] = self.dictCopy[self.currentItem]
            del self.dictCopy[self.currentItem]

            self.myUrlsList.SetItemText(self.currentIndex, name)
        else:
            log.info("EditMyUrlsDialog:Rename: The %s is not present in the dictionary"%self.type)
               
    def OnItemSelected(self, event):
        self.currentIndex = event.m_itemIndex
        self.currentItem = self.myUrlsList.GetItemText(event.m_itemIndex)
        print "Selected ", self.currentItem
              
    def OnRightDown(self, event):
        self.x = event.GetX() + self.myUrlsList.GetPosition().x
        self.y = event.GetY() + self.myUrlsList.GetPosition().y
        self.PopupMenu(self.menu, wxPoint(self.x, self.y))
        event.Skip()
        
    def GetValue(self):
        return self.dictCopy


class RenameDialog(wxDialog):

    def __init__(self, parent, id, title, type = 'venue'):
        wxDialog.__init__(self, parent, id, title)
        self.type = type
        self.text = wxStaticText(self, -1, "Please, fill in the new name of your %s"%self.type,
                                 style=wxALIGN_LEFT)
        self.nameText = wxStaticText(self, -1, "New Name: ",
                                     style=wxALIGN_LEFT)
        print 'before creating my urls ', self.type
        v = MyUrlsEditValidator(type = self.type)
        self.name = wxTextCtrl(self, -1, "", size = wxSize(300,20),
                               validator = v)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
        self.parent = parent
        
        if(self.ShowModal() == wxID_OK):
            parent.Rename(self.name.GetValue())
        self.Destroy()
                       
    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 20)

        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.nameText, 0)
        sizer2.Add(self.name, 1, wxEXPAND)

        sizer1.Add(sizer2, 0, wxEXPAND | wxALL, 20)

        sizer3 =  wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)

        sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
        sizer.Add(sizer3, 0, wxALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
    def DoesNameExist(self, name):
        return self.parent.DoesNameExist(name)
        
    def GetValue(self):
        return self.address.GetValue()
        
        
class MyUrlsEditValidator(wxPyValidator):
    def __init__(self, type = 'venue'):
        wxPyValidator.__init__(self)
        self.type = type

    def Clone(self):
        return MyUrlsEditValidator(self.type)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        nameExists = win.DoesNameExist(val)

        if nameExists:
            info = "A %s with the same name is already added, please select a different name."%self.type
            dlg = wxMessageDialog(None, info, "Duplicated %s"%self.type, 
                                  style = wxOK | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return false

        return true
    
    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.
                


        
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
    
