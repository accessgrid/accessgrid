
from wxPython.wx import *

from AccessGrid.Security.Utilities import GetCNFromX509Subject

from CertificateBrowserBase import CertificateBrowserBase
from CertificateViewer import CertificateViewer


class ProxyBrowser(CertificateBrowserBase):
    def __init__(self, parent, id, certMgr):
        CertificateBrowserBase.__init__(self, parent, id, certMgr)

    def _buildButtons(self, sizer):

        b = wxButton(self, -1, "Create")
        EVT_BUTTON(self, b.GetId(), self.OnCreate)
        sizer.Add(b, 0, wxEXPAND)

        b = wxButton(self, -1, "Renew")
        EVT_BUTTON(self, b.GetId(), self.OnRenew)
        sizer.Add(b, 0, wxEXPAND)

        b = wxButton(self, -1, "Destroy")
        EVT_BUTTON(self, b.GetId(), self.OnDestroy)
        sizer.Add(b, 0, wxEXPAND)
        self.defaultButton = b

        b = wxButton(self, -1, "View proxy")
        EVT_BUTTON(self, b.GetId(), self.OnViewCertificate)
        sizer.Add(b, 0, wxEXPAND)

    def OnCreate(self, event):
        pass

    def OnRenew(self, event):
        pass

    def OnDestroy(self, event):
        pass

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

    #
    # Overrides from superclass.
    #

    def _LoadCerts(self):
        proxies = []
        try:
            proxyCert = self.certMgr.GetGlobusProxyCert()
            proxies.append(proxyCert)
        except:
            pass

        return proxies

    def _FormatCert(self, cert):
        name = GetCNFromX509Subject(cert.GetIssuer())

        #
        # Find the issuing cert, to show the issuer of the
        # proxy's identity.
        #
        
        issuers = self.certMgr.GetCertificateRepository().FindCertificatesWithSubject(str(cert.GetIssuer()))
        validIssuers = filter(lambda x: not x.IsExpired(), issuers)

        if validIssuers == []:
            if issuers == []:
                issuer = "<not found>"
            else:
                issuer = GetCNFromX509Subject(issuers[0].GetIssuer())
        else:
            issuer = GetCNFromX509Subject(validIssuers[0].GetIssuer())

        valid = self.certMgr.CheckValidity(cert)

        return cert, [name, issuer, valid]

    def _getListColumns(self):
        return ["Proxy for", "Issuer", "Validity"]

    def _getListColumnWidths(self):
        return [wxLIST_AUTOSIZE, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE]

