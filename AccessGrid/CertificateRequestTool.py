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
import string

class CertificateRequestTool(wxWizard):
    '''
    This wizard guides users through the steps necessary for
    requesting either an identity, host, or service certificate. 
    '''
    def __init__(self, parent, flag = None):
        wizardId =  wxNewId()
        wxWizard.__init__(self, parent, wizardId,"", wxNullBitmap)
        self.step = 1
        self.maxStep = 4
        self.SetPageSize(wxSize(450, 80))

        self.page0 = IntroWindow(self, "Welcome to the Certificate Request Wizard")
        self.page1 = SelectCertWindow(self, "Select Certificate")
        self.page2 = IdentityCertWindow(self, "Enter Your Information")
        self.page3 = ServiceCertWindow(self, "Enter Service Information")
        self.page4 = HostCertWindow(self, "Enter Host Information")
        self.page5 = SubmitReqWindow(self, "Submit Request")
        self.FitToPage(self.page1)

        # Set the initial order of the pages
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
      
        
        if flag:
            self.maxStep = 3
            if flag == "IDENTITY":
                self.page0.SetNext(self.page2)
                self.page2.SetPrev(self.page0)
                self.SetTitle("Request Certificate - Step 1 of %s"
                              %self.maxStep)
                        
            elif flag == "SERVICE":
                self.page0.SetNext(self.page3)
                self.page3.SetPrev(self.page0)
                self.SetTitle("Request Certificate - Step 1 of %s"
                              %self.maxStep)
                    
            elif flag == "HOST":
                self.page0.SetNext(self.page4)
                self.page4.SetPrev(self.page0)
                self.SetTitle("Request Certificate - Step 1 of %s"
                              %self.maxStep)
            else:
                raise Exception("Flag is either IDENTITY, SERVICE or HOST")
        # Create the pages
        EVT_WIZARD_PAGE_CHANGING(self, wizardId, self.ChangingPage)
        EVT_WIZARD_CANCEL(self, wizardId, self.CancelPage) 
        
        # Run the wizard
        self.RunWizard(self.page0)
                         
    def CancelPage(self, event):
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
            # Check to see if values are entered correctly
            if not page.Validate():
                # If not, ignore the event
                event.Veto()
            else:
                self.step = self.step+1
                self.SetTitle("Request Certificate - Step %i of %i"
                              %(self.step, self.maxStep))

                next = page.GetNext()

                if next and isinstance(next, SubmitReqWindow):
                    name = ""
                    email = ""
                    request = ""

                    if isinstance(page, IdentityCertWindow):
                        name = page.nameCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        request = "identity"
                        
                    elif  isinstance(page, HostCertWindow):
                        name = page.hostCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        request = "host"
                        
                    elif  isinstance(page, ServiceCertWindow):
                        name = page.serviceCtrl.GetValue()+" on "+page.hostCtrl.GetValue()
                        email = page.emailCtrl.GetValue()
                        request = "service"

                    next.SetText(name, email, request)
                    next.SetPrev(page)
                
        elif dir == backward:
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
        self.info = wxStaticText(self, -1, "Certificates are used to identify everyone connected to the AccessGrid. \n\nYou are required to have a certificate to use the program. It is your electronic \nidentity card verifying that you are who you say you are. \n\nClick 'Next' to continue.")
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
        self.info2 = wxStaticText(self, -1, "To identify an individual")
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
        self.info1.SetFont(wxFont(wxDEFAULT, wxDEFAULT, wxDEFAULT, wxBOLD))
        self.info3.SetFont(wxFont(wxDEFAULT, wxDEFAULT, wxDEFAULT, wxBOLD))
        self.info5.SetFont(wxFont(wxDEFAULT, wxDEFAULT, wxDEFAULT, wxBOLD))
        
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

    #def GetNext(self):
    #    '''
    #    Gives the following page and is also setting the following page to
    #    point to this page as previous.
    #    Note: Overrides super class method
    #    '''
    #    self.next.next.next.SetPrev(self)
    #    return self.next.next.next
                          
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
            if char in string.letters and char != '.':
                return true

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
        self.text = wxTextCtrl(self, -1, self.info, size = wxSize(10,80),
                               style = wxNO_BORDER | wxNO_3D | wxTE_MULTILINE |
                               wxTE_RICH2 | wxTE_READONLY)
        self.text.SetBackgroundColour(self.GetBackgroundColour())
        self.Layout()

    def SetText(self, name, email, requestType):
        '''
        Sets the text based on previous page
        '''
        self.name = name
        self.email = email
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
        # Create a certificate request
        repositoryPath = "/home/lefvert/AccessGrid/AccessGrid/repo"
        try:
            repo = CertificateRepository.CertificateRepository(repositoryPath)

       
            name = [("O", "Argonne"),
                    ("OU", "mcs.anl.gov"),
                    ("CN", "Susanne Lefvert")]
            desc = repo.CreateCertificateRequest(name, "Identity Certificate")
            print desc.ExportPEM()
            print "subj is ", desc.GetSubject()
            print "mod is ", desc.GetModulus()
            print "modhash is ", desc.GetModulusHash()
            
        except RepoDoesNotExist:
            MessageDialog(self, "You do not have a certificate repository. Certificate request can not be created.", style = wxICON_ERROR)
            

        # Send certificate request to open certificate authority

        #
        # ?
        #


        return true

    def Layout(self):
        '''
        Handles UI layout.
        '''
        self.sizer.Add(self.text, 0, wxALL|wxEXPAND, 5)


if __name__ == "__main__":
    pp = wxPySimpleApp()
    certReq = CertificateRequestTool(None)
    certReq.Destroy()
     
