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

__revision__ = "$Id: CertificateRequestTool.py,v 1.24 2003-10-15 20:37:14 eolson Exp $"
__docformat__ = "restructuredtext en"

from wxPython.wx import *
from wxPython.wizard import *
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from AccessGrid import CertificateRepository
from AccessGrid import Toolkit
from AccessGrid.CertificateRepository import RepoDoesNotExist, RepoInvalidCertificate
from AccessGrid.CRSClient import CRSClient
from AccessGrid import Platform
from AccessGrid import NetUtilities

import string
import time
import md5
import os
import os.path

import logging, logging.handlers
log = logging.getLogger("AG.CertificateRequestTool")

class CertificateRequestTool(wxWizard):
    '''
    This wizard guides users through the steps necessary for
    requesting either an identity, host, or service certificate. 
    '''
    def __init__(self, parent, certificateType = None, requestId = None,
                 createIdentityCertCB = None):
        '''
        Creates all ui components.
        If certificateType is set to None all wizard pages will appear.
        If you know you want to request one specific type of certificate,
        set certificateType to IDENTITY, HOST, or SERVICE and only relevant
        pages for that certificate type will be shown when running the wizard.

        If you want to get and install a certificate already requested,
        run this wizard with the retreived requestId.
        '''

        wizardId =  wxNewId()
        wxWizard.__init__(self, parent, wizardId,"", wxNullBitmap)
        self.log = self.GetLog()

        self.createIdentityCertCB = createIdentityCertCB
        
        self.log.debug("__init__:Start Certificate Request Wizard")
        
        self.step = 1
        self.maxStep = 4
        self.SetPageSize(wxSize(430, 80))

        self.page0 = IntroWindow(self, "Welcome to the Certificate Request Wizard", )
        self.page1 = SelectCertWindow(self, "Select Certificate Type")
        self.page2 = IdentityCertWindow(self, "Enter Your Information")
        self.page3 = ServiceCertWindow(self, "Enter Service Information")
        self.page4 = HostCertWindow(self, "Enter Host Information")
        self.page5 = SubmitReqWindow(self, "Submit Request")
        self.FitToPage(self.page1)

        self.log.debug("__init__:Set the initial order of the pages")
        
        self.page0.SetNext(self.page1)
        self.page1.SetNext(self.page2)
        self.page2.SetNext(self.page5)
        self.page3.SetNext(self.page5)
        self.page4.SetNext(self.page5)

        self.page1.SetPrev(self.page0)
        self.page2.SetPrev(self.page1)
        self.page3.SetPrev(self.page1)
        self.page4.SetPrev(self.page1)
        self.page5.SetPrev(self.page4)
      
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
                    
            elif certificateType == "HOST":
                self.page0.SetNext(self.page4)
                self.page4.SetPrev(self.page0)
                self.SetTitle("Request Certificate - Step 1 of %s"
                              %self.maxStep)
            else:
                self.log.info("__init__:Handle arguments for certificate type")
                raise Exception("Flag should be either IDENTITY, SERVICE or HOST")

        self.log.debug("__init__:Create the pages")

        EVT_WIZARD_PAGE_CHANGING(self, wizardId, self.ChangingPage)
        EVT_WIZARD_CANCEL(self, wizardId, self.CancelPage) 
        
        self.log.debug("__init__:Run the wizard")
        
        self.RunWizard(self.page0)


    def GetLog(self):
        """
        Create a log with our standard format and return it
        """
        log = logging.getLogger("AG.CertificateRequestTool")
        log.setLevel(logging.DEBUG)
        logFile = os.path.join(Platform.GetUserConfigDir(), "CertificateRequestTool.log")
        hdlr = logging.handlers.RotatingFileHandler(logFile, "a", 10000000, 0)
        logFormat = "%(asctime)s %(levelname)-5s %(message)s (%(filename)s)"
        hdlr.setFormatter(logging.Formatter(logFormat))
        log.addHandler(hdlr)
        
        return log
                         
    def CancelPage(self, event):
        self.log.debug(" CancelPage:Cancel wizard")
        dlg = wxMessageDialog(self,"Your certificate request is not complete. If you quit now, the request will not be submitted. \nCancel request?.", "", style = wxYES_NO | wxNO_DEFAULT | wxICON_QUESTION)
        if(dlg.ShowModal() == wxID_NO):
            event.Veto()
            
        dlg.Destroy()
                     
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
           
            if not page.Validate():
                self.log.debug("ChangingPage:Values are not correct, do not change page")
                event.Veto()
            else:
                self.log.debug("ChangingPage:Values are correct")

                self.step = self.step+1
                self.SetTitle("Request Certificate - Step %i of %i"
                              %(self.step, self.maxStep))

                next = page.GetNext()

                if next and isinstance(next, SubmitReqWindow):
                    name = ""
                    email = ""
                    domain = ""
                    request = ""
                    password = ""

                    if isinstance(page, IdentityCertWindow):
                        name = page.firstNameCtrl.GetValue() +" "+page.lastNameCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        domain = page.domainCtrl.GetValue()
                        request = "identity"
                        password = page.passwordCtrl.GetValue()
                        
                    elif  isinstance(page, HostCertWindow):
                        name = page.hostCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        request = "host"
                        
                    elif  isinstance(page, ServiceCertWindow):
                        name = page.serviceCtrl.GetValue()+" on "+page.hostCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        request = "service"

                    next.SetText(name, email, domain, request, password)
                    next.SetPrev(page)
                
        elif dir == backward:
            self.log.debug("ChangingPage: Go back from %s to %s"
                           %(page.__class__, page.GetPrev().__class__))
            self.step = self.step-1
            self.SetTitle("Request Certificate - Step %i of %i"
                          %(self.step, self.maxStep))
       

class TitledPage(wxPyWizardPage):
    '''
    Base class for all wizard pages.  Creates a title.
    '''
    def __init__(self, parent, title):
    
        wxPyWizardPage.__init__(self, parent)
        self.title = title
        self.next = None
        self.prev = None
        self.MakePageTitle()

    def MakePageTitle(self):
        '''
        Create page title
        '''
        self.sizer = wxBoxSizer(wxVERTICAL)
        self.SetSizer(self.sizer)
        title = wxStaticText(self, -1, self.title, style = wxALIGN_CENTER)
        title.SetLabel(self.title)
        title.SetFont(wxFont(14, wxNORMAL, wxNORMAL, wxBOLD))
        self.sizer.AddWindow(title, 0, wxALL|wxEXPAND, 5)
        self.sizer.AddWindow(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        self.sizer.Add(10, 10)
                       
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
        self.info = wxStaticText(self, -1, "This wizard will help you request a certificate.\n\nCertificates are used to identify everyone connected to the AccessGrid. \nIt is your electronic identity card verifying that you are who you say you are. \n\nClick 'Next' to continue.")
        self.Layout()
  
    def Layout(self):
        self.sizer.Add(self.info, 0, wxALL, 5)

                      
class SelectCertWindow(TitledPage):
    def __init__(self, parent, title):
        '''
        Includes information about certificates and an option to request a
        host, identity, or service certificate.
        '''
        TitledPage.__init__(self, parent, title)
        self.text = wxStaticText(self, -1, "Select Certificate Type: ")
        self.selectionList = ["Identity", "Service", "Host"]
        self.selections = wxComboBox(self, -1, self.selectionList[0], choices = self.selectionList, style = wxCB_READONLY)
        self.info = wxStaticText(self, -1, "There are three kinds of certificates:")
        self.info1 = wxStaticText(self, -1, "Identity Certificate:")
        self.info2 = wxStaticText(self, -1, "To identify an individual.")
        self.info3 = wxStaticText(self, -1, "Service Certificate:")
        self.info4 = wxStaticText(self, -1, "To identify a service.")
        self.info5 = wxStaticText(self, -1, "Host Certificate:")
        self.info6 = wxStaticText(self, -1, "To identify a machine.")
        self.parent = parent
        self.__setProperties()
        self.Layout()

    def GetNext(self):
        """
        Next page depends on what type of certificate the user selects
        Note: Overrides super class method
        """
        next = self.next
        value = self.selections.GetValue()

        if value == self.selectionList[0]:
            next = self.parent.page2
            self.parent.page2.SetPrev(self)

        elif value == self.selectionList[1]:
            next = self.parent.page3
            self.parent.page3.SetPrev(self)
            
        elif value == self.selectionList[2]:
            next = self.parent.page4
            self.parent.page4.SetPrev(self)
            
        return next

    def __setProperties(self):
        self.info1.SetFont(wxFont(wxDEFAULT, wxDEFAULT, wxNORMAL, wxBOLD))
        self.info3.SetFont(wxFont(wxDEFAULT, wxDEFAULT, wxNORMAL, wxBOLD))
        self.info5.SetFont(wxFont(wxDEFAULT, wxDEFAULT, wxNORMAL, wxBOLD))
        
    def Layout(self):
        '''
        Handles UI layout
        '''
        self.sizer.Add(self.info, 0, wxALL, 5)
        self.sizer.Add(10, 10)
        
        infoSizer = wxFlexGridSizer(3, 2, 6, 6)
        infoSizer.Add(self.info1, 0, wxCENTER)
        infoSizer.Add(self.info2, 0, wxEXPAND | wxALIGN_LEFT)
        infoSizer.Add(self.info3, 0, wxCENTER)
        infoSizer.Add(self.info4, 0, wxEXPAND | wxALIGN_LEFT)
        infoSizer.Add(self.info5, 0, wxCENTER)
        infoSizer.Add(self.info6, 0, wxEXPAND | wxALIGN_LEFT)    
        self.sizer.Add(infoSizer, 0, wxALL| wxEXPAND, 5)
        self.sizer.Add(10, 10)
        
        gridSizer = wxFlexGridSizer(1, 2, 6,6)
        gridSizer.Add(self.text, 0, wxALIGN_CENTER)
        gridSizer.Add(self.selections, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add(gridSizer, 0, wxALL| wxEXPAND, 5)


class IdentityCertWindow(TitledPage):
    '''
    Includes controls to request an identity certificate.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.text = wxStaticText(self, -1,"""The name fields should contain your first and last name; requests with incomplete \nnames may be rejected. The e-mail address will be used for verification; \nplease make sure it is valid. Remember your password.
            """)

        self.firstNameId = wxNewId()
        self.lastNameId = wxNewId()
        self.emailId = wxNewId()
        self.domainId = wxNewId()
        self.passwrdId = wxNewId()
        self.passwrd2Id = wxNewId()
       
        self.firstNameText = wxStaticText(self, -1, "First name:")
        self.lastNameText = wxStaticText(self, -1, "Last name:")
        self.emailText = wxStaticText(self, -1, "E-mail:")
        self.domainText = wxStaticText(self, -1, "Domain:")
        self.passwordText = wxStaticText(self, -1, "Password:")
        self.passwordVerText = wxStaticText(self, -1, "Retype password:")
        self.firstNameCtrl = wxTextCtrl(self, self.firstNameId ,
                                   validator = IdentityCertValidator())
        self.lastNameCtrl = wxTextCtrl(self, self.lastNameId ,
                                   validator = IdentityCertValidator())
        self.emailCtrl = wxTextCtrl(self, self.emailId,
                                    validator = IdentityCertValidator())
        self.domainCtrl = wxTextCtrl(self, self.domainId,
                                    validator = IdentityCertValidator())
        self.passwordCtrl = wxTextCtrl(self, self.passwrdId,
                                       style = wxTE_PASSWORD,
                                       validator = IdentityCertValidator())
        self.passwordVerCtrl = wxTextCtrl(self, self.passwrd2Id,
                                          style = wxTE_PASSWORD,
                                          validator = IdentityCertValidator())

        EVT_TEXT(self, self.firstNameId, self.EnterText)
        EVT_TEXT(self, self.lastNameId, self.EnterText)
        EVT_TEXT(self.emailCtrl, self.emailId, self.EnterEmailText)
        EVT_TEXT(self.domainCtrl, self.domainId, self.EnterDomainText)
        EVT_TEXT(self.passwordCtrl, self.passwrdId , self.EnterText)
        EVT_TEXT(self.passwordVerCtrl, self.passwrd2Id, self.EnterText)
        EVT_CHAR(self.domainCtrl, self.EnterDomainChar)
        self.Layout()

        #
        # State to set if the user entered anything in the domain
        # textbox. If so, don't change it on them.
        #
        self.userEnteredDomain = 0

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
        item.SetBackgroundColour("white")
        item.Refresh()

    def Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add(10, 10)
        gridSizer = wxFlexGridSizer(4, 2, 6, 6)
        #gridSizer.Add(self.nameText)
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.firstNameText)
        gridSizer.Add(box)

        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.firstNameCtrl, 1, wxRIGHT, 10)
        box.Add(self.lastNameText, 0,wxRIGHT, 5)
        box.Add(self.lastNameCtrl, 1, wxEXPAND)
        gridSizer.Add(box, 1, wxEXPAND)
        
        #gridSizer.Add(self.nameCtrl, 0, wxEXPAND)
        gridSizer.Add(self.emailText)
        gridSizer.Add(self.emailCtrl, 0, wxEXPAND)
        gridSizer.Add(self.domainText)
        gridSizer.Add(self.domainCtrl, 0, wxEXPAND)
        gridSizer.Add(self.passwordText)
        gridSizer.Add(self.passwordCtrl, 0, wxEXPAND)
        gridSizer.Add(self.passwordVerText)
        gridSizer.Add(self.passwordVerCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)

        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)


class ValidatorHelp(wxPyValidator):
    '''
    This class encapsulates methods that more than one validator will use.
    '''
    def __init__(self):
       
        wxPyValidator.__init__(self)
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
            return false
        
        # Check if some part of the domain matches the host name
        for part in domainPartsList:
           if host.find(part) != -1:
               return true

        return false

    def CheckHost(self, host):
        '''
        Checks to see if host is a valid machine name and not
        an IP address.
        '''
        for char in host:
            return char in string.letters
              
        return false

    
class IdentityCertValidator(wxPyValidator):
    '''
    Validator used to ensure correctness of parameters entered in
    IdentityCertWindow.
    '''
    def __init__(self):
        wxPyValidator.__init__(self)
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
        firstName = win.firstNameCtrl.GetValue()
        lastName = win.lastNameCtrl.GetValue()
        email = win.emailCtrl.GetValue()
        domain = win.domainCtrl.GetValue()
        password = win.passwordCtrl.GetValue()
        password2 = win.passwordVerCtrl.GetValue()
       
        
        if firstName == "":
            MessageDialog(NULL, "Please enter your first name.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.firstNameCtrl)
            return false

        elif lastName == "":
            MessageDialog(NULL, "Please enter your last name.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.lastNameCtrl)
            return false
        
        elif email == "":
            MessageDialog(NULL, "Please enter your e-mail address.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false

        elif email.find("@") == -1:
            MessageDialog(NULL, "Pleas enter a valid e-mail address, for example name@example.com.",
                          style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false
        
        elif password == "":
            MessageDialog(NULL, "Please enter your password.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.passwordCtrl)
            return false
            
        elif password != password2:
            MessageDialog(NULL, "Your password entries do not match. Please retype them.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.passwordCtrl)
            self.helpClass.SetColour(win.passwordVerCtrl)
            return false

        elif domain == "":
            MessageDialog(NULL, "Please enter the domain name of your home site; for example, example.com..", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.domainCtrl)
            return false
            

        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

  
class HostCertWindow(TitledPage):
    '''
    Includes information for requesting a host certificate.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.emailId = wxNewId()
        self.hostId = wxNewId()
        self.text = wxStaticText(self, -1, "The e-mail address will be used for verification, please make sure it is valid.")
        self.emailText = wxStaticText(self, -1, "E-mail:")
        self.hostText = wxStaticText(self, -1, "Machine Name:")
        self.emailCtrl = wxTextCtrl(self, self.emailId, validator = HostCertValidator())
        try:
            self.hostName = os.environ['HOSTNAME']
        except:
            self.hostName = ''
        self.hostCtrl = wxTextCtrl(self, self.hostId, self.hostName, validator = HostCertValidator())
        self.SetEvents()
        self.Layout()

    def SetEvents(self):
        '''
        Sets events
        '''
        EVT_TEXT(self.emailCtrl, self.emailId, self.EnterText)
        EVT_TEXT(self.hostCtrl , self.hostId , self.EnterText)
            
    def EnterText(self, event):
        '''
        Sets background color of the item that triggered the event to white.
        '''    
        item = event.GetEventObject()
        item.SetBackgroundColour("white")
        item.Refresh()
        
    def Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add(10, 10) 
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.hostText)
        gridSizer.Add(self.hostCtrl, 0, wxEXPAND)
        gridSizer.Add(self.emailText)
        gridSizer.Add(self.emailCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)

        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)

        
class HostCertValidator(wxPyValidator):
    '''
    Includes controls to request a host certificate.
    '''
    def __init__(self):
       
        wxPyValidator.__init__(self)
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
            MessageDialog(NULL, "Please enter the machine name (mcs.anl.gov).", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return false
        
        elif hostName.find('.') == -1:
            MessageDialog(NULL, "Please enter complete machine name (machine.mcs.anl.gov).", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return false

        elif not self.helpClass.CheckHost(hostName):
            MessageDialog(NULL, "Please enter valid machine name (machine.mcs.anl.gov). \nIP address is not a valid machine name.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return false
            
        elif email == "":
            MessageDialog(NULL, "Please enter your e-mail address.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false

        elif email.find("@") == -1:
            MessageDialog(NULL, "Pleas enter a valid e-mail address, for example name@mcs.anl.gov.",
                          style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false

        elif not self.helpClass.CheckEmail(hostName, email):
            MessageDialog(NULL, "The e-mail address and machine name should be on same domain. \n\nFor machine name: video.mcs.anl.gov  \n\nValid e-mail addresses could be: \n\nname@mcs.anl.gov or name@anl.gov \n",
                          style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false
        
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

        
class ServiceCertWindow(TitledPage):
    '''
    Includes information for requesting a service certificate.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.serviceId = wxNewId()
        self.hostId = wxNewId()
        self.emailId = wxNewId()
            
        self.text = wxStaticText(self, -1, "The e-mail address will be used for verification, please make sure it is valid.")
        self.serviceText = wxStaticText(self, -1, "Service Name:")
        self.hostText = wxStaticText(self, -1, "Machine Name:")
        self.emailText = wxStaticText(self, -1, "E-mail:")
        self.serviceCtrl = wxTextCtrl(self, self.serviceId,
                                      validator = ServiceCertValidator())
        self.emailCtrl = wxTextCtrl(self, self.emailId,
                                    validator = ServiceCertValidator())
        try:
            self.hostName = os.environ['HOSTNAME']
        except:
            self.hostName = ''
        self.hostCtrl = wxTextCtrl(self, self.hostId, self.hostName,
                                   validator = ServiceCertValidator())

        EVT_TEXT(self.serviceCtrl, self.serviceId, self.EnterText)
        EVT_TEXT(self.emailCtrl, self.emailId, self.EnterText)
        EVT_TEXT(self.hostCtrl, self.hostId , self.EnterText)
        self.Layout()

    def EnterText(self, event):
        '''
        Sets background color of the item that triggered the event to white.
        '''   
        item = event.GetEventObject()
        item.SetBackgroundColour("white")
        item.Refresh()
                   
    def Layout(self):
        '''
        Handles UI layout
        '''
        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add(10, 10) 
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.serviceText)
        gridSizer.Add(self.serviceCtrl, 0, wxEXPAND)
        gridSizer.Add(self.hostText)
        gridSizer.Add(self.hostCtrl, 0, wxEXPAND)
        gridSizer.Add(self.emailText)
        gridSizer.Add(self.emailCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)

        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)


class ServiceCertValidator(wxPyValidator):
    '''
    Validator used to ensure correctness of parameters entered in
    ServiceCertWindow.
    '''
    def __init__(self):
        wxPyValidator.__init__(self)
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
        name = win.serviceCtrl.GetValue()
        email = win.emailCtrl.GetValue()
        host = win.hostCtrl.GetValue()
            
        if name == "":
            MessageDialog(NULL, "Please enter service name.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.serviceCtrl)
            return false
             
        elif host == "":
            MessageDialog(NULL, "Please enter machine name (machine.mcs.anl.gov).", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return false

        elif host.find('.') == -1:
            MessageDialog(NULL, "Please enter complete machine name (machine.mcs.anl.gov).", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return false
            
        elif not self.helpClass.CheckHost(host):
            MessageDialog(NULL, "Please enter valid machine name (machine.mcs.anl.gov). \nIP address is not a valid machine name.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.hostCtrl)
            return false

        elif email == "":
            MessageDialog(NULL, "Please enter e-mail address.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false

        elif email.find("@") == -1:
            MessageDialog(NULL, "Pleas enter a valid e-mail address, for example name@mcs.anl.gov.",
                          style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false
        
        elif not self.helpClass.CheckEmail(host, email):
            MessageDialog(NULL, "The e-mail address and machine name should be on same domain. \n\nFor machine name: video.mcs.anl.gov  \n\nValid e-mail addresses could be: \n\nname@mcs.anl.gov or name@anl.gov \n",
                          style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.emailCtrl)
            return false
            
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.


class HTTPProxyConfigPanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1)

        sbox = wxStaticBox(self, -1, "Proxy server")
        self.sizer = wxStaticBoxSizer(sbox, wxVERTICAL)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        
        #
        # Stuff for the proxy configuration.
        #
        

        proxies = NetUtilities.GetHTTPProxyAddresses()

        defaultProxyHost = ""
        defaultProxyPort = ""
        defaultEnabled = 0
        
        if proxies != []:
            defaultProxy, defaultEnabled = proxies[0]
            defaultProxyHost, defaultProxyPort = defaultProxy
            if defaultProxyPort is None:
                defaultProxyPort = ""

        self.proxyEnabled = wxCheckBox(self, -1, "Use a proxy server to connect to the certificate server")

        EVT_CHECKBOX(self, self.proxyEnabled.GetId(), self.OnCheckbox)

        self.proxyText = wxTextCtrl(self, -1, defaultProxyHost)
        self.proxyPort = wxTextCtrl(self, -1, defaultProxyPort)

        self.proxyEnabled.SetValue(defaultEnabled)
        self.UpdateProxyEnabledState()

        self._Layout()
        self.Fit()

    def _Layout(self):
        #
        # Labelled box for the proxy stuff.
        #

        self.sizer.Add(self.proxyEnabled, 0, wxEXPAND | wxALL, 5)
        hsizer = wxBoxSizer(wxHORIZONTAL)
        hsizer.Add(wxStaticText(self, -1, "Address: "), 0, wxALIGN_CENTER_VERTICAL | wxALL, 2)
        hsizer.Add(self.proxyText, 1, wxEXPAND|wxRIGHT, 5)
        hsizer.Add(wxStaticText(self, -1, "Port: "), 0, wxALIGN_CENTER_VERTICAL | wxALL, 2)
        hsizer.Add(self.proxyPort, 0, wxEXPAND|wxRIGHT, 5)
        
        self.sizer.Add(hsizer, 0, wxEXPAND |wxBOTTOM, 5)

    def OnCheckbox(self, event):
        self.UpdateProxyEnabledState()
        
    def UpdateProxyEnabledState(self):

        en = self.proxyEnabled.GetValue()

        self.proxyText.Enable(en)
        self.proxyPort.Enable(en)

    def GetInfo(self):
        return (self.proxyEnabled.GetValue(),
                self.proxyText.GetValue(),
                self.proxyPort.GetValue())

class SubmitReqWindow(TitledPage):
    '''
    Shows the user what information will be submitted in the certificate
    request.
        '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.info = ""
        self.parent = parent
        self.text = wxTextCtrl(self, -1, self.info, size = wxSize(10,80),
                               style = wxNO_BORDER | wxNO_3D | wxTE_MULTILINE |
                               wxTE_RICH2 | wxTE_READONLY)
        self.text.SetBackgroundColour(self.GetBackgroundColour())

        self.proxyPanel = HTTPProxyConfigPanel(self)

        self.Layout()


    def SetText(self, name, email, domain, requestType, password):
        '''
        Sets the text based on previous page
        '''
        # Parameters for requesting a certificate
        self.name = name
        self.email = email
        self.domain = domain
        self.password = password
        self.request = requestType
        
        self.info =  "Click 'Finish' to submit %s certificate request for %s to Argonne.  A confirmation e-mail will be sent, within 2 business days, to %s.  \n\nPlease contact agdev-ca@mcs.anl.gov if you have questions."%(self.request, self.name, self.email)
       
        self.text.SetValue(self.info)
        
        requestStart = 25
        nameStart = 50 + len(self.request)
        emailStart = 127 + len(self.request) + len(self.name)

        self.text.SetInsertionPoint(0)
        self.text.SetStyle(nameStart, nameStart+len(self.name),
                               wxTextAttr(wxNullColour,
                                          font = wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD)))
        self.text.SetInsertionPoint(0)
        self.text.SetStyle(emailStart, emailStart+len(self.email),
                           wxTextAttr(wxNullColour, font = wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD)))
        self.text.SetInsertionPoint(0)
        self.text.SetStyle(requestStart, requestStart+len(self.request),
                           wxTextAttr(wxNullColour, font = wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD)))

        self.text.Refresh()
        
    def Validate(self):

        #
        # Go ahead and try to create the certificate request.
        #
        # We will invoke self.identityCertCreate() callback that
        # was passed to the constructor of the wizard.
        #

        wxBeginBusyCursor()
        self.Refresh()
        self.Update()

        success = false

        try:
            pinfo = self.proxyPanel.GetInfo()
            success = self.parent.createIdentityCertCB(str(self.name),
                                                       str(self.email),
                                                       str(self.domain),
                                                       str(self.password),
                                                       pinfo[0],
                                                       pinfo[1],
                                                       pinfo[2])
        finally:
            wxEndBusyCursor()
            self.Refresh()
            self.Update()

        return success

    def Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 1, wxALL|wxEXPAND, 5)
        self.sizer.Add(self.proxyPanel, 0, wxEXPAND | wxALIGN_BOTTOM)
               
class CertificateStatusDialog(wxDialog):
    '''
    Dialog showing submitted certificate requests.  It allows users to check status
    of requests and store them to right location.
    '''
    def __init__(self, parent, id, title, createIdentityCertCB = None):
        wxDialog.__init__(self, parent, id, title,
                          style=wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER )

        self.SetSize(wxSize(700,350))
        self.createIdentityCertCB = createIdentityCertCB

        self.info = wxStaticText(self, -1, "You have requested following certificates:")
        self.list = wxListCtrl(self, wxNewId(),
                               style = wxLC_REPORT | wxSUNKEN_BORDER)
        
        self.importButton = wxButton(self, -1, "Import certificate")
        self.importButton.Enable(0)

        self.deleteButton = wxButton(self, -1, "Delete request")
        self.deleteButton.Enable(0)

        self.getStatusButton = wxButton(self, -1, "Update Status")
        self.closeButton = wxButton(self, wxID_CLOSE, "Close")

        self.proxyPanel = HTTPProxyConfigPanel(self)
        
        self.newRequestButton = wxButton(self, wxNewId(), "New Request")

        self.certReqDict = {}
        self.certStatus = {}
        self.beforeStatus = 0
        self.afterStatus = 1
        self.state = self.beforeStatus
        self.selectedItem = None
        
        self.__setProperties()
        self.__layout()
        self.__setEvents()

        self.AddCertificates()
                                     
    def __setEvents(self):
        EVT_BUTTON(self, self.importButton.GetId(), self.OnImportCertificate)
        EVT_BUTTON(self, self.deleteButton.GetId(), self.OnDeleteRequest)
        EVT_BUTTON(self, self.getStatusButton.GetId(), self.OnUpdateStatus)
        EVT_BUTTON(self, self.closeButton.GetId(), self.OnClose)
        EVT_BUTTON(self, self.newRequestButton.GetId(), self.RequestCertificate)

        EVT_LIST_ITEM_SELECTED(self.list, self.list.GetId(),
                               self.OnCertSelected)

    def __layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.info, 0, wxEXPAND|wxLEFT|wxRIGHT|wxTOP, 10)

        hs = wxBoxSizer(wxHORIZONTAL)
        vs = wxBoxSizer(wxVERTICAL)
        
        hs.Add(self.list, 1, wxEXPAND|wxALL, 10)
        hs.Add(vs, 0, wxEXPAND)
        
        vs.Add(self.importButton, 0, wxALL | wxEXPAND, 2)
        vs.Add(self.deleteButton, 0, wxALL | wxEXPAND, 2)
        
        sizer.Add(hs, 1, wxEXPAND | wxRIGHT, 8)
        
        sizer.Add(self.proxyPanel, 0, wxEXPAND | wxALL, 10)

        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.getStatusButton, 0 , wxALL, 5)
        box.Add(self.newRequestButton, 0 , wxALL, 5)
        box.Add(self.closeButton, 0 , wxALL, 5)
        sizer.Add(box, 0, wxCENTER | wxBOTTOM, 5)

        self.SetAutoLayout(1)
        self.SetSizer(sizer)
        self.Layout()

        #self.list.SetColumnWidth(0, self.list.GetSize().GetWidth()/3.0)
        #self.list.SetColumnWidth(1, self.list.GetSize().GetWidth()/3.0)
        #self.list.SetColumnWidth(2, self.list.GetSize().GetWidth()/3.0)
                
    def __setProperties(self):
        self.list.InsertColumn(0, "Certificate Type")
        self.list.InsertColumn(1, "Subject Name")
        self.list.InsertColumn(2, "Date Requested")
        self.list.InsertColumn(3, "Status")
           
    def OnUpdateStatus(self, event):
        self.CheckStatus()
            
    def OnClose(self, event):
        self.Close()

    def OnCertSelected(self, event):
        row = event.m_itemIndex
        print "Selected item ", row
        self.selectedItem = row

        if row in self.certStatus:
            status = self.certStatus[row][0]

            if status == "Ready":
                self.importButton.Enable(1)
                
            else:
                self.importButton.Enable(0)

        self.deleteButton.Enable(1)
            
    def OnDeleteRequest(self, event):
        print "delete, sel is ", self.selectedItem

        if self.selectedItem is None:
            return

        try:
            certMgr = Toolkit.GetApplication().GetCertificateManager()
            req = self.reqList[self.selectedItem][0]
            log.debug("Removing request %s", req.GetSubject())
            certMgr.GetCertificateRepository().RemoveCertificateRequest(req)
        except:
            log.exception("Error removing cert request")

        self.AddCertificates()
        
    def OnImportCertificate(self, event):

        print "import, sel is ", self.selectedItem
        if self.selectedItem is None:
            return
        
        item = self.reqList[self.selectedItem]
        status = self.certStatus[self.selectedItem]

        cert = status[1]

        #
        # Write the cert out to a tempfile, then import.
        #

        hash = md5.new(cert).hexdigest()
        tempfile = os.path.join(Platform.GetTempDir(), "%s.pem" % (hash))

        try:
            try:
                fh = open(tempfile, "w")
                fh.write(cert)
                fh.close()

                certMgr = Toolkit.GetApplication().GetCertificateManager()
                impCert = certMgr.ImportRequestedCertificate(tempfile)

                MessageDialog(self,
                              "Successfully imported certificate for\n" +
                              str(impCert.GetSubject()),
                              "Import Successful")
                self.AddCertificates()

            except RepoInvalidCertificate, e:
                log.exception("Invalid certificate")
                msg = e[0]
                ErrorDialog(self,
                            "The import of your approved certificate failed:\n"+
                            msg,
                            "Import Failed")


            except:
                log.exception("Import of requested cert failed")
                ErrorDialog(self,
                            "The import of your approved certificate failed.",
                            "Import Failed")

        finally:
            os.unlink(tempfile)

            

    def RequestCertificate(self, event):
        self.Hide()
        reqTool = CertificateRequestTool(None,
                                         certificateType = 'IDENTITY',
                                         createIdentityCertCB = self.createIdentityCertCB)
        reqTool.Destroy()
                                  
    def AddCertificates(self):

        certMgr = Toolkit.GetApplication().GetCertificateManager()

        #
        # reqList is a list of tuples (requestDescriptor, token, server, creationTime)
        #
        
        self.reqList = certMgr.GetPendingRequests()

        self.list.DeleteAllItems()

        row = 0
        for reqItem in self.reqList:

            self.certStatus[row] = ("Unknown")
            requestDescriptor, token, server, creationTime = reqItem

            #
            # For now we're just doing identity certificates.
            #

            type = "Identity"
            subject = str(requestDescriptor.GetSubject())

            if creationTime is not None:
                date = time.strftime("%x %X", time.localtime(int(creationTime)))
            else:
                date = ""

            status = "?"

            self.list.InsertStringItem(row, type)
            self.list.SetStringItem(row, 1, subject)
            self.list.SetStringItem(row, 2, date)
            self.list.SetStringItem(row, 3, status)
            self.list.SetItemData(row, row)
            row = row+1

        if len(self.reqList) == 0:
            self.list.SetColumnWidth(0, wxLIST_AUTOSIZE_USEHEADER)
            self.list.SetColumnWidth(1, wxLIST_AUTOSIZE_USEHEADER)
        else:
            self.list.SetColumnWidth(0, wxLIST_AUTOSIZE)
            self.list.SetColumnWidth(1, wxLIST_AUTOSIZE)
            
        self.list.SetColumnWidth(2, wxLIST_AUTOSIZE_USEHEADER)
        self.list.SetColumnWidth(3, wxLIST_AUTOSIZE_USEHEADER)

        self.CheckStatus()
                                
    def CheckStatus(self):
        """
        Update the status of the certificate requests we have listed in the GUI.

        """

        certMgr = Toolkit.GetApplication().GetCertificateManager()

        proxyEnabled, proxyHost, proxyPort = self.proxyPanel.GetInfo()
        print "Check got pinfo ", proxyEnabled, proxyHost, proxyPort
        
        # Check status of certificate requests
        for row in range(0, self.list.GetItemCount()):

            self.certStatus[row] = ("Unknown")
            
            itemId = self.list.GetItemData(row)
            reqItem = self.reqList[itemId]
            requestDescriptor, token, server, creationTime = reqItem

            print "Testing request %s server=%s token=%s" % (requestDescriptor,
                                                             server, token)
            self.list.SetStringItem(row, 3, "Checking...")
            self.Refresh()
            self.Update()
            if server is None or token is None:
                #
                # Can't check.
                #
                self.list.SetStringItem(row, 3, "Invalid")
                continue

            if proxyEnabled:
                certReturn = certMgr.CheckRequestedCertificate(requestDescriptor, token, server,
                                                               proxyHost, proxyPort)
            else:
                certReturn = certMgr.CheckRequestedCertificate(requestDescriptor, token, server)

            success, msg = certReturn
            if not success:

                #
                # Map nonobvious errors
                #

                if msg.startswith("Couldn't open certificate file."):
                    msg = "Not ready"
                elif msg.startswith("Couldn't read from certificate file."):
                    msg = "Not ready"
                elif msg.startswith("There is no certificate for this token."):
                    msg = "Request not found"
                
                self.list.SetStringItem(row, 3, msg)
                self.certStatus[row] = ("NotReady")
            else:
                self.list.SetStringItem(row, 3, "Ready for installation")
                self.certStatus[row] = ("Ready", msg)

            self.list.SetColumnWidth(3, wxLIST_AUTOSIZE)
            
#              self.cancelButton.Enable(false)

#              if cert != "":
#                  self.certificateClient.SaveCertificate(cert)
#                  nrOfApprovedCerts = nrOfApprovedCerts + 1
#                  # Change the status text
#                  self.text.SetLabel("%i of you certificates are installed. Click 'Ok' to start using them." %nrOfApprovedCerts)
#                  self.list.SetStringItem(row, 2, "Installed")

#              else:
#                  # Change status text to something else
#                  self.list.SetStringItem(row, 2, "Not approved")
#                  self.text.SetLabel("Your certificates have not been approved yet. \nPlease try again later.")
                
                        
if __name__ == "__main__":
    pp = wxPySimpleApp()

    from AccessGrid import Toolkit
    app = Toolkit.WXGUIApplication()
    app.Initialize()

    # Check if we have any pending certificate requests
    testURL = "http://www-unix.mcs.anl.gov/~judson/certReqServer.cgi"
    certificateClient = CRSClient(testURL)
    # nrOfReq = certificateClient.GetRequestedCertificates().keys()
    nrOfReq = 1
    if nrOfReq > 0:
        # Show pending requests
        certStatus = CertificateStatusDialog(None, -1, "Certificate Status Dialog")
        certStatus.ShowModal()    

    else:
        # Show certificate request wizard
        certReq = CertificateRequestTool(None, certificateType = "IDENTITY")
        certReq.Destroy()
