#-----------------------------------------------------------------------------
# Name:        CertificateRequestTool.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: CertificateRequestTool.py,v
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: CertificateRequestTool.py,v 1.28 2007-12-20 18:12:24 turam Exp $"
__docformat__ = "restructuredtext en"

import wx
import wx.wizard

from AccessGrid import Toolkit
from AccessGrid import Platform
from AccessGrid import NetUtilities, Utilities
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.Platform import IsOSX
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from AccessGrid.Security import CertificateRepository, CertificateManager
from AccessGrid.Security.CertificateRepository import RepoDoesNotExist
from AccessGrid.Security.CertificateRepository import RepoInvalidCertificate
from AccessGrid.Security.CRSClient import CRSClient
from AccessGrid.Security.wxgui.HTTPProxyConfigPanel import HTTPProxyConfigPanel
from AccessGrid.ServiceProfile import ServiceProfile

import string
import time
import os
import os.path

from AccessGrid import Log
log = Log.GetLogger(Log.CertificateRequestTool)

#
# Service type names and descriptions
#

ServiceTypes = [("Venue Server", "VenueServer"),
                ("Other", None),
                ]
                 

class CertificateRequestTool(wx.wizard.Wizard):
    '''
    This wizard guides users through the steps necessary for
    requesting either an identity, host, or service certificate. 
    '''
    def __init__(self, parent, certificateType = None, requestId = None):
        
        '''
        Creates all ui components.
        If certificateType is set to None all wizard pages will appear.
        If you know you want to request one specific type of certificate,
        set certificateType to IDENTITY, HOST, or SERVICE and only relevant
        pages for that certificate type will be shown when running the wizard.

        If you want to get and install a certificate already requested,
        run this wizard with the retreived requestId.
        '''

        wizardId =  wx.NewId()
        wx.wizard.Wizard.__init__(self, parent, wizardId,"", wx.NullBitmap)
        global log
        self.log = log

        self.log.debug("__init__:Start Certificate Request Wizard")
        
        self.step = 1
        self.maxStep = 4
        self.SetPageSize(wx.Size(500, 450))

        self.page0 = IntroWindow(self, "Welcome to the Certificate Request Wizard", )
        self.page1 = SelectCertWindow(self, "Select Certificate Type")
        self.idpage = self.page2 = IdentityCertWindow(self, "Enter Your Information")
        self.servicepage = self.page3 = ServiceCertWindow(self, "Enter Service Information")
        self.anonpage = self.page4a = AnonCertWindow(self, "Anonymous Certificate")
        self.submitpage = self.page5 = SubmitReqWindow(self, "Submit Request")
        self.FitToPage(self.page1)

        self.log.debug("__init__:Set the initial order of the pages")
        
        self.page0.SetNext(self.page1)
        self.page1.SetNext(self.page3)
        self.page2.SetNext(self.page5)
        self.page3.SetNext(self.page5)
        #self.page4.SetNext(self.page5)
        self.page4a.SetNext(self.page5)

        self.page1.SetPrev(self.page0)
        self.page2.SetPrev(self.page1)
        self.page3.SetPrev(self.page1)
        #self.page4.SetPrev(self.page1)
        self.page4a.SetPrev(self.page1)
        #self.page5.SetPrev(self.page4)
      
        self.log.debug("__init__:Handle arguments for certificate type")
        
        if certificateType:
            self.maxStep = 3
            if certificateType == "IDENTITY":
                self.page0.SetNext(self.page2)
                self.page2.SetPrev(self.page0)
                self.SetTitle("Request Certificate - Step 1 of %s"
                              %self.maxStep)
                        
            elif certificateType == "SERVICE":
                self.page0.SetNext(self.page3)
                self.page3.SetPrev(self.page0)
                self.SetTitle("Request Certificate - Step 1 of %s"
                              %self.maxStep)
                    
            elif certificateType == "ANONYMOUS":
                self.page0.SetNext(self.page4a)
                self.page4a.SetPrev(self.page0)
                self.SetTitle("Request Certificate - Step 1 of %s"
                              %self.maxStep)
            else:
                self.log.info("__init__:Handle arguments for certificate type")
                raise Exception("Flag should be either IDENTITY, SERVICE or ANONYMOUS")

        self.log.debug("__init__:Create the pages")

        wx.wizard.EVT_WIZARD_PAGE_CHANGING(self, wizardId, self.ChangingPage)
        wx.wizard.EVT_WIZARD_CANCEL(self, wizardId, self.CancelPage) 
        
        self.log.debug("__init__:Run the wizard")
        
        self.RunWizard(self.page0)

    def CancelPage(self, event):
        self.log.debug(" CancelPage:Cancel wizard")
        
        #dlg = wx.MessageDialog(self,"Your certificate request is not complete. If you quit now, the request will not be submitted. \nCancel request?.", "", style = wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        #if(dlg.ShowModal() == wx.ID_NO):
        #    event.Veto()
            
        #dlg.Destroy()
                     
    def ChangingPage(self, event):
        '''
        Makes sure right values are entered in following page
        '''
        dir = event.GetDirection()
        page = event.GetPage()
        forward = 1
        backward = 0
        
        if dir == forward:
            self.log.debug("ChangingPage: From %s to %s"
                           %(page.__class__, page.GetNext().__class__))

            if not page.GetValidity():
                self.log.debug("ChangingPage:Values are not correct, do not change page")
                event.Veto()
            else:
                self.log.debug("ChangingPage:Values are correct")

                self.step = self.step+1
                self.SetTitle("Request Certificate - Step %i of %i"
                              %(self.step, self.maxStep))

                next = page.GetNext()

                password = ""

                if next and isinstance(next, SubmitReqWindow):

                    if isinstance(page, IdentityCertWindow):
                        name = page.firstNameCtrl.GetValue() +" "+page.lastNameCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        domain = page.domainCtrl.GetValue()

                        password = page.passwordCtrl.GetValue()
                        #
                        # If you don't do the following, password is actually
                        # a unicode string, not a string, and openssl will
                        # bitterly complain.
                        #
                        password = str(password)
                        certInfo = CertificateManager.IdentityCertificateRequestInfo(name, domain, email)
                        
                    elif  isinstance(page, ServiceCertWindow):
                        name = page.serviceCtrl.GetValue()
                        host = page.hostCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        certInfo = CertificateManager.ServiceCertificateRequestInfo(name, host, email)

                    elif isinstance(page, AnonCertWindow):
                        certInfo = CertificateManager.AnonymousCertificateRequestInfo()
                        
                    next.SetText(certInfo, password)
                    next.SetPrev(page)
                if next:
                    next.OnPageShow()
                
        elif dir == backward:
            self.log.debug("ChangingPage: Go back from %s to %s"
                           %(page.__class__, page.GetPrev().__class__))
            self.step = self.step-1
            self.SetTitle("Request Certificate - Step %i of %i"
                          %(self.step, self.maxStep))
       

class TitledPage(wx.wizard.PyWizardPage):
    '''
    Base class for all wizard pages.  Creates a title.
    '''
    def __init__(self, parent, title):
    
        wx.wizard.PyWizardPage.__init__(self, parent)
        self.title = title
        self.next = None
        self.prev = None
        self.MakePageTitle()

    def MakePageTitle(self):
        '''
        Create page title
        '''
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        title = wx.StaticText(self, -1, self.title, style = wx.ALIGN_CENTER)
        title.SetLabel(self.title)
        title.SetFont(wx.Font(14, wx.NORMAL, wx.NORMAL, wx.BOLD))
        self.sizer.Add(title, 0, wx.ALL|wx.EXPAND, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Add(wx.Size(10, 10))
                       
    def OnPageShow(self):
        """
        Called when page is about to be shown.
        """

        pass
        

    def SetNext(self, next):
        '''
        Set following page that will show up when user clicks on next button.
        '''
        self.next = next

    def SetPrev(self, prev):
        '''
        Set previous page that will show up when user clicks on back button.
        '''
        self.prev = prev  

    def GetNext(self):
        '''
        Get the following page.
        '''
        return self.next
    
    def GetPrev(self):
        '''
        Get the previous page.
        '''
        return self.prev
         

class IntroWindow(TitledPage):
    '''
    Contains an introduction to certificates.
    '''
    def __init__(self, parent, title):
       
        TitledPage.__init__(self, parent, title)
        self.info = wx.StaticText(self, -1, "This wizard will help you request a certificate.\n\nCertificates are used to identify everyone connected to the AccessGrid. \nIt is your electronic identity card verifying that you are who you say you are. \n\nClick 'Next' to continue.")
        self.Layout()

    def GetValidity(self):
        return True
  
    def Layout(self):
        self.sizer.Add(self.info, 0, wx.ALL, 5)

                      
class SelectCertWindow(TitledPage):
    def __init__(self, parent, title):
        '''
        Includes information about certificates and an option to request a
        host, identity, or service certificate.
        '''
        TitledPage.__init__(self, parent, title)
        self.text = wx.StaticText(self, -1, "Select Certificate Type: ")
        self.selectionList = ["Service", "Anonymous", "Identity"]
        self.selections = wx.ComboBox(self, -1, self.selectionList[0],
                                     choices = self.selectionList,
                                     style = wx.CB_READONLY)
        self.selections.SetValue(self.selectionList[0])
        self.info = wx.StaticText(self, -1, "There are three kinds of certificates:")
        self.info1 = wx.StaticText(self, -1, "Identity Certificate:")
        self.info2 = wx.StaticText(self, -1, "To identify an individual.")
        self.info3 = wx.StaticText(self, -1, "Service Certificate:")
        self.info4 = wx.StaticText(self, -1, "To identify a service.")
        self.info5 = wx.StaticText(self, -1, "Anonymous Certificate:")
        self.info6 = wx.StaticText(self, -1, "Allows access but not per-user identification.")
        self.parent = parent
        self.__setProperties()
        self.__Layout()

    def GetValidity(self):
        return True

    def GetNext(self):
        """
        Next page depends on what type of certificate the user selects
        Note: Overrides super class method
        """
        next = self.next
        value = self.selections.GetValue()

        if value == self.selectionList[0]:
            next = self.parent.page3
            self.parent.page3.SetPrev(self)

        elif value == self.selectionList[1]:
            next = self.parent.page4a
            self.parent.page4a.SetPrev(self)
        elif value == self.selectionList[2]:
            next = self.parent.page2
            self.parent.page2.SetPrev(self)
            
        return next

    def __setProperties(self):
        # Fix for OS X where wx.DEFAULT isn't sane
        pointSize = wx.DEFAULT
        
        if Platform.IsOSX():
            pointSize=12
        
        self.info1.SetFont(wx.Font(pointSize, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.info3.SetFont(wx.Font(pointSize, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.info5.SetFont(wx.Font(pointSize, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        
    def __Layout(self):
        '''
        Handles UI layout
        '''
        self.sizer.Add(self.info, 0, wx.ALL, 5)
        self.sizer.Add(wx.Size(10, 10))
        
        infoSizer = wx.FlexGridSizer(3, 2, 6, 6)
        infoSizer.Add(self.info1, 0, wx.CENTER)
        infoSizer.Add(self.info2, 0, wx.EXPAND | wx.ALIGN_LEFT)
        infoSizer.Add(self.info3, 0, wx.CENTER)
        infoSizer.Add(self.info4, 0, wx.EXPAND | wx.ALIGN_LEFT)
        infoSizer.Add(self.info5, 0, wx.CENTER)
        infoSizer.Add(self.info6, 0, wx.EXPAND | wx.ALIGN_LEFT)    
        self.sizer.Add(infoSizer, 0, wx.ALL| wx.EXPAND, 5)
        self.sizer.Add(wx.Size(10, 10))
        
        gridSizer = wx.FlexGridSizer(1, 2, 6,6)
        gridSizer.Add(self.text, 0, wx.ALIGN_CENTER)
        gridSizer.Add(self.selections, 0, wx.EXPAND)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add(gridSizer, 0, wx.ALL| wx.EXPAND, 5)
        self.Layout()

class IdentityCertWindow(TitledPage):
    '''
    Includes controls to request an identity certificate.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.text = wx.StaticText(self, -1,
"""The name fields should contain your first and last name; requests with 
incomplete names may be rejected. The e-mail address will be used for 
verification; please make sure it is valid.

The domain represents the institution you belong to; it will default to the 
hostname part of your email address.  The domain will be used for verification; 
please make sure it is valid.

The passphrase will be used to access your generated certificate after it is 
created.  You will need to remember it: it is not possible to determine the 
passphrase from the certificate, and it cannot be reset.""")

        self.firstNameId = wx.NewId()
        self.lastNameId = wx.NewId()
        self.emailId = wx.NewId()
        self.domainId = wx.NewId()
        self.passwrdId = wx.NewId()
        self.passwrd2Id = wx.NewId()
                
        self.firstNameText = wx.StaticText(self, -1, "First name:")
        self.lastNameText = wx.StaticText(self, -1, "Last name:")
        self.emailText = wx.StaticText(self, -1, "E-mail:")
        self.domainText = wx.StaticText(self, -1, "Domain:")
        self.passwordText = wx.StaticText(self, -1, "Passphrase:")
        self.passwordVerText = wx.StaticText(self, -1, "Retype passphrase:")
        self.firstNameCtrl = wx.TextCtrl(self, self.firstNameId)
        self.lastNameCtrl = wx.TextCtrl(self, self.lastNameId)
        self.emailCtrl = wx.TextCtrl(self, self.emailId)
        self.domainCtrl = wx.TextCtrl(self, self.domainId)
        self.passwordCtrl = wx.TextCtrl(self, self.passwrdId,
                                       style = wx.TE_PASSWORD)
        self.passwordVerCtrl = wx.TextCtrl(self, self.passwrd2Id,
                                          style = wx.TE_PASSWORD)
        self.SetValidator(IdentityCertValidator())

        wx.EVT_TEXT(self, self.firstNameId, self.EnterText)
        wx.EVT_TEXT(self, self.lastNameId, self.EnterText)
        wx.EVT_TEXT(self.emailCtrl, self.emailId, self.EnterEmailText)
        wx.EVT_TEXT(self.domainCtrl, self.domainId, self.EnterDomainText)
        wx.EVT_TEXT(self.passwordCtrl, self.passwrdId , self.EnterText)
        wx.EVT_TEXT(self.passwordVerCtrl, self.passwrd2Id, self.EnterText)
        wx.EVT_CHAR(self.domainCtrl, self.EnterDomainChar)
        self.__Layout()

        #
        # State to set if the user entered anything in the domain
        # textbox. If so, don't change it on them.
        #
        self.userEnteredDomain = 0
   
    def GetValidity(self):
        return self.GetValidator().Validate(self)

    def EnterDomainChar(self, event):
        self.userEnteredDomain = 1
        event.Skip()
        
    def EnterDomainText(self, event):
        self.EnterText(event)
        
    def EnterEmailText(self, event):
        self.EnterText(event)

        #
        # See if the user has entered a domain yet. If not,
        # initialize to the part of the email address after the @.
        #

        if self.userEnteredDomain:
            return

        email = self.emailCtrl.GetValue()

        at = email.find("@")
        if at < 0:
            return

        domainStr = email[at+1:]

        if domainStr != "":
            self.domainCtrl.SetValue(domainStr)
        
    def EnterText(self, event):
        '''
        Sets background color of the item that triggered the event to white.
        '''        
        item = event.GetEventObject()
        item.SetBackgroundColour((254, 254, 254))
        item.Refresh()

    def __Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 0, wx.ALL, 5)
        #self.sizer.Add(wx.Size(10, 10))
        gridSizer = wx.FlexGridSizer(0, 2, 6, 6)
        #gridSizer.Add(self.nameText)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.firstNameText)
        gridSizer.Add(box)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.firstNameCtrl, 1, wx.RIGHT, 10)
        box.Add(self.lastNameText, 0,wx.RIGHT, 5)
        box.Add(self.lastNameCtrl, 1, wx.EXPAND)
        gridSizer.Add(box, 1, wx.EXPAND)
        
        #gridSizer.Add(self.nameCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.emailText)
        gridSizer.Add(self.emailCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.domainText)
        gridSizer.Add(self.domainCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.passwordText)
        gridSizer.Add(self.passwordCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.passwordVerText)
        gridSizer.Add(self.passwordVerCtrl, 0, wx.EXPAND)
        gridSizer.AddGrowableCol(1)

        self.sizer.Add(gridSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Fit(self)
        self.Layout()

class ValidatorHelp(wx.PyValidator):
    '''
    This class encapsulates methods that more than one validator will use.
    '''
    def __init__(self):
       
        wx.PyValidator.__init__(self)
        self.colour = "RED"
             
    def SetColour(self, ctrl):
        '''
        Sets the colour of the control to red.
        '''
        ctrl.SetBackgroundColour(self.colour)
        ctrl.SetFocus()
        ctrl.Refresh()
            
    def CheckEmail(self, host, email):
        '''
        Checks if e-mail address and host is on same domain.
        '''
        name, domain = email.split('@')

        # Remove blank spaces in the end
        domainList = domain.split(' ')
        hostList = host.split(' ')

        # No blank spacec in front of domain
        domain = domainList[0]

        # Ignore blank spacec in front of host
        index = 0
        for item in hostList:
            if hostList[index] != '':
                host = hostList[index]
                break
            index = index + 1
            
        # Get all subsets of the domain name
        domainParts = domain.split('.')
        domainPartsList = []
        index = 0
        
        for part in domainParts:
            index = index + 1
            followingList = domainParts[index:]
            for s in followingList:
                part = part+'.'+s

            domainPartsList.append(part)

        if domain == "":
            return False

        hostlow = host.lower()
        # Check if some part of the domain matches the host name
        for part in domainPartsList:
           if hostlow.find(part.lower()) != -1:
               return True

        return False

    def CheckHost(self, host):
        '''
        Checks to see if host is a valid machine name and not
        an IP address.
        '''
        for char in host:
            return char in string.letters
              
        return False

    
class IdentityCertValidator(wx.PyValidator):
    '''
    Validator used to ensure correctness of parameters entered in
    IdentityCertWindow.
    '''
    def __init__(self):
        wx.PyValidator.__init__(self)
        self.helpClass = ValidatorHelp()
        
    def Clone(self):
        '''
        Returns a new IdentityCertValidator.
        Note: Overrides super class method.
        '''
        return IdentityCertValidator()

    def Validate(self, win):
        '''
        Checks if win has correct parameters.
        '''
        # Are we going back or forward?
        
        firstName = win.firstNameCtrl.GetValue()
        lastName = win.lastNameCtrl.GetValue()
        email = win.emailCtrl.GetValue()
        domain = win.domainCtrl.GetValue()
        password = win.passwordCtrl.GetValue()
        password2 = win.passwordVerCtrl.GetValue()
               
        if firstName == "":
            MessageDialog(None, "Please enter your first name.",
                          style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.firstNameCtrl)
            return False

        elif lastName == "":
            MessageDialog(None, "Please enter your last name.",
                          style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.lastNameCtrl)
            return False
        
        elif email == "":
            MessageDialog(None, "Please enter your e-mail address.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False

        elif email.find("@") == -1:
            MessageDialog(None, "Pleas enter a valid e-mail address, for example name@example.com.",
                          style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False
        
        elif password == "":
            MessageDialog(None, "Please enter your passphrase.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.passwordCtrl)
            return False
            
        elif password != password2:
            MessageDialog(None, "Your passphrase entries do not match. Please retype them.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.passwordCtrl)
            self.helpClass.SetColour(win.passwordVerCtrl)
            return False

        elif domain == "":
            MessageDialog(None, "Please enter the domain name of your home site; for example, example.com..", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.domainCtrl)
            return False
            

        return True

    def TransferToWindow(self):
        return True # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return True # Prevent wx.Dialog from complaining.

  
class AnonCertWindow(TitledPage):
    '''
    Includes information for requesting a host certificate.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.text1 = wx.StaticText(self, -1,
                                 "An anonymous certificate carries no identification information.")
        self.text2 = wx.StaticText(self, -1,
                                 "You may not be able to use this certificate to gain entry to some venues.")
        self.Layout()

    def GetValidity(self):
        return True

    def Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text1, 0, wx.ALL, 5)
        self.sizer.Add(self.text2, 0, wx.ALL, 5)

class HostCertWindow(TitledPage):
    '''
    Includes information for requesting a host certificate.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.emailId = wx.NewId()
        self.hostId = wx.NewId()
        self.text = wx.StaticText(self, -1, "The e-mail address will be used for verification, please make sure it is valid.")
        self.emailText = wx.StaticText(self, -1, "E-mail:")
        self.hostText = wx.StaticText(self, -1, "Machine Name:")
        self.emailCtrl = wx.TextCtrl(self, self.emailId, validator = HostCertValidator())

        self.hostName = SystemConfig.instance().GetHostname();
        
        self.hostCtrl = wx.TextCtrl(self, self.hostId, self.hostName, validator = HostCertValidator())
        self.SetEvents()
        self.Layout()

    def SetEvents(self):
        '''
        Sets events
        '''
        wx.EVT_TEXT(self.emailCtrl, self.emailId, self.EnterText)
        wx.EVT_TEXT(self.hostCtrl , self.hostId , self.EnterText)
            
    def EnterText(self, event):
        '''
        Sets background color of the item that triggered the event to white.
        '''    
        item = event.GetEventObject()
        item.SetBackgroundColour((254, 254, 254))
        item.Refresh()
        
    def Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 0, wx.ALL, 5)
        self.sizer.Add(wx.Size(10, 10))
        gridSizer = wx.FlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.hostText)
        gridSizer.Add(self.hostCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.emailText)
        gridSizer.Add(self.emailCtrl, 0, wx.EXPAND)
        gridSizer.AddGrowableCol(1)

        self.sizer.Add(gridSizer, 0, wx.ALL | wx.EXPAND, 5)

        
class HostCertValidator(wx.PyValidator):
    '''
    Includes controls to request a host certificate.
    '''
    def __init__(self):
       
        wx.PyValidator.__init__(self)
        self.helpClass = ValidatorHelp()
            
    def Clone(self):
        '''
        Returns a new HostCertValidator.
        Note: Overrides super class method.
        '''
        return HostCertValidator()

    def Validate(self, win):
        '''
        Checks if win has correct parameters.
        '''
        tc = self.GetWindow()
        hostName = win.hostCtrl.GetValue()
        email = win.emailCtrl.GetValue()
              
        if hostName == "":
            MessageDialog(None, "Please enter the machine name (mcs.anl.gov).", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return False
        
        elif hostName.find('.') == -1:
            MessageDialog(None, "Please enter complete machine name (machine.mcs.anl.gov).", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return False

        elif not self.helpClass.CheckHost(hostName):
            MessageDialog(None, "Please enter valid machine name (machine.mcs.anl.gov). \nIP address is not a valid machine name.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return False
            
        elif email == "":
            MessageDialog(None, "Please enter your e-mail address.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False

        elif email.find("@") == -1:
            MessageDialog(None, "Pleas enter a valid e-mail address, for example name@mcs.anl.gov.",
                          style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False

        elif not self.helpClass.CheckEmail(hostName, email):
            MessageDialog(None, "The e-mail address and machine name should be on same domain. \n\nFor machine name: video.mcs.anl.gov  \n\nValid e-mail addresses could be: \n\nname@mcs.anl.gov or name@anl.gov \n",
                          style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False
        
        return True

    def TransferToWindow(self):
        return True # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return True # Prevent wx.Dialog from complaining.

        
class ServiceCertWindow(TitledPage):
    '''
    Includes information for requesting a service certificate.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.serviceId = wx.NewId()
        self.hostId = wx.NewId()
        self.emailId = wx.NewId()
            
        self.text = wx.StaticText(self, -1, "The e-mail address will be used for verification, please make sure it is valid.")
        self.serviceText = wx.StaticText(self, -1, "Service Type:")
        self.serviceDropdown = wx.ComboBox(self, -1, "",
                                          style = wx.CB_DROPDOWN | wx.CB_READONLY,
                                          choices = map(lambda x: x[0], ServiceTypes))
        self.hostText = wx.StaticText(self, -1, "Machine Name:")
        self.emailText = wx.StaticText(self, -1, "E-mail:")
        self.serviceCtrl = wx.TextCtrl(self, self.serviceId)
        self.serviceNameText = wx.StaticText(self, -1, "Service Name:")
        self.serviceCtrl.Enable(0)
        self.serviceNameText.Enable(0)

        self.serviceName = None
        self.userTyped = 0
        
        self.hostName = SystemConfig.instance().GetHostname();

        self.hostCtrl = wx.TextCtrl(self, self.hostId, self.hostName)
        self.emailCtrl = wx.TextCtrl(self, self.emailId)


        self.SetValidator(ServiceCertValidator())

        wx.EVT_COMBOBOX(self.serviceDropdown, self.serviceDropdown.GetId(),
                     self.OnServiceSelected)

        wx.EVT_TEXT(self.serviceCtrl, self.serviceId, self.OnServiceText)
        wx.EVT_TEXT(self.emailCtrl, self.emailId, self.EnterText)
        wx.EVT_TEXT(self.hostCtrl, self.hostId , self.EnterText)
        wx.EVT_CHAR(self.serviceCtrl, self.OnServiceChar)
        self.Layout()

    def GetValidity(self):
        return self.GetValidator().Validate(self)

    def OnServiceChar(self, event):
        self.userTyped = 1
        event.Skip()
        
    def OnServiceSelected(self, event):

        try:
            which = ServiceTypes[event.GetSelection()]

            self.serviceName = which[1]

            if which[0] == "Other":
                self.serviceCtrl.Enable(1)
                self.serviceNameText.Enable(1)
                if not self.userTyped:
                    self.serviceCtrl.SetValue("")
            else:
                self.serviceCtrl.Enable(0)
                self.serviceNameText.Enable(0)
                if not self.userTyped:
                    self.serviceCtrl.SetValue(self.serviceName)
        except:
            log.exception("hm, OnServiceSelected fails.")

    def OnServiceText(self, event):
        self.EnterText(event)
        self.serviceName = self.serviceCtrl.GetValue()

    def EnterText(self, event):
        '''
        Sets background color of the item that triggered the event to white.
        '''   
        item = event.GetEventObject()
        item.SetBackgroundColour((254, 254, 254))
        item.Refresh()
                   
    def Layout(self):
        '''
        Handles UI layout
        '''
        self.sizer.Add(self.text, 0, wx.ALL, 5)
        self.sizer.Add(wx.Size(10, 10))
        gridSizer = wx.FlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.serviceText, 0, wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.serviceDropdown, 0, wx.EXPAND)
        gridSizer.Add(self.serviceNameText, 0, wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.serviceCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.hostText, 0, wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.hostCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.emailText, 0, wx.ALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.emailCtrl, 0, wx.EXPAND)
        gridSizer.AddGrowableCol(1)

        self.sizer.Add(gridSizer, 0, wx.ALL | wx.EXPAND, 5)


class ServiceCertValidator(wx.PyValidator):
    '''
    Validator used to ensure correctness of parameters entered in
    ServiceCertWindow.
    '''
    def __init__(self):
        wx.PyValidator.__init__(self)
        self.helpClass = ValidatorHelp()
            
    def Clone(self):
        '''
        Returns a new ServiceCertValidator.
        Note: Overrides super class method.
        '''
        return ServiceCertValidator()

    def Validate(self, win):
        '''
        Checks if win has correct parameters.
        '''
        serviceType = win.serviceDropdown.GetValue()
        name = win.serviceCtrl.GetValue()
        email = win.emailCtrl.GetValue()
        host = win.hostCtrl.GetValue()
          
          
        if serviceType == "":
            MessageDialog(None, "Please select a service type.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.serviceDropdown)
            return False
            
        elif serviceType == "Other" and name == "":
            MessageDialog(None, "Please enter service name.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.serviceCtrl)
            return False
             
        elif host == "":
            MessageDialog(None, "Please enter machine name (machine.mcs.anl.gov).", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return False

        elif host.find('.') == -1:
            MessageDialog(None, "Please enter complete machine name (machine.mcs.anl.gov).", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return False
            
        elif not self.helpClass.CheckHost(host):
            MessageDialog(None, "Please enter valid machine name (machine.mcs.anl.gov). \nIP address is not a valid machine name.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return False

        elif email == "":
            MessageDialog(None, "Please enter e-mail address.", style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False

        elif email.find("@") == -1:
            MessageDialog(None, "Pleas enter a valid e-mail address, for example name@mcs.anl.gov.",
                          style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False
        
        elif not self.helpClass.CheckEmail(host, email):
            MessageDialog(None, "The e-mail address and machine name should be on same domain. \n\nFor machine name: video.mcs.anl.gov  \n\nValid e-mail addresses could be: \n\nname@mcs.anl.gov or name@anl.gov \n",
                          style = wx.OK | wx.ICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return False
            
        return True

    def TransferToWindow(self):
        return True # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return True # Prevent wx.Dialog from complaining.


class SubmitReqWindow(TitledPage):
    '''
    Shows the user what information will be submitted in the certificate
    request.
        '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.info = ""
        self.parent = parent
        self.text = wx.TextCtrl(self, -1, self.info, size = wx.Size(10,80),
                               style = wx.NO_BORDER | wx.NO_3D | wx.TE_MULTILINE |
                               wx.TE_RICH2 | wx.TE_READONLY)
        self.text.SetBackgroundColour(self.GetBackgroundColour())

        self.proxyPanel = HTTPProxyConfigPanel(self)
        self.ExportProfileButton = wx.Button(self, -1, "Export service profile...")
        wx.EVT_BUTTON(self, self.ExportProfileButton.GetId(),
                   self.ExportServiceProfile)
        self.__Layout()

    def SetText(self, certInfo, password):
        '''
        Sets the text based on previous page
        '''
        # Parameters for requesting a certificate
        self.certInfo = certInfo
        self.password = password

        reqType = certInfo.GetType()
        reqName = certInfo.GetName()
        reqEmail = certInfo.GetEmail()
        
        # Fix for dorky OS X wx.DEFAULT insanity
        pointSize=wx.DEFAULT
        if IsOSX():
            pointSize=12
        
        if reqType == "anonymous":

            self.info = """Click 'Finish' to submit the anonymous certificate request to the certificate server at Argonne. The certificate should be available immediately. 

Please contact agdev-ca@mcs.anl.gov if you have questions."""

            self.text.SetValue(self.info)

        else:

            self.info =  """Click 'Finish' to submit %s certificate request for %s to Argonne.  A confirmation e-mail will be sent, within 2 business days, to %s.

Please contact agdev-ca@mcs.anl.gov if you have questions.""" %(reqType, reqName, reqEmail)

            self.text.SetValue(self.info)

            requestStart = 25
            nameStart = 50 + len(reqType)
            emailStart = 127 + len(reqType) + len(reqName)

            self.text.SetInsertionPoint(0)
            f = wx.Font(pointSize, wx.NORMAL, wx.NORMAL, wx.BOLD)
            textAttr = wx.TextAttr(wx.NullColour)
            textAttr.SetFont(f)
            self.text.SetStyle(nameStart, nameStart+len(reqName), textAttr)
            self.text.SetInsertionPoint(0)

            f = wx.Font(pointSize, wx.NORMAL, wx.NORMAL, wx.BOLD)
            textAttr = wx.TextAttr(wx.NullColour)
            textAttr.SetFont(f)
            self.text.SetStyle(emailStart, emailStart+len(reqEmail), textAttr)
            self.text.SetInsertionPoint(0)

            f = wx.Font(pointSize, wx.NORMAL, wx.NORMAL, wx.BOLD)
            textAttr = wx.TextAttr(wx.NullColour)
            textAttr.SetFont(f)
            self.text.SetStyle(requestStart, requestStart+len(reqType), textAttr)

        self.text.Refresh()
        
    def GetValidity(self):
        #
        # Go ahead and try to create the certificate request.
        #
        # We will invoke self.identityCertCreate() callback that
        # was passed to the constructor of the wizard.
        #
        wx.BeginBusyCursor()
        self.Refresh()
        self.Update()

        success = False

        try:
            proxyInfo = self.proxyPanel.GetInfo()
            certMgr = Toolkit.Application.instance().GetCertificateManager()
            gui = Toolkit.Application.instance().GetCertificateManagerUI()

            #
            # Sigh, continue to hardcode URLs. Next turn of the crank
            # we'll hopefully get these out of here.
            #

            crsURL = None
            if self.certInfo.GetType() == "anonymous":
                crsURL = "http://www.mcs.anl.gov/research/projects/accessgrid/ca/anonymous/anonReqServer.cgi"
            success = gui.RequestCertificate(self.certInfo,
                                             self.password,
                                             proxyInfo[0],
                                             proxyInfo[1],
                                             proxyInfo[2],
                                             crsURL)
        finally:
            wx.EndBusyCursor()
            self.Refresh()
            self.Update()

        return success

    def __Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 1, wx.ALL|wx.EXPAND, 5)

        hs = wx.BoxSizer(wx.VERTICAL);
        hs.Add(self.proxyPanel, 1, wx.EXPAND | wx.ALL, 3)

        box = wx.StaticBox(self, -1, "Service profile")
        boxs = wx.StaticBoxSizer(box, wx.VERTICAL);
        boxs.Add(self.ExportProfileButton, 0, wx.EXPAND|wx.CENTER)

        hs.Add(boxs, 0, wx.EXPAND | wx.ALL, 3)
        self.sizer.Add(hs, 0, wx.EXPAND | wx.ALIGN_BOTTOM)
        #self.SetSizer(self.sizer)
        #self.Layout()

    def ExportServiceProfile(self, event):

        dn = "/" + "/".join(map(lambda a: "=".join(a), self.certInfo.GetDN()))
        profile = ServiceProfile(self.certInfo.GetName(),
                                 authType = "x509",
                                 subject = dn)

        dir = Platform.Config.UserConfig.instance().GetServicesDir()
        file = "%s.profile" % (self.certInfo.GetName())

        dlg = wx.FileDialog(self, "Export service profile",
                           dir, file,
                           "Service profiles|*.profile|All files|*.*",
                           wx.SAVE | wx.OVERWRITE_PROMPT)
        rc = dlg.ShowModal()
        if rc == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            try:
                profile.Export(path)
            except:
                log.exception("Failure exporting profile to %s", path)
                ErrorDialog(self, "Cannot export service profile",
                            "Cannot export service profile")

        else:
            dlg.Destroy()
               
    def OnPageShow(self):
        if self.certInfo.GetType() == "service":
            self.ExportProfileButton.Enable(1)
        else:
            self.ExportProfileButton.Enable(0)
                        
if __name__ == "__main__":
    pp = wx.PySimpleApp()

    from AccessGrid import Toolkit
    app = Toolkit.WXGUIApplication()
    app.Initialize()

    # Show certificate request wizard
    certReq = CertificateRequestTool(None)
#    certReq = CertificateRequestTool(None, certificateType = "SERVICE")
    certReq.Destroy()
