import time

import wx

from AccessGrid.Security.Utilities import GetCNFromX509Subject
from AccessGrid import Toolkit

from CertificateBrowserBase import CertificateBrowserBase
from CertificateViewer import CertificateViewer
from ImportCACertDialog import ImportCACertDialog

import ImportExportUtils

class CABrowser(CertificateBrowserBase):
    def __init__(self, parent, id, certMgr):
        CertificateBrowserBase.__init__(self, parent, id, certMgr)

    def _buildButtons(self, sizer):

        #
        # Buttons that are only valid when a cert is selected.
        #
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

        b = wx.Button(self, -1, "View Certificate")
        wx.EVT_BUTTON(self, b.GetId(), self.OnViewCertificate)
        sizer.Add(b, 0, wx.EXPAND)
        self.certOnlyButtons.append(b)

        b = wx.Button(self, -1, "Refresh")
        wx.EVT_BUTTON(self, b.GetId(), lambda event, self = self: self.Load())
        sizer.Add(b, 0, wx.EXPAND)

        for b in self.certOnlyButtons:
            b.Enable(0)

    def OnImport(self, event):
        """
        Import a CA certificate.

        """

        dlg = ImportCACertDialog(self, self.certMgr)
        ret = dlg.Run()

        if ret is None:
            dlg.Destroy()
            return

        certFile, signingPolicy = ret

        dlg.Destroy()

        ImportExportUtils.ImportCACertificate(self.certMgr, certFile, signingPolicy)
        self.Load()

    def OnDelete(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return


        dlg = wx.MessageDialog(self,
                              "Deleting a certificate is an irreversible operation.\n" +
                              "Really delete certificate for identity " +
                              cert.GetShortSubject() + "?",
                              "Really delete?",
                              style = wx.YES_NO | wx.NO_DEFAULT)
        ret = dlg.ShowModal()
        dlg.Destroy()

        if ret == wx.ID_NO:
            return

        self.certMgr.GetCertificateRepository().RemoveCertificate(cert)
        Toolkit.GetDefaultApplication().GetCertificateManagerUI().InitEnvironment()
        self.Load()

    def OnExport(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        dlg = ImportExportUtils.ExportCACertDialog(self, cert)
        dlg.ShowModal()
        dlg.Destroy()

    def OnCertSelected(self, event, cert):
        if cert is None:
            return

        for b in self.certOnlyButtons:
            b.Enable(1)

    def OnCertDeselected(self, event, cert):
        for b in self.certOnlyButtons:
            b.Enable(0)

    def OnCertActivated(self, event, cert):
        if cert is None:
            return

        dlg = CertificateViewer(self, -1, cert, self.certMgr)
        dlg.Show()

    def OnViewCertificate(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        name = GetCNFromX509Subject(cert.GetSubject())
        dlg = CertificateViewer(self, -1, cert, self.certMgr)
        dlg.Show()

    #
    # Overrides from superclass.
    #

    def _LoadCerts(self):
        return self.certMgr.GetCACerts()

    def _FormatCert(self, cert):
        subjName = cert.GetSubject()
        issuerName = cert.GetIssuer()
        subjStr = GetCNFromX509Subject(subjName)

        if subjName.as_der() == issuerName.as_der():
            issuerStr = "<self>"
        else:
            issuerStr = GetCNFromX509Subject(issuerName)
        
        valid = self.certMgr.CheckValidity(cert)

        return cert, [subjStr, issuerStr, valid]

    def _getListColumns(self):
        return ["Name", "Issuer", "Validity"]

    def _getListColumnWidths(self):
        return [wx.LIST_AUTOSIZE, wx.LIST_AUTOSIZE, wx.LIST_AUTOSIZE_USEHEADER]

