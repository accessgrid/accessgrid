#-----------------------------------------------------------------------------
# Name:        CertificateManagerWXGUI.py
# Purpose:     Cert management code = WX-based GUI.
#
# Author:      Robert Olson
#
# Created:     2003
# RCS-ID:      $Id: CertificateManagerWXGUI.py,v 1.17 2003-08-19 19:35:03 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
wxPython GUI code for the Certificate Manager.

This needs to be in a separate file because any attempt to import
wxPython.wx, even inside a try/except block, will result in a process
exit on Linux if the DISPLAY environment variable is not set.

"""

import time
import string
import logging
import os
import os.path
import re
import shutil

log = logging.getLogger("AG.CertificateManagerWXGUI")

from OpenSSL_AG import crypto
from wxPython.wx import *
from AccessGrid.Toolkit import AG_TRUE, AG_FALSE
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog

from AccessGrid import CertificateManager
from AccessGrid import CertificateRepository
from AccessGrid.CertificateRequestTool import CertificateRequestTool, CertificateStatusDialog
from AccessGrid.CRSClient import CRSClient

#
# Custom event types for the cert browser.
#

CERTSELECTED = wxNewEventType()
CERTIMPORT = wxNewEventType()
CERTEXPORT = wxNewEventType()
CERTDELETE = wxNewEventType()
CERTSETDEFAULT = wxNewEventType()

def EVT_CERT_SELECTED(window, fun):
    window.Connect(-1, -1, CERTSELECTED, fun)

def EVT_CERT_IMPORT(window, fun):
    window.Connect(-1, -1, CERTIMPORT, fun)

def EVT_CERT_EXPORT(window, fun):
    window.Connect(-1, -1, CERTEXPORT, fun)

def EVT_CERT_DELETE(window, fun):
    window.Connect(-1, -1, CERTDELETE, fun)

def EVT_CERT_SET_DEFAULT(window, fun):
    window.Connect(-1, -1, CERTSETDEFAULT, fun)

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
    def __init__(self, id, cert):
        self.cert = cert
        wxPyCommandEvent.__init__(self, self.eventType, id)
    def Clone( self ):
        self.__class__( self.GetId() )
        
class CertDeleteEvent(wxPyCommandEvent):
    eventType = CERTDELETE
    def __init__(self, id, cert):
        self.cert = cert
        wxPyCommandEvent.__init__(self, self.eventType, id)
    def Clone( self ):
        self.__class__( self.GetId() )
        
class CertSetDefaultEvent(wxPyCommandEvent):
    eventType = CERTSETDEFAULT
    def __init__(self, id, cert):
        self.cert = cert
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

        i = wxNewId()
        certMenu.Append(i, "Request a certificate...")
        EVT_MENU(win, i,
                 lambda event, win=win, self=self: self.OpenCertRequestDialog(event, win))

        i = wxNewId()
        certMenu.Append(i, "View pending requests...")
        EVT_MENU(win, i,
                 lambda event, win=win, self=self: self.OpenPendingRequestsDialog(event, win))

        return certMenu

    def OpenTrustedCertDialog(self, event, win):
        dlg = TrustedCertDialog(win, -1, "View trusted certificates",
                                self.certificateManager)
        dlg.ShowModal()
        dlg.Destroy()

    def OpenIdentityCertDialog(self, event, win):
        dlg = IdentityCertDialog(win, -1, "View user identity certificates",
                                self.certificateManager)
        dlg.ShowModal()
        dlg.Destroy()

    def OpenCertRequestDialog(self, event, win):
        self.RunCertificateRequestTool(win)

    def OpenPendingRequestsDialog(self, event, win):
        self.RunCertificateStatusTool(win)

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

        self.RunCertificateRequestTool()
        
        return 1

    def RunCertificateRequestTool(self, win = None):
        reqTool = CertificateRequestTool(win,
                                         certificateType = 'IDENTITY',
                                         createIdentityCertCB = self.CreateCertificateRequestCB)
        reqTool.Destroy()
    
    def RunCertificateStatusTool(self, win = None):
        statTool = CertificateStatusDialog(win, -1,
                                           "View certificate status")
        statTool.ShowModal()
        statTool.Destroy()

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
            return 0

        #
        # See if we really need to have a proxy.
        #

        if not ident.HasEncryptedPrivateKey():
            #
            # We're using an unencrypted private key; proxies unnecessary.
            #

            return 1

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
            certificateRequest.SetMetadata("AG.CertificateManager.requestURL",
                                           submitServerURL)
            certificateRequest.SetMetadata("AG.CertificateManager.creationTime",
                                           str(int(time.time())))
            
            
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

    TYPE_IDENTITY = "identity"
    TYPE_CA = "ca"
    def __init__(self, parent, id, certMgr, browserType):
        """
        Create the RepositoryBrowser.

        certMgr - the certificate manager instance for this browser.

        browerType - either TYPE_IDENTITY (for browsing identity certs)
        	or TYPE_CA (for browsing trusted CA certs)

        """

        wxPanel.__init__(self, parent, id)

        if browserType == self.TYPE_IDENTITY:
            self.certPred = lambda c: c.GetMetadata("AG.CertificateManager.certType") == "identity"
        elif browserType == self.TYPE_CA:
            self.certPred = lambda c: c.GetMetadata("AG.CertificateManager.certType") == "trustedCA"
        else:
            raise RuntimeError, "Invalid type %s passed to RepostiroyBrowser constructor" % (browserType)
            
        self.browserType = browserType
        self.certMgr = certMgr
        self.repo = certMgr.GetCertificateRepository()

        self.__build()
        self.LoadCerts()

    def LoadCerts(self):
        """
        Refresh the certificate list from the repository.
        """

        selName = None
        sel = self.certList.GetSelection()
        if sel >= 0:
            cert, isDefault = self.certList.GetClientData(sel)
            selName = str(cert.GetSubject())
            del cert
            
        self.certList.Clear()
        self.ClearPerCertInfo()

        idx = 0
        certs = self.repo.FindCertificates(self.certPred)
        for cert in certs:
            print "cert is ", cert, cert.GetSubject()
            name = str(cert.GetSubject().CN)
            print "name is ", name

            #
            # Handle default identity case, if we're an identity browser.
            #

            isDefault = 0
            if self._IsIdentityBrowser():
                if self.certMgr.IsDefaultIdentityCert(cert):
                    log.debug("Cert %s is default", name)
                    name = "(DEFAULT) %s" % (name,)
                    isDefault = 1
                              
            self.certList.Append(name, (cert, isDefault))

            if selName == str(cert.GetSubject()):
                self.certList.SetSelection(idx, 1)
                self._UpdateCertInfo(cert, isDefault)

            idx += 1
        print "done"
        

    def _IsIdentityBrowser(self):
        return self.browserType == self.TYPE_IDENTITY

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
        
        hboxTop.Add(self.certList, 1, wxEXPAND)
        EVT_LISTBOX(self, self.certList.GetId(), self.OnSelectCert)

        hboxTop.Add(vboxTop, 0, wxEXPAND)

        #
        # If we're browsing identity certs, we have a set as default option.
        #
        

        if self._IsIdentityBrowser():
            b = wxButton(self, -1, "Set as default identity")
            EVT_BUTTON(self, b.GetId(), self.OnSetDefaultIdentity)
            vboxTop.Add(b, 0, wxEXPAND)
            b.Enable(False)
            self.buttonSetDefault = b

        b = wxButton(self, -1, "Import...")
        EVT_BUTTON(self, b.GetId(), self.OnImport)
        vboxTop.Add(b, 0, wxEXPAND)
        self.buttonImport = b
        # b.Enable(False)

        
        # b = wxButton(self, -1, "Export...")
        # EVT_BUTTON(self, b.GetId(), self.OnExport)
        # vboxTop.Add(b, 0, wxEXPAND)
        # # b.Enable(False)
        # self.buttonExport = b

        b = wxButton(self, -1, "Delete")
        EVT_BUTTON(self, b.GetId(), self.OnDelete)
        vboxTop.Add(b, 0, wxEXPAND)
        self.buttonDelete = b
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

    def OnSetDefaultIdentity(self, event):
        log.debug("Set default identity")

        #
        # Find selected cert and pass it in the event.
        #

        sel = self.certList.GetSelection()
        cert, isDefault = self.certList.GetClientData(sel)

        event = CertSetDefaultEvent(self.GetId(), cert)
        self.GetEventHandler().AddPendingEvent(event)
        

    def ClearPerCertInfo(self):
        self.nameText.Clear()
        self.issuerText.Clear()
        self.certText.Clear()

    def OnSelectCert(self, event):
        sel = self.certList.GetSelection()
        cert, isDefault = self.certList.GetClientData(sel)
        print "Selected cert ", sel, cert

        self._UpdateCertInfo(cert, isDefault)

    def _UpdateCertInfo(self, cert, isDefault):
        """
        Update the gui fields for the selected cert.
        """
        
        if self._IsIdentityBrowser():
            if isDefault:
                self.buttonSetDefault.Enable(0)
            else:
                self.buttonSetDefault.Enable(1)

        self.ClearPerCertInfo()

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
        sel = self.certList.GetSelection()
        if sel >= 0:
            cert, isDefault = self.certList.GetClientData(sel)
        else:
            cert = None
            
        event = CertExportEvent(self.GetId(), cert)
        self.GetEventHandler().AddPendingEvent(event)


    def OnDelete(self, event):
        sel = self.certList.GetSelection()
        if sel >= 0:
            cert, isDefault = self.certList.GetClientData(sel)
        else:
            cert = None
            
        event = CertDeleteEvent(self.GetId(), cert)
        self.GetEventHandler().AddPendingEvent(event)


class TrustedCertDialog(wxDialog):
    def __init__(self, parent, id, title, certMgr):
        wxDialog.__init__(self, parent, id, title, size = wxSize(400, 400))

        self.certMgr = certMgr

        sizer = wxBoxSizer(wxVERTICAL)
        self.browser = cpanel = RepositoryBrowser(self, -1, self.certMgr, RepositoryBrowser.TYPE_CA)
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


    def OnCertImport(self, event):
        """
        Import a new CA certificate.

        Bring up a file browser for the certificate file.
        Then bring one up for the signing policy.

        Import to repo.
        """

        dlg = wxFileDialog(None, "Choose a trusted CA certificate file",
                           defaultDir = "",
                           wildcard = "Trusted cert files (*.o)|*.0|PEM Files (*.pem)|*.pem|All files|*",
                           style = wxOPEN)
        rc = dlg.ShowModal()

        if rc != wxID_OK:
            dlg.Destroy()
            return

        dir = dlg.GetDirectory()
        file = dlg.GetFilename()

        log.debug("Chose file=%s dir=%s", file, dir)

        path = os.path.join(dir, file)

        root, ext = os.path.splitext(file)
        sp = os.path.join(dir, "%s.signing_policy" % (root))
        if os.path.isfile(sp):
            dlg.SetFilename(sp)
        else:
            dlg.SetFilename("")
        dlg.SetWildcard("Signing policy files (*.signing_policy)|*.signing_policy|All files|*")

        rc = dlg.ShowModal()
        if rc == wxID_OK:
            spPath = dlg.GetPath()
            log.debug("Got signing policy %s", spPath)
        else:
            spPath = None

        #
        # Open file and scan for cetificate and key info.
        #

        certRE = re.compile("-----BEGIN CERTIFICATE-----")

        try:
            fh = open(path)

            validCert = 0
            
            for l in fh:
                if certRE.search(l):
                    validCert = 1
                    break
            fh.close()
            log.debug("scan complete, validCert=%s", validCert)

        except IOError:
            log.error("Could not open certificate file %s", path)
            dlg.Destroy()
            dlg = wxMessageDialog(None,
                                  "Could not open certificate file %s." % (path),
                                  "File error",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
            
        except:
            log.exception("Unexpected error opening certificate file %s", path)
            dlg.Destroy()
            dlg = wxMessageDialog(None,
                                  "Unexpected error opening certificate file %s." % (path),
                                  "File error",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # Test to see if we had a valid PEM-formatted certificate.
        #

        if not validCert:
            log.error("BEGIN CERTIFICATE not found in %s", path)
            dlg.Destroy()
            dlg = wxMessageDialog(None,
                                  "File %s does not appear to contain a PEM-encoded certificate." % (path),
                                  "File error",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg.Destroy()

        try:

            impCert = self.certMgr.ImportCACertificatePEM(self.certMgr.GetCertificateRepository(),
                                                          path)
            log.debug("Imported identity %s", str(impCert.GetSubject()))

            if spPath is not None and os.path.isfile(spPath):
                log.debug("Copying signing policy %s", spPath)
                shutil.copyfile(spPath,
                                impCert.GetFilePath("signing_policy"))
                
            self.certMgr.GetUserInterface().InitGlobusEnvironment()
            self.browser.LoadCerts()

        except:
            log.exception("Error importing certificate from %s", path)
            dlg = wxMessageDialog(None, "Error occurred during certificate import.",
                                  "Error on import",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
            
    def OnCertExport(self, event):
        print "Got export "

    def OnCertDelete(self, event):
        cert = event.cert
        print "Got delete ", cert
        if cert is None:
            return

        print "Delete ", cert.GetSubject()

        isDefault = self.certMgr.IsDefaultIdentityCert(cert)
        
        self.certMgr.GetCertificateRepository().RemoveCertificate(cert)
        self.certMgr.GetUserInterface().InitGlobusEnvironment()

        self.browser.LoadCerts()

    def OnCertSelected(self, event):
        print "Got cert sel ", event, event.cert

    def OnCertExport(self, event):
        print "Got export "

    def OnOK(self, event):
        self.EndModal(wxOK)

class IdentityCertDialog(wxDialog):
    def __init__(self, parent, id, title, certMgr):
        wxDialog.__init__(self, parent, id, title, size = wxSize(400, 400))

        self.certMgr = certMgr

        sizer = wxBoxSizer(wxVERTICAL)
        self.browser = cpanel = RepositoryBrowser(self, -1, self.certMgr, RepositoryBrowser.TYPE_IDENTITY)
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
        EVT_CERT_SET_DEFAULT(self, self.OnCertSetDefault)

    def OnCertSetDefault(self, event):
        cert = event.cert
        print "Got set default ", cert.GetSubject()
        self.certMgr.SetDefaultIdentity(cert)
        self.certMgr.GetUserInterface().InitGlobusEnvironment()
        self.browser.LoadCerts()

    def OnCertSelected(self, event):
        print "Got cert sel ", event, event.cert

    def OnCertImport(self, event):
        """
        Import a new identity certificate.

        Bring up a file browser for the certificate file.
        Check to see if it has a key embedded in it. If not,
        bring up a file browser for the key.
        Check if key is encrypted, if so, prompt for passphrase.

        Import to repo.
        """

        dlg = wxFileDialog(None, "Choose a certificate file",
                           defaultDir = "",
                           wildcard = "PEM Files (*.pem)|*.pem|All files|*",
                           style = wxOPEN)
        rc = dlg.ShowModal()

        if rc != wxID_OK:
            dlg.Destroy()
            return

        dir = dlg.GetDirectory()
        file = dlg.GetFilename()

        log.debug("Chose file=%s dir=%s", file, dir)

        path = os.path.join(dir, file)

        #
        # Open file and scan for cetificate and key info.
        #

        certRE = re.compile("-----BEGIN CERTIFICATE-----")
        keyRE = re.compile("-----BEGIN RSA PRIVATE KEY-----")

        try:
            fh = open(path)

            validCert = validKey = 0
            
            for l in fh:
                if not validCert and certRE.search(l):
                    validCert = 1
                    if validKey:
                        break
                if not validKey and keyRE.search(l):
                    validKey = 1
                    if validCert:
                        break
            fh.close()
            log.debug("scan complete, validKey=%s validCert=%s", validKey, validCert)

        except IOError:
            log.error("Could not open certificate file %s", path)
            dlg.Destroy()
            dlg = wxMessageDialog(None,
                                  "Could not open certificate file %s." % (path),
                                  "File error",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
            
        except:
            log.exception("Unexpected error opening certificate file %s", path)
            dlg.Destroy()
            dlg = wxMessageDialog(None,
                                  "Unexpected error opening certificate file %s." % (path),
                                  "File error",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # Test to see if we had a valid PEM-formatted certificate.
        #

        if not validCert:
            log.error("BEGIN CERTIFICATE not found in %s", path)
            dlg.Destroy()
            dlg = wxMessageDialog(None,
                                  "File %s does not appear to contain a PEM-encoded certificate." % (path),
                                  "File error",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # We've got our cert. See if we need to ask for a private key.
        #

        if validKey:
            #
            # There was a key in the cert file.
            #

            kfile = file
            kdir = dir
        else:
            #
            # Try to guess a default.
            #

            kfile = ""
            m = re.search(r"^(.*)cert\.pem$", file)
            print "regexp search returns ", m
            if m:
                kfile = "%skey.pem" % (m.group(1))
                print "Trying ", kfile
                if not os.path.isfile(os.path.join(dir, kfile)):
                    kfile = ""

            dlg.SetFilename(kfile)
            dlg.SetMessage("Select the file containing the private key for this certificate.")
            rc = dlg.ShowModal()

            if rc != wxID_OK:
                return

            kfile = dlg.GetFilename();
            kdir = dlg.GetDirectory();

        kpath = os.path.join(kdir, kfile)
        log.debug("Key location: %s", kpath)

        dlg.Destroy()

        try:
            cb = self.certMgr.GetUserInterface().GetPassphraseCallback("Private key passphrase",
                                                                     "Enter the passphrase to your private key.")
            impCert = self.certMgr.ImportIdentityCertificatePEM(self.certMgr.GetCertificateRepository(),
                                                                 path, kpath, cb)
            log.debug("Imported identity %s", str(impCert.GetSubject()))
            self.browser.LoadCerts()

        except:
            log.exception("Error importing certificate from %s keyfile %s", path, kpath)
            dlg = wxMessageDialog(None, "Error occurred during certificate import.",
                                  "Error on import",
                                  style = wxOK | wxICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
            
                      
        #
        # Check to see if we have the CA cert for the issuer of this cert.
        #

        if not self.certMgr.VerifyCertificatePath(impCert):
            log.warn("can't verify issuer")
            dlg = wxMessageDialog(None, "Cannot verify the certificate path for \n" +
                                  str(impCert.GetSubject()) + "\n"
                                  "This certificate may not be usable until the \n" +
                                  "appropriate CA certificates are imported. At the least,\n" +
                                  "the certificate for this CA must be imported:\n" +
                                  str(impCert.GetIssuer()) + "\n" +
                                  "It might be found in a file %s.0." % (impCert.GetIssuer().get_hash()),
                                  "Cannot verify certificate path")
            dlg.ShowModal()
            dlg.Destroy()

    def OnCertExport(self, event):
        print "Got export "

    def OnCertDelete(self, event):
        cert = event.cert
        print "Got delete ", cert
        if cert is None:
            return

        print "Delete ", cert.GetSubject()

        isDefault = self.certMgr.IsDefaultIdentityCert(cert)
        
        self.certMgr.GetCertificateRepository().RemoveCertificate(cert)

        #
        # We've deleted our default identity; arbitrarily assign a new one.
        # User can pick a different one if he wants.
        #

        if isDefault:
            idCerts = self.certMgr.GetIdentityCerts()
            if len(idCerts) > 0:
                self.certMgr.SetDefaultIdentity(idCerts[0])
                self.certMgr.GetUserInterface().InitGlobusEnvironment()

        self.browser.LoadCerts()
        

    def OnCertSelected(self, event):
        print "Got cert sel ", event

    def OnOK(self, event):
        self.EndModal(wxOK)

