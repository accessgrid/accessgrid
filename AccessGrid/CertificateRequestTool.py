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

from wxPython.wx import *
from wxPython.wizard import *
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from AccessGrid import CertificateRepository
from AccessGrid.CertificateRepository import RepoDoesNotExist
from AccessGrid.CRSClient import CRSClient

import string

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
        self.SetPageSize(wxSize(450, 80))

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
        logFile="CertificateRequestTool.log"
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
                    request = ""
                    password = ""

                    if isinstance(page, IdentityCertWindow):
                        name = page.nameCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
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

                    next.SetText(name, email, request, password)
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
        self.info = wxStaticText(self, -1, "This wizard will help you request a certificare.\n\nCertificates are used to identify everyone connected to the AccessGrid. \nIt is your electronic identity card verifying that you are who you say you are. \n\nClick 'Next' to continue.")
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
        self.text = wxStaticText(self, -1, "The e-mail address will be used for verification, please make sure it is valid.")

        self.nameId = wxNewId()
        self.emailId = wxNewId()
        self.passwrdId = wxNewId()
        self.passwrd2Id = wxNewId()
       
        self.nameText = wxStaticText(self, -1, "Name:")
        self.emailText = wxStaticText(self, -1, "E-mail:")
        self.passwordText = wxStaticText(self, -1, "Password:")
        self.passwordVerText = wxStaticText(self, -1, "Retype Password:")
        self.nameCtrl = wxTextCtrl(self, self.nameId ,
                                   validator = IdentityCertValidator())
        self.emailCtrl = wxTextCtrl(self, self.emailId,
                                    validator = IdentityCertValidator())
        self.passwordCtrl = wxTextCtrl(self, self.passwrdId,
                                       style = wxTE_PASSWORD,
                                       validator = IdentityCertValidator())
        self.passwordVerCtrl = wxTextCtrl(self, self.passwrd2Id,
                                          style = wxTE_PASSWORD,
                                          validator = IdentityCertValidator())

        EVT_TEXT(self, self.nameId, self.EnterText)
        EVT_TEXT(self.emailCtrl, self.emailId, self.EnterText)
        EVT_TEXT(self.passwordCtrl, self.passwrdId , self.EnterText)
        EVT_TEXT(self.passwordVerCtrl, self.passwrd2Id, self.EnterText)
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
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add(10, 10)
        gridSizer = wxFlexGridSizer(4, 2, 6, 6)
        gridSizer.Add(self.nameText)
        gridSizer.Add(self.nameCtrl, 0, wxEXPAND)
        gridSizer.Add(self.emailText)
        gridSizer.Add(self.emailCtrl, 0, wxEXPAND)
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
        name = win.nameCtrl.GetValue()
        email = win.emailCtrl.GetValue()
        password = win.passwordCtrl.GetValue()
        password2 = win.passwordVerCtrl.GetValue()
        
        if name == "":
            MessageDialog(NULL, "Please enter your name.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.nameCtrl)
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
        
        elif password == "":
            MessageDialog(NULL, "Please enter your password.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.passwordCtrl)
            return false
            
        elif password != password2:
            MessageDialog(NULL, "Your password entries do not match. Please retype them.", style = wxOK | wxICON_INFORMATION)
            self.helpClass.SetColour(win.passwordCtrl)
            self.helpClass.SetColour(win.passwordVerCtrl)
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
        self.Layout()

    def SetText(self, name, email, requestType, password):
        '''
        Sets the text based on previous page
        '''
        # Parameters for requesting a certificate
        self.name = name
        self.email = email
        self.password = password
        self.request = requestType
        
        self.info =  "Click 'Finish' to submit %s certificate request for %s to Argonne.  A confirmation e-mail will be sent, within 2 business days, to %s.  \n\nPlease contact agdev_ca@mcs.anl.gov if you have questions."%(self.request, self.name, self.email)
       
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

        self.parent.createIdentityCertCB(str(self.name),
                                         str(self.email),
                                         'my.domain',
                                         str(self.password))

        return true

    def Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 0, wxALL|wxEXPAND, 5)


class CertificateStatusDialog(wxDialog):
    '''
    Dialog showing submitted certificate requests.  It allows users to check status
    of requests and store them to right location.
    '''
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title, style=wxDEFAULT_DIALOG_STYLE)
        self.SetSize(wxSize(400,250))
        self.info = wxStaticText(self, -1, "You have requested following certificates:")
        self.list = wxListCtrl(self, wxNewId(),
                               style = wxLC_REPORT | wxLC_SORT_ASCENDING | wxSUNKEN_BORDER)
        
        self.text = wxStaticText(self, -1, "Click 'Ok' to check their status.")
        self.certificateClient = CRSClient("a url")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.newRequestButton = wxButton(self, wxNewId(), "New Request")
        self.certReqDict = {}
        self.requestStatus = {}
        self.beforeStatus = 0
        self.afterStatus = 1
        self.state = self.beforeStatus

       
        self.__setProperties()
        self.__layout()
        self.__setEvents()

        self.AddCertificates()
                                     
    def __setEvents(self):
        EVT_BUTTON(self, self.okButton.GetId(), self.Ok)
        EVT_BUTTON(self, self.newRequestButton.GetId(), self.RequestCertificate)

    def __layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.info, 0, wxEXPAND|wxLEFT|wxRIGHT|wxTOP, 10)
        sizer.Add(self.list, 1, wxEXPAND|wxALL, 10)
        sizer.Add(self.text, 0, wxEXPAND|wxALL, 10)
        sizer.Add(10,10)
        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND)

        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.okButton, 0 , wxALL, 5)
        box.Add(self.cancelButton, 0 , wxALL, 5)
        box.Add(self.newRequestButton, 0 , wxALL, 5)

        sizer.Add(box, 0, wxCENTER)

        self.SetAutoLayout(1)
        self.SetSizer(sizer)
        self.Layout()

        self.list.SetColumnWidth(0, self.list.GetSize().GetWidth()/3.0)
        self.list.SetColumnWidth(1, self.list.GetSize().GetWidth()/3.0)
        self.list.SetColumnWidth(2, self.list.GetSize().GetWidth()/3.0)
                
    def __setProperties(self):
        self.list.InsertColumn(0, "Certificate Type")
        self.list.InsertColumn(1, "Date")
        self.list.InsertColumn(2, "Status")
           
    def Ok(self, event):
        if self.state == self.beforeStatus:
            self.CheckStatus()
            self.state = self.afterStatus
        else:
            self.Close()
            
    def RequestCertificate(self, event):
        self.Hide()
        certReq = CertificateRequestTool(self, None)
                            
    def AddCertificates(self):
        
        self.certReqDict = self.certificateClient.GetRequestedCertificates()

        row = 0 
        for requestId, request in self.certReqDict.items():
            type, date, status = request
            self.list.InsertStringItem(row, type)
            self.list.SetStringItem(row, 1, date)
            self.list.SetStringItem(row, 2, status)
            self.requestStatus[requestId] = row
            row = row+1
                                
    def CheckStatus(self):
        nrOfApprovedCerts = 0
                
        # Check status of certificate requests
        for requestId in self.certReqDict.keys():
                       
            # Get certificate and save it
            cert = self.certificateClient.RetrieveCertificate(requestId)
            row = self.requestStatus[requestId]
            self.cancelButton.Enable(false)

            if cert != "":
                self.certificateClient.SaveCertificate(cert)
                nrOfApprovedCerts = nrOfApprovedCerts + 1
                # Change the status text
                self.text.SetLabel("%i of you certificates are installed. Click 'Ok' to start using them." %nrOfApprovedCerts)
                self.list.SetStringItem(row, 2, "Installed")

            else:
                # Change status text to something else
                self.list.SetStringItem(row, 2, "Not approved")
                self.text.SetLabel("Your certificates have not been approved yet. \nPlease try again later.")
                
                        
if __name__ == "__main__":
    pp = wxPySimpleApp()

    # Check if we have any pending certificate requests
    testURL = "http://www-unix.mcs.anl.gov/~judson/certReqServer.cgi"
    certificateClient = CRSClient(testURL)
    # nrOfReq = certificateClient.GetRequestedCertificates().keys()
    nrOfReq = 0
    if nrOfReq > 0:
        # Show pending requests
        certStatus = CertificateStatusDialog(None, -1, "Certificate Status Dialog")
        certStatus.ShowModal()    

    else:
        # Show certificate request wizard
        certReq = CertificateRequestTool(None, certificateType = "IDENTITY")
        certReq.Destroy()
