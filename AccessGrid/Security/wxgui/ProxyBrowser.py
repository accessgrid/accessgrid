
from wxPython.wx import *

from AccessGrid.Security.Utilities import GetCNFromX509Subject

from CertificateBrowserBase import CertificateBrowserBase
from CertificateViewer import CertificateViewer

import time
import os

class ProxyBrowser(CertificateBrowserBase):
    def __init__(self, parent, id, certMgr):
        CertificateBrowserBase.__init__(self, parent, id, certMgr)

    def _buildButtons(self, sizer):

        #
        # Buttons that are only valid when a cert is selected.
        #
        self.certOnlyButtons = []

        b = wxButton(self, -1, "Create")
        EVT_BUTTON(self, b.GetId(), self.OnCreate)
        sizer.Add(b, 0, wxEXPAND)

        b = wxButton(self, -1, "Destroy")
        EVT_BUTTON(self, b.GetId(), self.OnDestroy)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "View proxy")
        EVT_BUTTON(self, b.GetId(), self.OnViewCertificate)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Refresh display")
        EVT_BUTTON(self, b.GetId(), lambda event, self = self: self.Load())
        sizer.Add(b, 0, wxEXPAND)

        for b in self.certOnlyButtons:
            b.Enable(0)

    def OnCreate(self, event):
        print "Creating proxy"
        self.certMgr.CreateProxy()
        self.Load()

    def OnDestroy(self, event):

        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        dlg = wxMessageDialog(self,
                              "Really delete proxy for identity " +
                              cert.GetShortSubject() + "?",
                              "Really delete?",
                              style = wxYES_NO | wxNO_DEFAULT)

        ret = dlg.ShowModal()
        dlg.Destroy()

        if ret == wxID_NO:
            return

        #
        # Deleting a proxy is just a matter of deleting the file.
        #

        try:
            os.unlink(self.certMgr.GetProxyPath())
        except:
            log.exception("exception removing proxy certificate");

        self.Load()

    def OnCertSelected(self, event, cert):
        if cert is None:
            return

        for b in self.certOnlyButtons:
            b.Enable(1)

    def OnCertDeselected(self, event, cert):
        if cert is None:
            return

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

        if cert.IsExpired():
            validity = "Expired"

        elif not self.certMgr.VerifyCertificatePath(cert):
            validity = "Missing CA"

        else:
            #
            # Otherwise, return the remaining lifetime.
            #

            left = cert.GetNotValidAfter() - int(time.time())

            validity = ""
            if left > 86400:
                days = int(left / 86400)
                validity += "%dd " % (days)

                left = left % 86400

            hour = int(left / 3600)
            left = left % 3600

            min = int(left / 60)
            sec = left % 60

            validity += "%02d:%02d:%02d left" % (hour, min, sec)

        return cert, [name, issuer, validity]

    def _getListColumns(self):
        return ["Proxy for", "Issuer", "Validity"]

    def _getListColumnWidths(self):
        return [wxLIST_AUTOSIZE, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE_USEHEADER ]

