import time

from wxPython.wx import *

from AccessGrid.Security.Utilities import GetCNFromX509Subject
from AccessGrid import Platform
from AccessGrid.ServiceProfile import ServiceProfile
from CertificateBrowserBase import CertificateBrowserBase
from CertificateViewer import CertificateViewer

import ImportExportUtils

from ImportIdentityCertDialog import ImportIdentityCertDialog

class DeleteCertificateDialog(wxDialog):
    """
    Dialog to use for asking the user if he wants to delete the cert.

    Adds a checkbox that allows the private key to not be deleted, though
    that is not the default.
    """

    def __init__(self, parent, msg):
        wxDialog.__init__(self, parent, -1, title = "Really delete?")

        sizer = wxBoxSizer(wxVERTICAL)

        for l in msg.split("\n"):
            l = l.strip()
            txt = wxStaticText(self, -1, l)
            sizer.Add(txt, 0, wxEXPAND | wxTOP | wxRIGHT | wxLEFT, 10)

        self.checkbox = wxCheckBox(self, -1, "Retain private key for certificate.")
        sizer.Add(self.checkbox, 0, wxALIGN_LEFT | wxLEFT | wxRIGHT | wxTOP, 10)

        hs = wxBoxSizer(wxHORIZONTAL)

        b = wxButton(self, wxID_YES, "Yes")
        hs.Add(b, 0, wxALL, 3)
        EVT_BUTTON(self, wxID_YES, lambda e, self = self: self.EndModal(wxID_YES))

        b = wxButton(self, wxID_NO, "No")
        hs.Add(b, 0, wxALL, 3)
        EVT_BUTTON(self, wxID_NO, lambda e, self = self: self.EndModal(wxID_NO))

        sizer.Add(hs, 0, wxTOP | wxBOTTOM |  wxALIGN_CENTER, 10)

        self.SetSizer(sizer)
        self.Fit()

    def GetRetainPrivateKey(self):
        return self.checkbox.IsChecked()
        
class IdentityBrowser(CertificateBrowserBase):
    def __init__(self, parent, id, certMgr):
        CertificateBrowserBase.__init__(self, parent, id, certMgr)

    def _buildButtons(self, sizer):

        #
        # Buttons that are only valid when a cert is selected.
        #
        self.certOnlyButtons = []

        b = wxButton(self, -1, "Import")
        EVT_BUTTON(self, b.GetId(), self.OnImport)
        sizer.Add(b, 0, wxEXPAND)

        b = wxButton(self, -1, "Export")
        EVT_BUTTON(self, b.GetId(), self.OnExport)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Delete")
        EVT_BUTTON(self, b.GetId(), self.OnDelete)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Set as default")
        EVT_BUTTON(self, b.GetId(), self.OnSetDefault)
        sizer.Add(b, 0, wxEXPAND)
        self.defaultButton = b
        b.Enable(0)

        b = wxButton(self, -1, "View certificate")
        EVT_BUTTON(self, b.GetId(), self.OnViewCertificate)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND | wxALL , 3)

        self.exportServiceProfileButton = wxButton(self, -1,
                                                   "Export service profile")
        EVT_BUTTON(self, self.exportServiceProfileButton.GetId(),
                   self.OnExportServiceProfile)
        sizer.Add(self.exportServiceProfileButton, 0, wxEXPAND)
        self.exportServiceProfileButton.Enable(0)
        
        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND | wxALL , 3)

        b = wxButton(self, -1, "Refresh")
        EVT_BUTTON(self, b.GetId(), lambda event, self = self: self.Load())
        sizer.Add(b, 0, wxEXPAND)


        for b in self.certOnlyButtons:
            b.Enable(0)

    def OnImport(self, event):
        """
        Import a new identity certificate.
        """

        dlg = ImportIdentityCertDialog(self, self.certMgr)
        ret = dlg.Run()
        dlg.Destroy()

        if ret is None:
            return

        certType, certFile, privateKeyFile = ret

        if certType == "PKCS12":
            impCert = ImportExportUtils.ImportPKCS12IdentityCertificate(self.certMgr, certFile)
        elif certType == "PEM":
            impCert = ImportExportUtils.ImportPEMIdentityCertificate(self.certMgr, certFile, privateKeyFile)
        else:

            dlg = wxMessageDialog(self,
                                  "Unknown certificate type in import."
                                  "Import failed",
                                  style = wxOK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # TODO : bring up confirmation dialog?
        #

        self.Load()

    def OnExport(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        dlg = ImportExportUtils.ExportIDCertDialog(self, cert)
        dlg.ShowModal()
        dlg.Destroy()

    def OnDelete(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        dlg = DeleteCertificateDialog(self, 
                                      "Deleting a certificate is an irreversible operation.\n" +
                                      "Really delete certificate for identity " +
                                      cert.GetShortSubject() + "?")
        
        ret = dlg.ShowModal()

        retain = dlg.GetRetainPrivateKey()
        
        dlg.Destroy()

        if ret == wxID_NO:
            return

        self.certMgr.GetCertificateRepository().RemoveCertificate(cert, dlg.GetRetainPrivateKey())
        self.certMgr.GetUserInterface().InitGlobusEnvironment()
        self.Load()

    def OnSetDefault(self, event):

        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        self.certMgr.SetDefaultIdentity(cert)
        self.certMgr.GetUserInterface().InitGlobusEnvironment()
        self.Load()

    def OnCertSelected(self, event, cert):
        if cert is None:
            return

        for b in self.certOnlyButtons:
            b.Enable(1)

        if self.certMgr.IsDefaultIdentityCert(cert):
            self.defaultButton.Enable(0)
        else:
            self.defaultButton.Enable(1)

        self.exportServiceProfileButton.Enable(cert.IsServiceCert() is not None)
        
    def OnCertDeselected(self, event, cert):
        if cert is None:
            return

        for b in self.certOnlyButtons:
            b.Enable(0)
        self.exportServiceProfileButton.Enable(0)

        self.defaultButton.Enable(0)

    def OnCertActivated(self, event, cert):
        if cert is None:
            return

        dlg = CertificateViewer(self, -1, cert, self.certMgr)
        dlg.Show()

    def OnViewCertificate(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        dlg = CertificateViewer(self, -1, cert, self.certMgr)
        dlg.Show()

    def OnExportServiceProfile(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        svcInfo = cert.IsServiceCert()

        if svcInfo is None:
            return

        dn = str(cert.GetSubject())
        serviceName, hostname = svcInfo
        
        print "Export a service profile for ", serviceName, dn
        profile = ServiceProfile(serviceName,
                                 authType = "x509",
                                 subject = dn)

        dir = Platform.Config.UserConfig.instance().GetServicesDir()
        file = "%s.profile" % (serviceName)

        dlg = wxFileDialog(self, "Export service profile",
                           dir, file,
                           "Service profiles|*.profile|All files|*.*",
                           wxSAVE | wxOVERWRITE_PROMPT)
        rc = dlg.ShowModal()
        if rc == wxID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            try:
                print "Exporting to ", path
                profile.Export(path)
            except:
                log.exception("Failure exporting profile to %s", path)
                ErrorDialog(self, "Cannot export service profile",
                            "Cannot export service profile")

        else:
            dlg.Destroy()
        

    #
    # Overrides from superclass.
    #

    def _LoadCerts(self):
        return self.certMgr.GetIdentityCerts()

    def _FormatCert(self, cert):

        if cert.IsServiceCert():
            type = "Service"
        elif cert.IsHostCert():
            type = "Host"
        else:
            type = "Identity"


        subj = GetCNFromX509Subject(cert.GetSubject())
        issuer = GetCNFromX509Subject(cert.GetIssuer())

        proxyValid = ""

        if self.certMgr.IsDefaultIdentityCert(cert):
            isDefault= "Y"

            #
            # If this is the default identity cert,
            # we might have a proxy. Note that in future
            # when we may have multiple valid proxies, this
            # test will have to move out of here. It's here
            # as a currently-valid optimization.
            #

            proxyValid = self._TestGlobusProxy(cert)
            
        else:
            isDefault = ""

        valid = self.certMgr.CheckValidity(cert)

        return cert, [type, subj, issuer, isDefault, valid, proxyValid]

    def _TestGlobusProxy(self, defaultCert):

        try:
            proxyCert = self.certMgr.GetGlobusProxyCert()

        except:
            return "Missing"

        if not proxyCert.IsGlobusProxy():
            return "Not a proxy"

        proxyIssuer = proxyCert.GetIssuer()
        idSubject = defaultCert.GetSubject()
        if proxyIssuer.get_der() != idSubject.get_der():
            return "Proxy for other id"

        #
        # Check to see if the proxy cert has expired.
        #

        if proxyCert.IsExpired():
            return "Expired"

        if not self.certMgr.VerifyCertificatePath(proxyCert):
            return "Missing CA"

        #
        # Otherwise, return the remaining lifetime.
        #

        left = proxyCert.GetNotValidAfter() - int(time.time())

        out = ""
        if left > 86400:
            days = int(left / 86400)
            out += "%dd " % (days)

            left = left % 86400

        hour = int(left / 3600)
        left = left % 3600

        min = int(left / 60)
        sec = left % 60

        out += "%02d:%02d:%02d left" % (hour, min, sec)

        return out

    def _getListColumns(self):
        return ["Certificate Type", "Subject Name", "Issuer", "Default", "Validity", "Proxy status"]

    def _getListColumnWidths(self):
        return [wxLIST_AUTOSIZE_USEHEADER, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE_USEHEADER, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE_USEHEADER]


if __name__ == "__main__":
    a = wxPySimpleApp()
    dlg = DeleteCertificateDialog(None, "You can't undo this\n" +
                              "Really delete certificate for identity ?")
    rc = dlg.ShowModal()
    print rc
