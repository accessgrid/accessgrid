"""
wxPython GUI code for the Certificate Manager.

This needs to be in a separate file because any attempt to import
wxPython.wx, even inside a try/except block, will result in a process
exit on Linux if the DISPLAY environment variable is not set.

"""

import time
import string
import logging

log = logging.getLogger("AG.CertificateManagerWXGUI")

from OpenSSL_AG import crypto
from wxPython.wx import *
from AccessGrid.Toolkit import AG_TRUE, AG_FALSE
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog

from AccessGrid import CertificateManager
from AccessGrid import CertificateRepository
from AccessGrid.CertificateRequestTool import CertificateRequestTool
from AccessGrid.CRSClient import CRSClient

#
# Custom event types for the cert browser.
#

CERTSELECTED = wxNewEventType()
CERTIMPORT = wxNewEventType()
CERTEXPORT = wxNewEventType()
CERTDELETE = wxNewEventType()

def EVT_CERT_SELECTED(window, fun):
    window.Connect(-1, -1, CERTSELECTED, fun)

def EVT_CERT_IMPORT(window, fun):
    window.Connect(-1, -1, CERTIMPORT, fun)

def EVT_CERT_EXPORT(window, fun):
    window.Connect(-1, -1, CERTEXPORT, fun)

def EVT_CERT_DELETE(window, fun):
    window.Connect(-1, -1, CERTDELETE, fun)

class CertSelectedEvent(wxPyCommandEvent):
    eventType = CERTSELECTED
    def __init__(self, id, cert):
        self.cert = cert
        wxPyCommandEvent.__init__(self, self.eventType, id)
    def Clone( self ):
        self.__class__( self.GetId() )
        
class CertImportEvent(wxPyCommandEvent):
    eventType = CERTIMPORT
    def __init__(self, id):

        wxPyCommandEvent.__init__(self, self.eventType, id)
    def Clone( self ):
        self.__class__( self.GetId() )
        
class CertExportEvent(wxPyCommandEvent):
    eventType = CERTEXPORT
    def __init__(self, id):

        wxPyCommandEvent.__init__(self, self.eventType, id)
    def Clone( self ):
        self.__class__( self.GetId() )
        
class CertDeleteEvent(wxPyCommandEvent):
    eventType = CERTDELETE
    def __init__(self, id):

        wxPyCommandEvent.__init__(self, self.eventType, id)
    def Clone( self ):
        self.__class__( self.GetId() )
        
class CertificateManagerWXGUI(CertificateManager.CertificateManagerUserInterface):
    """
    wxWindows-based user interfact to the certificate mgr.
    """

    def __init__(self):
        CertificateManager.CertificateManagerUserInterface.__init__(self)

    def GetPassphraseCallback(self, caption, message):
        return lambda rwflag, caption = caption, message = message, self = self: \
            self.GUIPassphraseCallback(rwflag, caption, message)

    def GUIPassphraseCallback(self, rwflag, caption, message):
        dlg = wxTextEntryDialog(None, message, caption, style = wxTE_PASSWORD)
        rc = dlg.ShowModal()

        if rc == wxID_OK:
            ret = str(dlg.GetValue())
        else:
            ret = None

        dlg.Destroy()

        return ret
            
    def ReportError(self, err):
        dlg = wxMessageDialog(None, err, "Certificate manager error",
                              style = wxOK)
        dlg.ShowModal()
        dlg.Destroy()                

    def ReportBadPassphrase(self):
        dlg = wxMessageDialog(None,
                              "Incorrect passphrase. Try again?",
                              style = wxYES_NO | wxYES_DEFAULT)
        rc = dlg.ShowModal()
        dlg.Destroy()
        if rc == wxID_YES:
            return 1
        else:
            return 0
        
    def GetProxyInfo(self, cert, msg = ""):
        """
        Construct and show a dialog to retrieve proxy creation information from user.

        """

        dlg = PassphraseDialog(None, -1, "Enter passphrase", cert, msg)
        rc = dlg.ShowModal()
        if rc == wxID_OK:
            return dlg.GetInfo()
        else:
            return None

    def GetMenu(self, win):
        certMenu = wxMenu()

        i = wxNewId()
        certMenu.Append(i, "View &Trusted CA Certificates...")
        EVT_MENU(win, i,
                 lambda event, win=win, self=self: self.OpenTrustedCertDialog(event, win))

        i = wxNewId()
        certMenu.Append(i, "View &Identity Certificates...")
        EVT_MENU(win, i,
                 lambda event, win=win, self=self: self.OpenIdentityCertDialog(event, win))

        return certMenu

    def OpenTrustedCertDialog(self, event, win):
        dlg = TrustedCertDialog(win, -1, "View trusted certificates",
                                self.certificateManager.certRepo)
        dlg.ShowModal()
        dlg.Destroy()

    def OpenIdentityCertDialog(self, event, win):
        dlg = IdentityCertDialog(win, -1, "View user identity certificates",
                                self.certificateManager.certRepo)
        dlg.ShowModal()
        dlg.Destroy()

    def InitGlobusEnvironment(self):
        """
        Initialize the globus runtime environment.

        This method invokes certmgr.InitEnvironment().

        If the InitEnvrironment call succeeds, we are done.

        If it does not succeed, it may raise a number of different exceptions
        based on what in particular the error was. These must be handled
        before the InitGlobusEnvironment call can succeed.

        Since this is the user interface class, it can expect to do some
        work on behalf of the user to remedy the problems.
        """

        success  = 0
        while 1:
            try:
                self.certificateManager.InitEnvironment()
                # yay!
                success = 1
                break

            except CertificateManager.NoCertificates:

                success = self.HandleNoCertificateInteraction()
                break

            except CertificateManager.NoDefaultIdentity:
                dlg = wxMessageDialog(None, 
                                      "There are more than one certificates loaded and a unique default is not set; using the first one.",
                                      "Multiple default identities");
                dlg.ShowModal()
                                      

                certs = self.certificateManager.GetIdentityCerts()
                self.certificateManager.SetDefaultIdentity(certs[0])
                # loop back to init env

            except CertificateManager.NoProxyFound:
                retry = self.CreateProxy()
                if not retry:
                    break

            except CertificateManager.ProxyExpired:
                retry = self.CreateProxy()
                if not retry:
                    break

        print "done, success=", success

        return success

    def HandleNoCertificateInteraction(self):
        """
        Encapsulate the user interaction that takes place when the
        app starts up and tehre are no users.

        This should check for pending certificates and bring up the
        status dialog if there are.

        It also brings up the cert request tool.

        """

        reqTool = CertificateRequestTool(None,
                                         certificateType = 'IDENTITY',
                                         createIdentityCertCB = self.CreateCertificateRequestCB)
        reqTool.Destroy()

        return 1
    
    def CreateProxy(self):
        """
        GUI interface for creating a Globus proxy.

        Collect the passphrase, lifetime in hours, and key-size from user.

        Returns 1 if we either successfully created the proxy, or if we didn't create
        one but the user wants to try again.

        Returns 0 if we should cancel the transaction.
        
        """

        ident = self.certificateManager.GetDefaultIdentity()

        #
        # In order to create a globus proxy, there must be a default identity.
        #
        
        if ident is None:
            dlg = wxMessageDialog(None, 
                                  "No default identity is available.",
                                  "No default identity",
                                  style = wxOK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # See if we really need to have a proxy.
        #

        if not ident.HasEncryptedPrivateKey():
            #
            # We're using an unencrypted private key; proxies unnecessary.
            #

            return

        #
        # Attempt to create a proxy.
        #

        while 1:

            ppdlg = PassphraseDialog(None, -1, "Create a globus proxy", ident)
            rc = ppdlg.ShowModal()
            if rc != wxID_OK:
                ppdlg.Destroy()
                return 0
                break

            passphrase, lifetime, bits = ppdlg.GetInfo()

            ppdlg.Destroy()
                
            #
            # Have input, try to create proxy.
            #

            try:
                # passphrase comes back as a unicode
                passphrase = str(passphrase)
                bits = int(bits)
                lifetime = int(lifetime)
                self.certificateManager.CreateProxyCertificate(passphrase, bits, lifetime)
                print "Proxy created"
                break
            except:
                dlg = wxMessageDialog(None, "Invalid passphrase. Try again?",
                                      "Invalid passphrase",
                                      style= wxYES_NO | wxYES_DEFAULT)
                rc = dlg.ShowModal()
                dlg.Destroy()

                if rc != wxID_YES:
                    return 0
        return 1

    def CreateCertificateRequestCB(self, name, email, domain, password):
        """
        Callback routine that is passed to the CertificateRequestTool.

        Perform the actual certificate request mechanics.

        Returns 1 on success, 0 on failure.
        """

        log.debug("CreateCertificateRequestCB:Create a certificate request")


        try:
            repo = self.certificateManager.GetCertificateRepository()

            #
            # Ptui. Hardcoding name for the current AGdev CA.
            # Also hardcoding location of submission URL.
            #

            submitServerURL = "http://www-unix.mcs.anl.gov/~judson/certReqServer.cgi"

            name = [("O", "Access Grid"),
                    ("OU", "agdev-ca.mcs.anl.gov"),
                    ("OU", domain),
                    ("CN", name)]

            certificateRequest = repo.CreateCertificateRequest(name, password)

            pem =  certificateRequest.ExportPEM()

            log.debug("SubmitRequest:Validate: ExportPEM returns %s", pem)
            log.debug("SubmitRequest:Validate: subj is %s",
                      certificateRequest.GetSubject())
            log.debug("SubmitRequest:Validate: mod is %s",
                      certificateRequest.GetModulus())
            log.debug("SubmitRequest:Validate:modhash is %s",
                      certificateRequest.GetModulusHash())

            certificateClient = CRSClient(submitServerURL)
            requestId = certificateClient.RequestCertificate(email, pem)

            log.debug("SubmitRequest:Validate:Request id is %s", requestId)

            certificateRequest.SetMetadata("AG.CertificateManager.requestToken",
                                           str(requestId))
            
        except CertificateRepository.RepoDoesNotExist:
            log.exception("SubmitRequest:Validate:You do not have a certificate repository. Certificate request can not be completed.")

            MessageDialog(None,
                          "You do not have a certificate repository. Certificate request can not be completed.",
                          style = wxICON_ERROR)

        except:
            log.exception("SubmitRequest:Validate: Certificate request can not be completed")
            MessageDialog(None,
                          "Error occured. Certificate request can not be completed.",
                          style = wxICON_ERROR)


class PassphraseDialog(wxDialog):
    def __init__(self, parent, id, title, cert, msg = ""):

        self.cert = cert

        wxDialog.__init__(self, parent, id, title)

        sizer = wxBoxSizer(wxVERTICAL)

        t = wxStaticText(self, -1, "Create a proxy for %s" % cert.GetSubject())
        sizer.Add(t, 0, wxEXPAND | wxALL, 4)

        if msg != "":
            t = wxStaticText(self, -1, msg)
            sizer.Add(t, 0, wxEXPAND | wxALL, 4)
            

        grid = wxFlexGridSizer(cols = 2, hgap = 3, vgap = 3)
        sizer.Add(grid, 1, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Pass phrase:")
        grid.Add(t, 0, wxALL, 4)

        passId = wxNewId()
        self.passphraseText = wxTextCtrl(self, passId,
                                         style = wxTE_PASSWORD | wxTE_PROCESS_ENTER )
        grid.Add(self.passphraseText, 0, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Key size:")
        grid.Add(t, 0, wxALL, 4)

        keyId = wxNewId()
        self.keyList = wxComboBox(self, keyId,
                                  style = wxCB_READONLY,
                                  choices = ["512", "1024", "2048", "4096"])
        self.keyList.SetSelection(1)
        grid.Add(self.keyList, 1, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Proxy lifetime (hours):")
        grid.Add(t, 0, wxALL, 4)

        lifeTimeId = wxNewId()
        self.lifetimeText = wxTextCtrl(self, lifeTimeId, "8", style = wxTE_PROCESS_ENTER )
        grid.Add(self.lifetimeText, 0, wxEXPAND | wxALL, 4)

        grid.AddGrowableCol(1)

        h = wxBoxSizer(wxHORIZONTAL)

        sizer.Add(h, 0, wxALIGN_CENTER | wxALL, 4)

        b = wxButton(self, -1, "OK")
        h.Add(b, 0, wxALL, 4)
        EVT_BUTTON(self, b.GetId(), self.OnOK)

        b = wxButton(self, -1, "Cancel")
        h.Add(b, 0, wxALL, 4)
        EVT_BUTTON(self, b.GetId(), self.OnCancel)

        EVT_TEXT_ENTER(self, passId, self.KeyDown)
        EVT_TEXT_ENTER(self, keyId, self.KeyDown)
        EVT_TEXT_ENTER(self, lifeTimeId, self.KeyDown)
       
        self.SetSizer(sizer)
        self.SetAutoLayout(AG_TRUE)
        self.Fit()

    def GetInfo(self):
        return (self.passphraseText.GetValue(),
                self.lifetimeText.GetValue(),
                self.keyList.GetValue())

    def OnOK(self, event):
        self.EndModal(wxID_OK)

    def OnCancel(self, event):
        self.EndModal(wxID_CANCEL)

    def KeyDown(self, event):
        self.EndModal(wxID_OK)


class RepositoryBrowser(wxPanel):
    """
    A RepositoryBrowser provides the basic GUI for browsing certificates.

    It holds a list of certificates. When a cert is selected,
    the name and issuer appear in the dialog, along with the details of the cert.

    This browser supports the import/export/deletion of certs. It does not
    have more specific abilities with regards to the setting of default
    identity certificates, for instance. That functionality is delegated to
    a more specific dialog for handling id certs.
    """

    def __init__(self, parent, id, repo, certPred):
        """
        Create the RepositoryBrowser.

        repo - a CertificateRepository instance to browse.

        certPred - 1-argument callable which returns true 
        	when invoked with a certificate type we wish
                to browse.

        """

        wxPanel.__init__(self, parent, id)

        self.repo = repo
        self.certPred = certPred

        self.__build()

    def __build(self):
        """
        Construct the GUI.

        self.sizer: overall vertical sizer
        hboxTop: top row horizontal sizer
        vboxTop: top row vertical sizer for the import/export buttons
        hboxMid: middle row sizer
        vboxMidL: middle row, left column vbox
        vboxMidR: middle row, right column vbox
        """

        self.sizer = wxBoxSizer(wxVERTICAL)
        hboxTop = wxBoxSizer(wxHORIZONTAL)
        hboxMid = wxBoxSizer(wxHORIZONTAL)
        vboxTop = wxBoxSizer(wxVERTICAL)
        vboxMidL = wxBoxSizer(wxVERTICAL)
        vboxMidR = wxBoxSizer(wxVERTICAL)

        #
        # We want the various fields to have the same
        # background as the panel
        #

        bgcolor = self.GetBackgroundColour()

        #
        # Build the top row.
        #

        self.sizer.Add(hboxTop, 1, wxEXPAND)
        self.certList = wxListBox(self, -1, style = wxLB_SINGLE)
        
        certs = self.repo.FindCertificates(self.certPred)
        for cert in certs:
            print "cert is ", cert, cert.GetSubject()
            name = str(cert.GetSubject().CN)
            print "name is ", name
            self.certList.Append(name, cert)
        print "done"
        hboxTop.Add(self.certList, 1, wxEXPAND)
        EVT_LISTBOX(self, self.certList.GetId(), self.OnSelectCert)

        hboxTop.Add(vboxTop, 0, wxEXPAND)

        b = wxButton(self, -1, "Import...")
        EVT_BUTTON(self, b.GetId(), self.OnImport)
        vboxTop.Add(b, 0, wxEXPAND)
        # b.Enable(False)

        b = wxButton(self, -1, "Export...")
        EVT_BUTTON(self, b.GetId(), self.OnExport)
        vboxTop.Add(b, 0, wxEXPAND)
        # b.Enable(False)

        b = wxButton(self, -1, "Delete")
        EVT_BUTTON(self, b.GetId(), self.OnDelete)
        vboxTop.Add(b, 0, wxEXPAND)
        # b.Enable(False)

        #
        # Middle row
        #

        self.sizer.Add(hboxMid, 1, wxEXPAND)

        hboxMid.Add(vboxMidL, 1, wxEXPAND)
        t = wxStaticText(self, -1, "Certificate name")
        vboxMidL.Add(t, 0, wxEXPAND)

        self.nameText = wxTextCtrl(self, -1, style = wxTE_MULTILINE | wxTE_READONLY)
        vboxMidL.Add(self.nameText, 1, wxEXPAND)
        self.nameText.SetBackgroundColour(bgcolor)

        hboxMid.Add(vboxMidR, 1, wxEXPAND)
        t = wxStaticText(self, -1, "Issuer")
        vboxMidR.Add(t, 0, wxEXPAND)

        self.issuerText = wxTextCtrl(self, -1, style = wxTE_MULTILINE | wxTE_READONLY)
        vboxMidR.Add(self.issuerText, 1, wxEXPAND)
        self.issuerText.SetBackgroundColour(bgcolor)

        #
        # Bottom row
        #

        self.certText = wxTextCtrl(self, -1, style = wxTE_MULTILINE | wxTE_READONLY)
        self.sizer.Add(self.certText, 1, wxEXPAND)
        self.certText.SetBackgroundColour(bgcolor)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.Fit()

    def OnSelectCert(self, event):
        sel = self.certList.GetSelection()
        cert = self.certList.GetClientData(sel)
        print "Selected cert ", sel, cert

        self.nameText.Clear()
        self.issuerText.Clear()
        self.certText.Clear()

        self.nameText.AppendText(self.__formatNameForGUI(cert.GetSubject()))
        self.issuerText.AppendText(self.__formatNameForGUI(cert.GetIssuer()))
        self.certText.AppendText(self.__formatCertForGUI(cert))

        event = CertSelectedEvent(self.GetId(), cert)
        self.GetEventHandler().AddPendingEvent(event)

    def __formatNameForGUI(self, name):
        fmt = ''
        comps = name.get_name_components()
        comps.reverse()
        for id, val in comps:
            fmt += "%s = %s\n" % (id, val)
        return fmt

    def __formatCertForGUI(self, certObj):

        #
        # get the lowlevel cert object
        #

        return certObj.GetVerboseText()

    def OnImport(self, event):
        event = CertImportEvent(self.GetId())
        self.GetEventHandler().AddPendingEvent(event)

    def OnExport(self, event):
        event = CertExportEvent(self.GetId())
        self.GetEventHandler().AddPendingEvent(event)


    def OnDelete(self, event):
        event = CertDeleteEvent(self.GetId())
        self.GetEventHandler().AddPendingEvent(event)


class TrustedCertDialog(wxDialog):
    def __init__(self, parent, id, title, repo):
        wxDialog.__init__(self, parent, id, title, size = wxSize(400, 400))

        self.repo = repo

        sizer = wxBoxSizer(wxVERTICAL)
        pred = lambda c: c.GetMetadata("AG.CertificateManager.certType") == "trustedCA"
        cpanel = RepositoryBrowser(self, -1, self.repo, pred)
        sizer.Add(cpanel, 1, wxEXPAND)

        b = wxButton(self, -1, "OK")
        EVT_BUTTON(self, b.GetId(), self.OnOK)
        sizer.Add(b, 0, wxALIGN_CENTER)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

        EVT_CERT_SELECTED(self, self.OnCertSelected)
        EVT_CERT_IMPORT(self, self.OnCertImport)
        EVT_CERT_EXPORT(self, self.OnCertExport)
        EVT_CERT_DELETE(self, self.OnCertDelete)


    def OnCertSelected(self, event):
        print "Got cert sel ", event, event.cert

    def OnCertImport(self, event):
        print "Got import indlg"

    def OnCertExport(self, event):
        print "Got export "

    def OnCertDelete(self, event):
        print "Got delete "

    def OnOK(self, event):
        self.EndModal(wxOK)

class IdentityCertDialog(wxDialog):
    def __init__(self, parent, id, title, repo):
        wxDialog.__init__(self, parent, id, title, size = wxSize(400, 400))

        self.repo = repo

        sizer = wxBoxSizer(wxVERTICAL)
        pred = lambda c: c.GetMetadata("AG.CertificateManager.certType") == "identity"
        cpanel = RepositoryBrowser(self, -1, self.repo, pred)
        sizer.Add(cpanel, 1, wxEXPAND)

        b = wxButton(self, -1, "OK")
        EVT_BUTTON(self, b.GetId(), self.OnOK)
        sizer.Add(b, 0, wxALIGN_CENTER)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

        EVT_CERT_SELECTED(self, self.OnCertSelected)


    def OnCertSelected(self, event):
        print "Got cert sel ", event

    def OnOK(self, event):
        self.EndModal(wxOK)

