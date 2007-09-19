import time

import wx

from AccessGrid.Security.Utilities import GetCNFromX509Subject
from AccessGrid import Platform
from AccessGrid.ServiceProfile import ServiceProfile
from CertificateBrowserBase import CertificateBrowserBase
from CertificateViewer import CertificateViewer
from AccessGrid import Toolkit

import ImportExportUtils

from ImportIdentityCertDialog import ImportIdentityCertDialog

class DeleteCertificateDialog(wx.Dialog):
    """
    Dialog to use for asking the user if he wants to delete the cert.

    Adds a checkbox that allows the private key to not be deleted, though
    that is not the default.
    """

    def __init__(self, parent, msg):
        wx.Dialog.__init__(self, parent, -1, title = "Really delete?")

        sizer = wx.BoxSizer(wx.VERTICAL)

        for l in msg.split("\n"):
            l = l.strip()
            txt = wx.StaticText(self, -1, l)
            sizer.Add(txt, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, 10)

        self.checkbox = wx.CheckBox(self, -1, "Retain private key for certificate.")
        sizer.Add(self.checkbox, 0, wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        hs = wx.BoxSizer(wx.HORIZONTAL)

        b = wx.Button(self, wx.ID_YES, "Yes")
        hs.Add(b, 0, wx.ALL, 3)
        wx.EVT_BUTTON(self, wx.ID_YES, lambda e, self = self: self.EndModal(wx.ID_YES))

        b = wx.Button(self, wx.ID_NO, "No")
        hs.Add(b, 0, wx.ALL, 3)
        wx.EVT_BUTTON(self, wx.ID_NO, lambda e, self = self: self.EndModal(wx.ID_NO))

        sizer.Add(hs, 0, wx.TOP | wx.BOTTOM |  wx.ALIGN_CENTER, 10)

        self.SetSizer(sizer)
        self.Fit()

    def GetRetainPrivateKey(self):
        return self.checkbox.IsChecked()
        
class IdentityBrowser(CertificateBrowserBase):
    def __init__(self, parent, id, certMgr):
        CertificateBrowserBase.__init__(self, parent, id, certMgr)

    def _buildButtons(self, sizer):

        # Buttons that are only valid when a cert is selected.
        self.certOnlyButtons = []

        b = wx.Button(self, -1, "Import")
        wx.EVT_BUTTON(self, b.GetId(), self.OnImport)
        sizer.Add(b, 0, wx.EXPAND)

        b = wx.Button(self, -1, "Export")
        wx.EVT_BUTTON(self, b.GetId(), self.OnExport)
        sizer.Add(b, 0, wx.EXPAND)
        self.certOnlyButtons.append(b)

        b = wx.Button(self, -1, "Delete")
        wx.EVT_BUTTON(self, b.GetId(), self.OnDelete)
        sizer.Add(b, 0, wx.EXPAND)
        self.certOnlyButtons.append(b)

        b = wx.Button(self, -1, "Make Default")
        wx.EVT_BUTTON(self, b.GetId(), self.OnSetDefault)
        sizer.Add(b, 0, wx.EXPAND)
        self.defaultButton = b
        b.Enable(0)

        b = wx.Button(self, -1, "View Certificate")
        wx.EVT_BUTTON(self, b.GetId(), self.OnViewCertificate)
        sizer.Add(b, 0, wx.EXPAND)
        self.certOnlyButtons.append(b)

        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL , 3)

        self.exportServiceProfileButton = wx.Button(self, -1,
                                                   "Export Service Profile")
        wx.EVT_BUTTON(self, self.exportServiceProfileButton.GetId(),
                   self.OnExportServiceProfile)
        sizer.Add(self.exportServiceProfileButton, 0, wx.EXPAND)
        self.exportServiceProfileButton.Enable(0)
        
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL , 3)

        b = wx.Button(self, -1, "Refresh")
        wx.EVT_BUTTON(self, b.GetId(), lambda event, self = self: self.Load())
        sizer.Add(b, 0, wx.EXPAND)


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

        if certType == "PEM":
            impCert = ImportExportUtils.ImportPEMIdentityCertificate(self.certMgr, certFile, privateKeyFile)
        else:

            dlg = wx.MessageDialog(self,
                                  "Unknown certificate type in import."
                                  "Import failed",
                                  style = wx.OK)
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

        if ret == wx.ID_NO:
            return

        self.certMgr.GetCertificateRepository().RemoveCertificate(cert, dlg.GetRetainPrivateKey())
        Toolkit.GetDefaultApplication().GetCertificateManagerUI().InitEnvironment()
        self.Load()

    def OnSetDefault(self, event):

        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        self.certMgr.SetDefaultIdentity(cert)
        Toolkit.GetDefaultApplication().GetCertificateManagerUI().InitEnvironment()
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

        dlg = wx.FileDialog(self, "Export service profile",
                           dir, file,
                           "Service profiles|*.profile|All files|*.*",
                           wx.SAVE | wx.OVERWRITE_PROMPT)
        rc = dlg.ShowModal()
        if rc == wx.ID_OK:
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

        if self.certMgr.IsDefaultIdentityCert(cert):
            isDefault= "Y"
        else:
            isDefault = ""

        valid = self.certMgr.CheckValidity(cert)

        return cert, [type, subj, issuer, isDefault, valid]

    def _getListColumns(self):
        return ["Certificate Type", "Subject Name", "Issuer", "Default", "Validity"]

    def _getListColumnWidths(self):
        return [wx.LIST_AUTOSIZE_USEHEADER, wx.LIST_AUTOSIZE, wx.LIST_AUTOSIZE, wx.LIST_AUTOSIZE_USEHEADER, wx.LIST_AUTOSIZE]


if __name__ == "__main__":
    a = wx.PySimpleApp()
    dlg = DeleteCertificateDialog(None, "You can't undo this\n" +
                              "Really delete certificate for identity ?")
    rc = dlg.ShowModal()
    print rc
