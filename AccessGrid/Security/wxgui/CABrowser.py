import time

from wxPython.wx import *

from AccessGrid.Security.Utilities import GetCNFromX509Subject

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

        b = wxButton(self, -1, "View certificate")
        EVT_BUTTON(self, b.GetId(), self.OnViewCertificate)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Refresh")
        EVT_BUTTON(self, b.GetId(), lambda event, self = self: self.Load())
        sizer.Add(b, 0, wxEXPAND)

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


        dlg = wxMessageDialog(self,
                              "Deleting a certificate is an irreversible operation.\n" +
                              "Really delete certificate for identity " +
                              cert.GetShortSubject() + "?",
                              "Really delete?",
                              style = wxYES_NO | wxNO_DEFAULT)
        ret = dlg.ShowModal()
        dlg.Destroy()

        if ret == wxID_NO:
            return

        self.certMgr.GetCertificateRepository().RemoveCertificate(cert)
        self.certMgr.GetUserInterface().InitGlobusEnvironment()
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

        if subjName.get_der() == issuerName.get_der():
            issuerStr = "<self>"
        else:
            issuerStr = GetCNFromX509Subject(issuerName)
        
        valid = self.certMgr.CheckValidity(cert)

        return cert, [subjStr, issuerStr, valid]

    def _getListColumns(self):
        return ["Name", "Issuer", "Validity"]

    def _getListColumnWidths(self):
        return [wxLIST_AUTOSIZE, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE_USEHEADER]

