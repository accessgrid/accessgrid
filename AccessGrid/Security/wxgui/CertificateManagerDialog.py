import logging

from wxPython.wx import *

from AccessGrid.Security.wxgui.ProxyBrowser import ProxyBrowser
from AccessGrid.Security.wxgui.IdentityBrowser import IdentityBrowser
from AccessGrid.Security.wxgui.CABrowser import CABrowser
from AccessGrid.Security.wxgui.CertificateStatusBrowser import CertificateStatusBrowser

class CertificateManagerDialog(wxDialog):
    def __init__(self, parent, id, title, certMgr):
        wxDialog.__init__(self, parent, id, title, size = wxSize(700, 400),
                          style= wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER)

        self.certMgr = certMgr

        #
        # Toplevel vsizer with a notebook and a hsizer with
        # window ops buttons.
        #

        sizer = wxBoxSizer(wxVERTICAL)

        #
        # Build the notebook.
        #

        self.notebook = wxNotebook(self, -1)
        sizer.Add(self.notebook, 1, wxEXPAND)

        self.proxyBrowser = ProxyBrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.proxyBrowser, "Globus proxies")

        self.identBrowser = IdentityBrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.identBrowser, "Certificates")

        self.caBrowser = CABrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.caBrowser, "Trusted CA Certificates")

        self.statusBrowser = CertificateStatusBrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.statusBrowser, "Certificate Requests")

        #
        # Legacy ones
        #

        # self.idBrowser = RepositoryBrowser(self.notebook, -1, self.certMgr, RepositoryBrowser.TYPE_IDENTITY)
        # self.notebook.AddPage(self.idBrowser, "Personal")
        
        # self.caBrowser = RepositoryBrowser(self.notebook, -1, self.certMgr, RepositoryBrowser.TYPE_CA)
        # self.notebook.AddPage(self.caBrowser, "Authorities")

        hsizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(hsizer, 0)

        b = wxButton(self, -1, "Close")
        EVT_BUTTON(self, b.GetId(), self.OnOK)
        hsizer.Add(b, 0, wxALIGN_RIGHT | wxEXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

        #EVT_CERT_SELECTED(self.browser, self.OnCertSelected)
        #EVT_CERT_IMPORT(self.browser, self.OnCertImport)
        #EVT_CERT_EXPORT(self.browser, self.OnCertExport)
        #EVT_CERT_DELETE(self.browser, self.OnCertDelete)

        EVT_CLOSE(self, self.OnClose)

    def OnClose(self, event):
        self.Destroy()

    def OnOK(self, event):
        if self.IsModal():
            self.EndModal(wxOK)
        else:
            self.Close(1)


if __name__ == "__main__":

    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(logging.StreamHandler())

    pyapp = wxPySimpleApp()

    import AccessGrid.Toolkit
    app = AccessGrid.Toolkit.WXGUIApplication()
    app.Initialize()
#    app.GetCertificateManager().InitEnvironment()

#    id = app.GetCertificateManager().GetDefaultIdentity()
#    print "id is ", id.GetSubject()

    d = CertificateManagerDialog(None, -1, "CMGR", app.GetCertificateManager())
    
    d.Show(1)

    pyapp.SetTopWindow(d)

    pyapp.MainLoop()
    
