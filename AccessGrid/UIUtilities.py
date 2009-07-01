#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.96 2007-10-08 01:38:53 willing Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: UIUtilities.py,v 1.96 2007-10-08 01:38:53 willing Exp $"

from AccessGrid import Log
log = Log.GetLogger(Log.UIUtilities)

from AccessGrid.Platform import IsWindows, IsOSX, IsLinux, IsFreeBSD
import string
import struct
import os
import time

try:
    import _winreg
except:
    pass

import wx

from AccessGrid import icons
from AccessGrid.Utilities import SubmitBug, VENUE_CLIENT_LOG
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Version import GetVersion, GetStatus, GetBuildNumber
from AccessGrid.Platform.Config import UserConfig, AGTkConfig
from AccessGrid.Platform import Config

class MessageDialog:
    def __init__(self, frame, text, text2 = "", style = wx.OK|wx.ICON_INFORMATION):
        messageDialog = wx.MessageDialog(frame, text, text2, style)
        messageDialog.ShowModal()
        messageDialog.Destroy()

class ErrorDialog:
    def __init__(self, frame, text, text2 = "",
                 style =  wx.ICON_ERROR |wx.YES_NO | wx.NO_DEFAULT, logFile = VENUE_CLIENT_LOG,
                 extraBugCommentText=""):
        info = text + "\n\nDo you wish to send an automated error report?"
        errorDialog = wx.MessageDialog(frame, info, text2, style)

        if(errorDialog.ShowModal() == wx.ID_YES):
            # The user wants to send an error report
            bugReportCommentDialog = BugReportCommentDialog(frame)

            if(bugReportCommentDialog.ShowModal() == wx.ID_OK):
                # Submit the error report to Bugzilla
                comment = bugReportCommentDialog.GetComment()
                email = bugReportCommentDialog.GetEmail()
                try:
                    # load profile
                    userConfig = Config.UserConfig.instance()
                    profileFile = os.path.join(userConfig.GetConfigDir(),
                                               "profile" )
                    profile = ClientProfile(profileFile)
                except:
                    profile = None
                
                if len(extraBugCommentText) > 0:
                    comment = comment + "\n\n----------------\n\n" + extraBugCommentText
                SubmitBug(comment, profile, email, logFile)
                bugFeedbackDialog = wx.MessageDialog(frame, "Your error report has been sent, thank you.",
                                                    "Error Reported", style = wx.OK|wx.ICON_INFORMATION)
                bugFeedbackDialog.ShowModal()
                bugFeedbackDialog.Destroy()       

            bugReportCommentDialog.Destroy()

        errorDialog.Destroy()


class BugReportCommentDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Bug Report")
        self.text = wx.StaticText(self, -1, "Please, enter a description of the problem you are experiencing.  You may \nreceive periodic mailings from us with information on this problem.  If you \ndo not wish to be contacted, please leave the 'E-mail' field blank.", style=wx.ALIGN_LEFT)
        
        self.commentBox = wx.TextCtrl(self, -1, "", size = wx.Size(300,100),
                                     style = wx.TE_MULTILINE,
                                     validator = TextValidator())
        self.line = wx.StaticLine(self, -1)
        
        # I have to add this due to a wxPython bug. A wx.TextCtrl that
        # has wx.TE_MULTILINE flag set ignores focus of next child. If
        # I don't have tmp, the email text ctrl will never get focus
        # when you use the TAB key.  --

        if IsWindows():
            temp = wx.BitmapButton(self, -1, wx.EmptyBitmap(1,1),
                                  size = wx.Size(1,1))
        # --
        
        self.commentText =  wx.StaticText(self, -1, "Comment:")
        self.emailText = wx.StaticText(self, -1, "E-mail:")
        self.emailBox =  wx.TextCtrl(self, -1, "")
        self.infoText = wx.StaticText(self, -1, "For more information on bugs, visit http://bugzilla.mcs.anl.gov/AccessGrid ")
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
    
    def GetEmail(self):
        return self.emailBox.GetValue()
        
    def GetComment(self):
        return self.commentBox.GetValue()

    def Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 0, wx.ALL, 10)
        sizer.Add(self.commentText, 0, wx.LEFT| wx.RIGHT | wx.EXPAND, 10)
        sizer.Add(self.commentBox, 0,  wx.LEFT| wx.RIGHT | wx.EXPAND, 10)
        sizer.Add((10,10))
        sizer.Add(self.emailText, 0, wx.LEFT| wx.RIGHT | wx.TOP| wx.EXPAND, 10)
        sizer.Add(self.emailBox, 0,  wx.LEFT| wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        sizer.Add(self.infoText, 0, wx.LEFT | wx.RIGHT | wx.TOP |  wx.EXPAND, 10)
        sizer.Add(self.line, 0, wx.ALL | wx.EXPAND, 10)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
        sizer.Add(buttonSizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5) 
            
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


class TextValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
            
    def Clone(self):
        return TextValidator()

    def Validate(self,win):
        tc = self.GetWindow()
        val = tc.GetValue()

        if val == "":
            MessageDialog(None, "Please, enter a comment.")
            return False
       
        return True

    def TransferToWindow(self):
        # Prevent wx.Dialog from complaining.
        return True 

    def TransferFromWindow(self):
        # Prevent wx.Dialog from complaining.
        return True 
        
class ErrorDialogWithTraceback:
    def __init__(self, frame, text, text2 = "", style = wx.OK | wx.ICON_ERROR):
        
       (name, args, traceback_string_list) = formatExceptionInfo()

       tbstr = ""
       for x in traceback_string_list:
           print(x)
           tbstr += x + "\n"
       import sys
       print sys.exc_type
       print sys.exc_value
       info = text + "\n\n"+"Type: "+str(sys.exc_type)+"\n"+"Value: "+str(sys.exc_value) + "\nTraceback:\n" + tbstr
       errorDialog = wx.MessageDialog(frame, info, text2, style)
       errorDialog.ShowModal()
       errorDialog.Destroy()
        
class ProgressDialog(wx.Frame):
    def __init__(self, parent, bmp, max, versionText=""):
        height = bmp.GetHeight()
        width = bmp.GetWidth()
        self.max = max
        msgHeight = 20
        gaugeHeight = 15
        gaugeBorder = 1
        gaugeWidth = min(300, width - 100)
        padding = 5

        wx.Frame.__init__(self, parent=parent, title="Starting AccessGrid", style=wx.SIMPLE_BORDER)
        SetIcon(self)
        self.CenterOnScreen()
        self.SetBackgroundColour(wx.WHITE)
        
        self.bitmapCtrl = wx.StaticBitmap(self, -1, bmp, wx.Point(0, 0), wx.Size(width, height))
        self.versionTextCtrl = wx.StaticText(self,-1,versionText,
                                    size=wx.Size(width,-1),
                                    style = wx.ALIGN_CENTRE)
        self.lineCtrl = wx.StaticLine(self,-1,size=wx.Size(width,-1))
        self.progressText = wx.StaticText(self, -1, "",  
                                size=wx.Size(width, msgHeight),
                                style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE)
        self.progressText.SetBackgroundColour(wx.WHITE)
        gaugeBox = wx.Window(self, -1, 
                        size=wx.Size(gaugeWidth, gaugeHeight))
        gaugeBox.SetBackgroundColour(wx.WHITE)
        self.gauge = wx.Gauge(gaugeBox, -1,
                              range = max,
                              style = wx.GA_HORIZONTAL|wx.GA_SMOOTH,
                              size  = (gaugeWidth - 2 * gaugeBorder,
                                       gaugeHeight - 2 * gaugeBorder))
        #self.gauge.SetBackgroundColour(wx.Colour(0xff, 0xff, 0xff))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.bitmapCtrl,0)
        sizer.Add(self.versionTextCtrl,0,wx.BOTTOM,10)
        sizer.Add(self.lineCtrl,0)
        sizer.Add(self.progressText,0,wx.TOP,10)
        sizer.Add(gaugeBox,0,wx.ALIGN_CENTRE|wx.BOTTOM,20)
        
        self.SetSizer(sizer)
        self.Fit()
        
    def UpdateGauge(self, text, progress=None, increment=0):
        curval = self.gauge.GetValue()
        if progress:
            increment = progress-curval
        else:
            progress = curval+increment
			
        # cycle around to the beginning if progress exceeds max
        # this may seem wrong, but the emphasis is on continuing 
        # the indication of progress given to the user
        if progress > self.max:
            progress -= self.max

        self.progressText.SetLabel(text)
        for i in range(increment):
            self.gauge.SetValue(curval+i)
            self.lineCtrl.Update()
            self.versionTextCtrl.Update()
            self.bitmapCtrl.Update()
            time.sleep(0.03)
            
        self.gauge.SetValue(progress)
        self.lineCtrl.Update()
        self.versionTextCtrl.Update()
        self.bitmapCtrl.Update()
        wx.Yield()

    def Destroy(self):
        self._startup = False
        self.gauge.SetValue(self.max)
        wx.Yield()
        #time.sleep(0.2) #give the user a chance to see the gauge reach 100%
        wx.Frame.Destroy(self)
        

class AboutDialog(wx.Dialog):
            
    def __init__(self, parent):
        version = str(GetVersion()) + " "+GetStatus() + "  (build %s)" % GetBuildNumber()
        wx.Dialog.__init__(self, parent, -1, version)
        bmp = icons.getSplashBitmap()
        info = "Version: %s \nPlease visit www.accessgrid.org for more information" %version
        self.ReadLicenseFile()

        
        self.SetSize(wx.Size(bmp.GetWidth()+20, 400))
        
        self.panel = wx.Panel(self, -1, size = wx.Size(bmp.GetWidth()+20, 400))
        self.image = wx.StaticBitmap(self.panel, -1, bmp,
                                    size = wx.Size(bmp.GetWidth(), bmp.GetHeight()))
        self.text = wx.StaticText(self.panel, -1, info)
        self.text.SetBackgroundColour("WHITE")
        self.license = wx.TextCtrl(self.panel, -1, self.licenseText,
                                  size = wx.Size(bmp.GetWidth()-10, 200),
                                  style = wx.TE_MULTILINE)
        self.okButton = wx.Button(self.panel, wx.ID_OK, "Ok" )
        self.panel.SetBackgroundColour("WHITE")

        self.okButton.SetDefault()
        self.okButton.SetFocus()

        self.__layout()

    def ReadLicenseFile(self):
        '''
        Read COPYING.txt file from shared document directory.
        '''
        config = AGTkConfig.instance()
        path = os.path.join(config.GetDocDir(), 'COPYING.txt')
        licenseFile = file(os.path.normpath(path))
        self.licenseText = licenseFile.read() 
        licenseFile.close()
               
    def __layout(self):
        '''
        Handle UI layout.
        '''
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add(self.panel, 1, wx.EXPAND)
        
        boxSizer = wx.BoxSizer(wx.VERTICAL)
        boxSizer.Add((5,5))
        boxSizer.Add(self.image, 0 ,wx.ALIGN_CENTER)
        boxSizer.Add(self.text, 0 ,wx.ALIGN_LEFT | wx.ALL, 10)
        boxSizer.Add(self.license, 1 ,wx.ALIGN_CENTER |wx.EXPAND| wx.LEFT | wx.RIGHT| wx.BOTTOM, 10)
        boxSizer.Add(wx.StaticLine(self.panel, -1), 0, wx.ALL | wx.EXPAND, 10)
        boxSizer.Add(self.okButton, 0, wx.ALIGN_CENTER|wx.BOTTOM, 10)

        self.panel.SetSizer(boxSizer)
        boxSizer.Fit(self.panel)

        sizer.Fit(self)
        
def ProgressDialogTest():
    maxSize = 100
     
    dlg = ProgressDialog(None, icons.getSplashBitmap(),100, "VERSION")
    dlg.Show()

    count = 0
    while count < maxSize:
        count = count + 1
        wx.Sleep(0.2)
        dlg.UpdateGauge('update '+ str(count), count)

    dlg.Destroy()

def AboutDialogTest():
    dlg = AboutDialog(None)
    dlg.ShowModal()
    dlg.Destroy()
       

class FileLocationWidget(wx.Panel):
    """
    A FileLocationWidget has a label, text field, and browse button.

    It is configured with a list of tuples (wildcard description, wildcard) which
    will be used to configure the file browser dialog.

    The selected path is available via the GetPath() method.
    """

    def __init__(self, parent, title, label, wildcardDesc, fileSelectCB):
        wx.Panel.__init__(self, parent, -1, style = 0)

        self.title = title
        self.fileSelectCB = fileSelectCB
        self.wildcardDesc = wildcardDesc
        self.path = ""
        self.lastFilterIndex = 0
        
        sizer = self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self, -1, label)
        sizer.Add(t, 0, wx.ALIGN_CENTER_VERTICAL)
        
        self.text = wx.TextCtrl(self, -1, style = wx.TE_PROCESS_ENTER)
        sizer.Add(self.text, 1, wx.ALIGN_CENTER_VERTICAL)
        wx.EVT_TEXT_ENTER(self, self.text.GetId(), self.OnTextEnter)
        if not(IsOSX() and wx.VERSION >= (2,5,3,0)):
            wx.EVT_KILL_FOCUS(self.text, self.OnTextLoseFocus)
        
        b = wx.Button(self, -1, "Browse")
        sizer.Add(b, 0)
        wx.EVT_BUTTON(self, b.GetId(), self.OnBrowse)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        self.Fit()

    def GetPath(self):
        return str(self.text.GetValue())

    def OnTextEnter(self, event):
        self.path = self.text.GetValue()
        if self.fileSelectCB is not None:
            self.fileSelectCB(self, self.path)

    def OnTextLoseFocus(self, event):
        self.path = self.text.GetValue()
        if self.fileSelectCB is not None:
            self.fileSelectCB(self, self.path)
        event.Skip()

    def OnBrowse(self, event):
        path = self.path
        fdir = ffile = ""
        
        if path != "":
            if os.path.isdir(path):
                fdir = path
            elif os.path.isfile(path):
                fdir, ffile = os.path.split(path)
            else:
                # User entered an invalid file; point the browser
                # at the directory containing that file.
                fdir, ffile = os.path.split(path)
                ffile = ""

        wildcard = "|".join(map(lambda a: "|".join(a), self.wildcardDesc))
        dlg = wx.FileDialog(self, self.title,
                           defaultDir = fdir,
                           defaultFile = ffile,
                           wildcard = wildcard,
                           style = wx.OPEN)
        dlg.SetFilterIndex(self.lastFilterIndex)

        rc = dlg.ShowModal()

        if rc != wx.ID_OK:
            dlg.Destroy()
            return

        self.lastFilterIndex = dlg.GetFilterIndex()

        self.path = path = dlg.GetPath()
        self.text.SetValue(path)
        self.text.SetInsertionPointEnd()

        if self.fileSelectCB is not None:
            self.fileSelectCB(self, self.path)

class SecureTextCtrl(wx.TextCtrl):
    """
    Securely read passwords.

    "Securely" means that the password is never present
    as a python string, since once creatd, strings hang around in memory
    even after being garbage collected.

    Instead, maintain the text as a list of character codes.

    """
    
    def __init__(self, parent, id, size = wx.DefaultSize):

        wx.TextCtrl.__init__(self, parent, id,
                            style = wx.TE_RICH2,
                            size = size)

        wx.EVT_TEXT_ENTER(self, self.GetId(), self.OnEnter)
        wx.EVT_CHAR(self, self.OnChar)
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)

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
        wx.TheClipboard.Open()
        data = wx.TextDataObject()
        wx.TheClipboard.GetData(data)
        wx.TheClipboard.Close()
        txt = str(data.GetText())
        for k in txt:
            ch, = struct.unpack('b', k)
            self.insertChar(ch)

    def deleteSelection(self, sel):
        del self.chars[sel[0]: sel[1]]
        self.Remove(sel[0], sel[1])
        if IsOSX() and wx.VERSION >= (2,6,0,0):
            self.SetInsertionPoint(sel[0])
        
    def insertChar(self, k):
        sel = self.GetSelection()
        pos = self.GetInsertionPoint()

        if sel[0] < sel[1]:
            self.deleteSelection(sel)
            
        ch = struct.pack('b', k)

        self.Replace(pos, pos, "*")
        self.chars.insert(pos, ch)
        self.SetInsertionPoint(pos + 1)
    
    def OnKeyDown(self, event):
        k = event.GetKeyCode()

        # We only worry about control keys here.
        # sigh, special handling for osx/wx.2.6
        controlDown = 0
        if wx.VERSION >= (2,6,0,0):
            controlDown = event.CmdDown()
        else:
            controlDown = event.ControlDown()
        if not controlDown:
            event.Skip()
            return
        
        if k == ord('V'):
            # Ctl-V
            self.doPaste()

        elif k == ord('C'):
            # Ctl-C
            # Don't do anything - disallow copying password.
            pass

        else:
            event.Skip()

    def OnChar(self, event):
        k = event.GetKeyCode()

        if k == wx.WXK_BACK:
            sel = self.GetSelection()

            if sel[0] < sel[1]:
                self.deleteSelection(sel)
            else:
                pos = self.GetInsertionPoint()
                if pos > 0:
                    del self.chars[pos - 1 : pos]
                    self.Remove(pos - 1, pos)
                    if IsOSX() and wx.VERSION >= (2,6,0,0):
                        self.SetInsertionPoint(pos-1)
        elif k == wx.WXK_RETURN:
            event.Skip()
            return
        elif k == wx.WXK_TAB:
            event.Skip()
            return
        elif k == wx.WXK_DELETE:
            sel = self.GetSelection()
            pos = self.GetInsertionPoint()

            if sel[0] < sel[1]:
                self.deleteSelection(sel)
            else:
                if pos < self.GetLastPosition():
                    del self.chars[pos : pos + 1]
                    self.Remove(pos , pos + 1)
                    if IsOSX() and wx.VERSION >= (2,6,0,0):
                        self.SetInsertionPoint(pos)
        elif k < 127 and k >= 32:
            self.insertChar(k)
                         
        elif k == wx.WXK_LEFT:
            pos = self.GetInsertionPoint()
            if pos > 0:
                self.SetInsertionPoint(pos - 1)
        elif k == wx.WXK_RIGHT:
            pos = self.GetInsertionPoint()
            if pos < self.GetLastPosition():
                self.SetInsertionPoint(pos + 1)
        elif k == ord('V') - 64:
            # Ctl-V
            self.doPaste()
        else:
            event.Skip()
            
    def Remove(self,start,end):
        if IsOSX() and wx.VERSION >= (2,6,0,0):
            # Special handling for wx 2.6, while it's broken
            val = self.GetValue()
            newval = val[:start] + val[end:]
            cursor = self.GetInsertionPoint()
            self.SetValue(newval)
        else:
            wx.TextCtrl.Remove(self,start,end)
        
    def Replace(self,start,end,text):
        if IsOSX() and wx.VERSION >= (2,6,0,0):
            # Special handling for wx 2.6, while it's broken
            val = self.GetValue()
            newval = val[:start] + text + val[end:]
            self.SetValue(newval)
        else:
            wx.TextCtrl.Replace(self,start,end,text)

class PassphraseDialog(wx.Dialog):
    """
    Dialog to retrieve a passphrase from  the user.

    Uses SecureTextCtrl so the returned passphrase is a list of integers.
    """
    
    def __init__(self, parent, message, caption, size = wx.Size(400,400)):
        """
        Create passphrase dialog.

        @param parent: parent widget
        @param message: message to show on the dialog.
        @param caption: string to show in window title.
        """

        wx.Dialog.__init__(self, parent, -1, caption,
                          style = wx.DEFAULT_DIALOG_STYLE,
                          size = size)

        topsizer = wx.BoxSizer(wx.VERTICAL)

        ts = self.CreateTextSizer(message)
        topsizer.Add(ts, 0, wx.ALL, 10)

        self.text = SecureTextCtrl(self, -1, size = wx.Size(300, -1))
        topsizer.Add(self.text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)

        buttons = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        topsizer.Add(buttons, 0, wx.CENTRE | wx.ALL, 10)

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
        wx.EVT_CLOSE(self, self.OnClose)
        
        self.text.SetFocus()
        
        self.SetSizer(topsizer)
        self.SetAutoLayout(1)
        self.Fit()

    def OnClose(self, event):
        self.FlushChars()
        self.EndModal(wx.ID_CANCEL)
        self.Destroy()

    def OnOK(self, event):
        self.EndModal(wx.ID_OK)

    def GetChars(self):
        return self.text.GetChars()

    def FlushChars(self):
        return self.text.FlushChars()

class PassphraseVerifyDialog(wx.Dialog):
    """
    Dialog to retrieve a passphrase from user. It requires the
    user to type the passphrase twice to verify it.

    Uses SecureTextCtrl so the returned passphrase is a list of integers.
    """
    
    def __init__(self, parent, message1, message2, caption,
                 size = wx.Size(400,400)):
        """
        Create passphrase dialog.

        @param parent: parent widget
        @param message1: message to show on the dialog before the first text input field.
        @param message2: message to show on the dialog before the second text input field.
        @param caption: string to show in window title.
        """

        wx.Dialog.__init__(self, parent, -1, caption,
                          size = size,
                          style = wx.DEFAULT_DIALOG_STYLE)

        # Need to create a panel so that tab traversal works properly.
        # Should be fixed in wx 2.5.
        #
        # http://lists.wxwidgets.org/cgi-bin/ezmlm-cgi?11:mss:26416:200403:laipomedjcjdlbblliki
        #
        
        panel = wx.Panel(self, -1, style = wx.TAB_TRAVERSAL)
        topsizer = wx.BoxSizer(wx.VERTICAL)

        txt = wx.StaticText(panel, -1, message1)
        topsizer.Add(txt, 0, wx.ALL, 10)

        self.text1 = SecureTextCtrl(panel, -1, size = wx.Size(300, -1))
        topsizer.Add(self.text1, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)

        txt = wx.StaticText(panel, -1, message2)
        topsizer.Add(txt, 0, wx.ALL, 10)

        self.text2 = SecureTextCtrl(panel, -1, size = wx.Size(300, -1))

        topsizer.Add(self.text2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)

        b = wx.Button(panel, wx.ID_OK, "OK")
        topsizer.Add(b, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
        wx.EVT_CLOSE(self, self.OnClose)
        
        self.text1.SetFocus()
        
        panel.SetSizer(topsizer)
        panel.SetAutoLayout(1)
        panel.Fit()
        self.SetAutoLayout(1)
        self.Fit()

    def OnClose(self, event):
        self.FlushChars()
        self.EndModal(wx.ID_CANCEL)
        self.Destroy()

    def OnOK(self, event):

        # Doublecheck to see if the passphrases match.
        if self.text1.GetChars() != self.text2.GetChars():
            dlg = wx.MessageDialog(self,
                                  "Entered passphrases do not match.",
                                  "Verification error.",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.EndModal(wx.ID_OK)

    def GetChars(self):
        return self.text1.GetChars()

    def FlushChars(self):
        self.text1.FlushChars()
        self.text2.FlushChars()

def PassphraseDialogTest():
    
    wx.PySimpleApp()

    d = PassphraseDialog(None, "Message", "Caption")

    print d.ShowModal()
    chars = d.GetChars()
    d.FlushChars()
    d.Destroy()

    print chars
        
def PassphraseVerifyDialogTest():
    
    wx.PySimpleApp()

    d = PassphraseVerifyDialog(None, "Message", "And again", "Caption")

    print d.ShowModal()
    chars = d.GetChars()
    d.FlushChars()
    d.Destroy()

    print chars
   
# Add URL Base Dialog
class AddURLBaseDialog(wx.Dialog):
       
    def __init__(self, parent, id, name, url, type = 'venue'):
        wx.Dialog.__init__(self, parent, id, "Add %s"%(type))
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.type = type
        self.Centre()
        info = "Specify the URL of the %s to add to your list of %ss."%(self.type,self.type)
        self.text = wx.StaticText(self, -1, info, style=wx.ALIGN_LEFT)
        self.addressText = wx.StaticText(self, -1, "Name: ", style=wx.ALIGN_LEFT)
        self.address = wx.TextCtrl(self, -1, name, size = wx.Size(300,20))
        self.urlText =  wx.StaticText(self, -1, "URL: ", style=wx.ALIGN_LEFT)
        self.url = wx.TextCtrl(self, -1, url, size = wx.Size(300,20))
        self.Layout()
                        
    def Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)

        sizer2 = wx.FlexGridSizer(2,2,10,10)
        sizer2.Add(self.addressText, 0)
        sizer2.Add(self.address, 1, wx.EXPAND)
        sizer2.Add(self.urlText, 0)
        sizer2.Add(self.url, 1, wx.EXPAND)

        sizer1.Add(sizer2, 0, wx.EXPAND | wx.ALL, 20)

        sizer3 =  wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        sizer.Add(sizer1, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(sizer3, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
    def GetName(self):
        return self.address.GetValue()

    def GetUrl(self):
        return self.url.GetValue()

# Edit URL Base Dialog
class EditURLBaseDialog(wx.Dialog):
    ID_DELETE = wx.NewId() 
    ID_RENAME = wx.NewId()
    ID_LIST = wx.NewId()
    listWidth = 500
    listHeight = 200
    currentItem = 0
             
    def __init__(self, parent, id, title, myUrlsDict, type = 'venue'):
        wx.Dialog.__init__(self, parent, id, title)
        self.parent = parent 
        self.dictCopy = myUrlsDict.copy()
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Centre()
        self.type = type
        info = "Please, right click on the %s you want to edit and choose from the \noptions available in the menu."%(self.type)
        self.text = wx.StaticText(self, -1, info, style=wx.ALIGN_LEFT)
        self.myUrlsList= wx.ListCtrl(self, self.ID_LIST, 
                                       size = wx.Size(self.listWidth, self.listHeight), 
                                       style=wx.LC_REPORT)
        self.myUrlsList.InsertColumn(0, "Name")
        self.myUrlsList.SetColumnWidth(0, self.listWidth * 1.0/3.0)
        self.myUrlsList.InsertColumn(1, "Url ")
        self.myUrlsList.SetColumnWidth(1, self.listWidth * 2.0/3.0)
        
        self.menu = wx.Menu()
        self.menu.Append(self.ID_RENAME,"Rename", "Rename selected %s" %self.type)
        self.menu.Append(self.ID_DELETE,"Delete", "Delete selected %s" %self.type)
        self.Layout()
        self.__PopulateList()
        self.__SetEvents()
        
    def __SetEvents(self):
        wx.EVT_RIGHT_DOWN(self.myUrlsList, self.OnRightDown)
        wx.EVT_LIST_ITEM_SELECTED(self.myUrlsList, self.ID_LIST,
                               self.OnItemSelected)
        wx.EVT_MENU(self.menu, self.ID_RENAME, self.OnRename)
        wx.EVT_MENU(self.menu, self.ID_DELETE, self.OnDelete)
               
    def __PopulateList(self):
        i = 0
        self.myUrlsList.DeleteAllItems()
        for name in self.dictCopy.keys():
            self.myUrlsList.InsertStringItem(i, name)
            self.myUrlsList.SetStringItem(i, 1, self.dictCopy[name])
            i = i + 1

    def Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        sizer1.Add(self.myUrlsList, 1, wx.ALL, 10)

        sizer3 =  wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        sizer.Add(sizer1, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(sizer3, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

    def OnDelete(self, event):
        log.debug( "Deleting %s",self.currentItem)
        if(self.dictCopy.has_key(self.currentItem)):
            del self.dictCopy[self.currentItem]
            self.__PopulateList()
            log.debug( " dict copy = %s", self.dictCopy)
        else:
            text = "Please, select the %s you want to delete"%self.type
            title = "Notification"
            MessageDialog(self, text, title, style = wx.OK|wx.ICON_INFORMATION)

    def OnRename(self, event):
        if(self.dictCopy.has_key(self.currentItem)):
            RenameDialog(self, -1, "Rename %s"%self.type, type = self.type)
            
        else:
            text = "Please, select the %s you want to rename"%self.type
            title = "Notification"
            MessageDialog(self, text, title, style = wx.OK|wx.ICON_INFORMATION)

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
        log.debug ("Selected %s", self.currentItem)
              
    def OnRightDown(self, event):
        self.x = event.GetX() + self.myUrlsList.GetPosition().x
        self.y = event.GetY() + self.myUrlsList.GetPosition().y
        self.PopupMenu(self.menu, wx.Point(self.x, self.y))
        event.Skip()
        
    def GetValue(self):
        return self.dictCopy


class RenameDialog(wx.Dialog):

    def __init__(self, parent, id, title, type = 'venue'):
        wx.Dialog.__init__(self, parent, id, title)
        self.type = type
        self.text = wx.StaticText(self, -1, "Please, fill in the new name of your %s"%self.type,
                                 style=wx.ALIGN_LEFT)
        self.nameText = wx.StaticText(self, -1, "New Name: ",
                                     style=wx.ALIGN_LEFT)
        log.debug( 'before creating my urls %s', self.type)
        v = MyUrlsEditValidator(type = self.type)
        self.name = wx.TextCtrl(self, -1, "", size = wx.Size(300,20),
                               validator = v)
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
        self.parent = parent
        
        if(self.ShowModal() == wx.ID_OK):
            parent.Rename(self.name.GetValue())
        self.Destroy()
                       
    def Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
      
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.nameText, 0)
        sizer2.Add(self.name, 1, wx.EXPAND)

        sizer1.Add(sizer2, 0, wx.EXPAND | wx.ALL, 20)

        sizer3 =  wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        sizer.Add(sizer1, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(sizer3, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
    def DoesNameExist(self, name):
        return self.parent.DoesNameExist(name)
        
        
        
class MyUrlsEditValidator(wx.PyValidator):
    def __init__(self, type = 'venue'):
        wx.PyValidator.__init__(self)
        self.type = type

    def Clone(self):
        return MyUrlsEditValidator(self.type)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        nameExists = win.DoesNameExist(val)

        if nameExists:
            info = "A %s with the same name is already added, please select a different name."%self.type
            dlg = wx.MessageDialog(None, info, "Duplicated %s"%self.type, 
                                  style = wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return True
    
    def TransferToWindow(self):
        # Prevent wx.Dialog from complaining.
        return True 

    def TransferFromWindow(self):
        # Prevent wx.Dialog from complaining.
        return True 
        
class TextDialog(wx.Dialog):
    """
    Dialog to retrieve a text string from the user.
    """
    
    def __init__(self, parent, message, caption, size = wx.Size(400,400), text = ""):
        """
        Create passphrase dialog.

        @param parent: parent widget
        @param message: message to show on the dialog.
        @param caption: string to show in window title.
        """

        wx.Dialog.__init__(self, parent, -1, caption,
                          style = wx.DEFAULT_DIALOG_STYLE,
                          size = size)

        topsizer = wx.BoxSizer(wx.VERTICAL)

        ts = self.CreateTextSizer(message)
        topsizer.Add(ts, 0, wx.ALL, 10)

        self.text = wx.TextCtrl(self, -1, value = text, style = wx.TE_RICH2, size = wx.Size(300, -1))
        topsizer.Add(self.text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)

        buttons = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        topsizer.Add(buttons, 0, wx.CENTRE | wx.ALL, 10)

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
        wx.EVT_CLOSE(self, self.OnClose)
        
        self.text.SetFocus()
        
        self.SetSizer(topsizer)
        self.SetAutoLayout(1)
        self.Fit()

    def OnClose(self, event):
        self.FlushChars()
        self.EndModal(wx.ID_CANCEL)
        self.Destroy()

    def OnOK(self, event):
        self.EndModal(wx.ID_OK)

    def GetChars(self):
        return self.text.GetValue()
        
class ProxyAuthDialog(wx.Dialog):
    def __init__(self, parent, ID, title):
        """
        A dialog box to retrieve the username/password for a proxy.
        Unfortunately, the password has to be sent in the clear to the
        proxy, so there is no way we can use any password mangling
        like SecureTxtControl. When the password is saved to the
        preferences, it's automatically encrypted, and only decrypted
        when retrieved, but it's still not ideal. 
        """      
        wx.Dialog.__init__(self, parent, ID, title)

        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()

        self.guideText = wxStaticText(self, -1, "HTTP connection failed. You are using an authenticated proxy server.\nPlease check your settings are correct.")
        self.usernameText = wxStaticText(self, -1, "Username:")
        self.usernameCtrl = wxTextCtrl(self, -1, "")
        self.passwordText = wxStaticText(self, -1, "Password:")
        
        # Intel OS X has issues with the password control, but we aren't
        # granular enough to know if this is an Intel chip or not.
        # This might be fixed in the latest wxPython, but AG won't
        # run with it because of deprecated functionality
        if IsOSX() and wxVERSION <= (2,8,0,0):
            self.passwordCtrl = wxTextCtrl(self, -1, "")
        else:
            self.passwordCtrl = wxTextCtrl(self, -1, "", style=wxTE_PASSWORD)
        
        self.authProxyButton = wxCheckBox(self, wxNewId(), "  Use an authenticated proxy ")
        self.authProxyButton.SetValue(1)

        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.guideText, 0, wxALL|wxEXPAND,10)
        sizer.Add(self.usernameText, 0, wxALL|wxEXPAND,10)
        sizer.Add(self.usernameCtrl, 1, wxALL|wxEXPAND,10)
        sizer.Add(self.passwordText, 0, wxALL|wxEXPAND,10)
        sizer.Add(self.passwordCtrl, 0, wxALL|wxEXPAND,10)
        sizer.Add(self.authProxyButton, 0, wxALL|wxEXPAND, 10)

        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        sizer2.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)
        sizer.Add(sizer2)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

    def GetProxyUsername(self):
        return self.usernameCtrl.GetValue()

    def GetProxyPassword(self):
        return self.passwordCtrl.GetValue()

    def GetProxyEnabled(self):
        if self.authProxyButton.IsChecked():
            return 1
        else:
            return 0

    def SetProxyUsername(self,username):
        self.usernameCtrl.SetValue(username)

    def SetProxyPassword(self,password):
        self.passwordCtrl.SetValue(password)

    def SetProxyEnabled(self, value):
        self.authProxyButton.SetValue(value)
        
def SetIcon(app):
        icon = None
        if IsWindows()or IsLinux() or IsFreeBSD():
            icon = icons.getAGIconIcon()
            app.SetIcon(icon)
        elif IsOSX():
             icon = icons.getAGIcon128Icon()
             t = wx.TaskBarIcon()
             t.SetIcon(icon,"VenueClient")
             
             
dimensions = {  600:  800 , 
                768:  1024,
               1024:  1280, 
               1200:  1920,
               
               # rotated screen sizes
                800:  600,
               1280:  1024,
               1600:  1200,
               1920:  1200 }
def GetScreenWidth(w,h):
    """
    For a given screen width and height, calculate a related nominal width;
    This is used in cases where the width is N screens wide, but the width
    of a single screen is desired; for example, in positioning/sizing
    windows on the screen.
    """
    screenwidth = 0
    if dimensions.has_key(h):
        if dimensions[h] == w:
            # use the given screenwidth
            screenwidth = w
        else:
            # some non-standard screen width; use the standard screenwidth
            screenwidth = dimensions[h]
    else:
        raise ValueError('Unexpected screen dimensions (%d,%d)' % (w,h))
    
    return screenwidth
        



class ItemBrowserCtrl(wx.Panel):
    def __init__(self, parent, id, choices, **kw):
        self.parent = parent
        self.choices = choices
        wx.Panel.__init__(self, parent, id)
        
        self.listCtrl = wx.ListCtrl(self, id, style=wx.LC_REPORT|wx.TAB_TRAVERSAL|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL, size=(500, 599))
        self.listCtrl.InsertColumn(0, 'Name')
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # - search panel
        
        self.searchPanel = wx.Panel(self, -1, size=(100, 100))
        #self.searchPanel.SetBackgroundColour(wx.GREEN)
        self.panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        
        self.searchLabel = wx.StaticText(self.searchPanel, -1, 'Search')
        
        self.searchTextCtrl = wx.TextCtrl(self.searchPanel, -1, size=(150, -1), style=wx.TE_PROCESS_ENTER|wx.TAB_TRAVERSAL)
        
        self.searchResetButton = wx.Button(self, -1, 'Reset')
        
        self.searchPanel.SetSizer(self.panelSizer)
        
        sizer.Add(self.searchPanel, 0, wx.EXPAND)
        self.panelSizer.Add(self.searchLabel, 0, wx.ALL, border=5)
        self.panelSizer.Add(self.searchTextCtrl, 1, wx.ALL|wx.EXPAND, border=5)
        self.panelSizer.Add(self.searchResetButton, 0, wx.ALL, border=5)
        sizer.Add(self.listCtrl, 1, wx.EXPAND)
        

        self.ShowAll()
        
        if self.listCtrl.GetItemCount():
            self.listCtrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
    
        self.Fit()
        self.OnSize()
        
        self.value = -1
        
        
        # - set up event handlers
        wx.EVT_CHAR(self.searchTextCtrl, self.OnChar)
        wx.EVT_CHAR(self.listCtrl, self.OnChar)
        wx.EVT_TEXT(parent, self.searchTextCtrl.GetId(), self.OnSearchText)
        wx.EVT_TEXT_ENTER(parent, self.searchTextCtrl.GetId(), self.OnSearchTextEnter)
        wx.EVT_LIST_ITEM_ACTIVATED(parent,self.listCtrl.GetId(),self.OnListItemActivated)
        wx.EVT_BUTTON(parent, self.searchResetButton.GetId(), self.OnSearchReset)
                
        wx.EVT_SIZE(self, self.OnSize)
        
        self.searchTextCtrl.SetFocus()
        self.ignoreTextChanges= 0
        
    def AppendProfileItem(self, profile,data):

        item = self.listCtrl.InsertStringItem(self.listCtrl.GetItemCount(), profile.name)
        self.listCtrl.SetItemData(item, data)

        if self.listCtrl.GetItemCount() % 2 == 0:
            self.listCtrl.SetItemBackgroundColour(item, wx.Colour(240, 240, 240))
            
        return item   
             
    def OnSearchText(self, event):
        
        if self.ignoreTextChanges:
            return

        searchText = self.searchTextCtrl.GetValue()
        if len(searchText) == 0:
            self.ShowAll()
            return
    
        self.listCtrl.DeleteAllItems()
    
        num = 0
        for profile in self.choices:
            if profile.name.lower().startswith(searchText.lower()):
                retitem = self.AppendProfileItem(profile,num)
            num += 1
    
                
        if self.listCtrl.GetItemCount():
            self.listCtrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            ind = self.listCtrl.GetItemData(0)
            self.ignoreTextChanges = 1
            self.searchTextCtrl.SetValue(self.choices[ind].name)
            self.searchTextCtrl.SetSelection(len(searchText),len(self.choices[ind].name))
            self.ignoreTextChanges = 0


    
    def OnChar(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnSearchReset(event)
            return
        elif event.GetKeyCode() == wx.WXK_TAB:
            if event.GetEventObject() == self.searchTextCtrl:
                self.listCtrl.SetFocus()
            elif event.GetEventObject() == self.listCtrl:
                self.searchTextCtrl.SetFocus()
        elif event.GetKeyCode() == wx.WXK_BACK:
            sel = self.searchTextCtrl.GetSelection()
            if sel[1] - sel[0] > 0:
                self.searchTextCtrl.Remove(sel[0],sel[1])
            else:
                p = self.searchTextCtrl.GetInsertionPoint()
                self.searchTextCtrl.Remove(p-1,p)
                self.OnSearchText(None)
        else:
            event.Skip()
    
    def OnSearchTextEnter(self, event):
        item = -1
        item = self.listCtrl.GetNextItem(item, 
                                     wx.LIST_NEXT_ALL, 
                                     wx.LIST_STATE_SELECTED)
        ind = self.listCtrl.GetItemData(item)
        self.value = self.choices[ind]
        self.parent.EndModal(wx.ID_OK)  
        
    def OnListItemActivated(self, event):  
        ind = self.listCtrl.GetItemData(event.GetItem().GetId())
        self.value = self.choices[ind]
        self.parent.EndModal(wx.ID_OK)  
    
    def GetSelection(self):
        return self.value
    
    def OnSearchReset(self, event):
        self.searchTextCtrl.SetValue('')
    
        self.ShowAll()
    
    def ShowAll(self):
        self.listCtrl.DeleteAllItems()
        
        num=0
        for profile in self.choices:
            self.AppendProfileItem(profile,num)
            num += 1

    
    def OnSize(self, event=None):
        self.listCtrl.SetColumnWidth(0, self.GetSize()[0]-30)
        if event:
            event.Skip()
            
            
            
class ItemBrowserDialog(wx.Dialog):
    def __init__(self,parent,id,title,choices,**kw):
        wx.Dialog.__init__(self,parent,id,title,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,**kw)
        buttonSizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.itemBrowser = ItemBrowserCtrl(self,-1,choices)
        
        self.SetSizer(sizer)
        
        sizer.Add(self.itemBrowser,1,wx.EXPAND)
        sizer.Add(buttonSizer)
        
        
    def GetValue(self):
        return self.itemBrowser.GetSelection()



if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    ProgressDialogTest()
    AboutDialogTest()
    

    # Test for bug report
    b = BugReportCommentDialog(None)
    b.ShowModal()
    b.Destroy()

    # Test for error dialog (includes bug report)
    e = ErrorDialog(None, "test", "Enter Venue Error",
                    style = wx.OK  | wx.ICON_ERROR)
    
    app.MainLoop()
    
