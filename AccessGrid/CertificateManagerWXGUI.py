"""
wxPython GUI code for the Certificate Manager.

This needs to be in a separate file because any attempt to import
wxPython.wx, even inside a try/except block, will result in a process
exit on Linux if the DISPLAY environment variable is not set.

"""

import time
import string

from OpenSSL_AG import crypto
from wxPython.wx import *

from CertificateManager import CertificateManagerUserInterface, utc2tuple

class CertificateManagerWXGUI(CertificateManagerUserInterface):
    """
    wxWindows-based user interfact to the certificate mgr.
    """

    def __init__(self):
        CertificateManagerUserInterface.__init__(self)

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
                                self.certificateManager.trustedCARepo)
        dlg.ShowModal()
        dlg.Destroy()

    def OpenIdentityCertDialog(self, event, win):
        dlg = TrustedCertDialog(win, -1, "View user identity certificates",
                                self.certificateManager.userCertRepo)
        dlg.ShowModal()
        dlg.Destroy()

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

        t = wxStaticText(self, -1, "Passphrase:")
        grid.Add(t, 0, wxALL, 4)

        self.passphraseText = wxTextCtrl(self, -1,
                                         style = wxTE_PASSWORD)
        grid.Add(self.passphraseText, 0, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Key size:")
        grid.Add(t, 0, wxALL, 4)

        self.keyList = wxComboBox(self, -1,
                                  style = wxCB_READONLY,
                                  choices = ["512", "1024", "2048", "4096"])
        self.keyList.SetSelection(1)
        grid.Add(self.keyList, 1, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Proxy lifetime (hours):")
        grid.Add(t, 0, wxALL, 4)

        self.lifetimeText = wxTextCtrl(self, -1, "8")
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

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Fit()

    def GetInfo(self):
        return (self.passphraseText.GetValue(),
                self.lifetimeText.GetValue(),
                self.keyList.GetValue())

    def OnOK(self, event):
        self.EndModal(wxID_OK)

    def OnCancel(self, event):
        self.EndModal(wxID_CANCEL)


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

    def __init__(self, parent, id, repo):
        """
        Create the RepositoryBrowser.

        repo - a CertificateRepository instance to browse.

        """

        wxPanel.__init__(self, parent, id)

        self.repo = repo

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
        
        certs = self.repo.GetCertificates()
        print certs
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
        b.Enable(False)

        b = wxButton(self, -1, "Export...")
        EVT_BUTTON(self, b.GetId(), self.OnExport)
        vboxTop.Add(b, 0, wxEXPAND)
        b.Enable(False)

        b = wxButton(self, -1, "Delete")
        EVT_BUTTON(self, b.GetId(), self.OnDelete)
        vboxTop.Add(b, 0, wxEXPAND)
        b.Enable(False)

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

    def __formatNameForGUI(self, name):
        fmt = ''
        comps = name.get_name_components()
        comps.reverse()
        for id, val in comps:
            fmt += "%s = %s\n" % (id, val)
        return fmt

    def __formatCertForGUI(self, certObj):
        fmt = ''
        #
        # get the lowlevel cert object
        #
        cert = certObj.cert
        fmt += "Certificate version: %s\n" % (cert.get_version())
        fmt += "Serial number: %s\n" % (cert.get_serial_number())

        notBefore = cert.get_not_before()
        notAfter = cert.get_not_after()

        fmt += "Not valid before: %s\n" % (time.strftime("%x %X", utc2tuple(notBefore)))
        fmt += "Not valid after: %s\n" % (time.strftime("%x %X", utc2tuple(notAfter)))

        (type, fp) = cert.get_fingerprint()
        fmt += "%s Fingerprint: %s\n"  % (type,
                                          string.join(map(lambda a: "%02X" % (a), fp), ":"))
        fmt += "Certificate location: %s\n" % (certObj.GetPath(),)
        fmt += "Private key location: %s\n" % (certObj.GetKeyPath(),)
        
        return fmt


    def OnImport(self, event):
        print "Import"

    def OnExport(self, event):
        print "Export"

    def OnDelete(self, event):
        print "Delete"

class TrustedCertDialog(wxDialog):
    def __init__(self, parent, id, title, repo):
        wxDialog.__init__(self, parent, id, title, size = wxSize(400, 400))

        self.repo = repo

        sizer = wxBoxSizer(wxVERTICAL)
        cpanel = RepositoryBrowser(self, -1, self.repo)
        sizer.Add(cpanel, 1, wxEXPAND)

        b = wxButton(self, -1, "OK")
        EVT_BUTTON(self, b.GetId(), self.OnOK)
        sizer.Add(b, 0, wxALIGN_CENTER)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def OnOK(self, event):
        self.EndModal(wxOK)

