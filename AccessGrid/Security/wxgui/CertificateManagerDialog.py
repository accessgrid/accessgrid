import logging

import wx

from AccessGrid.Security.wxgui.ProxyBrowser import ProxyBrowser
from AccessGrid.Security.wxgui.IdentityBrowser import IdentityBrowser
from AccessGrid.Security.wxgui.CABrowser import CABrowser
from AccessGrid.Security.wxgui.CertificateStatusBrowser import CertificateStatusBrowser

class CertificateManagerDialog(wx.Dialog):
    def __init__(self, parent, id, title, certMgr, certMgrUI):
        wx.Dialog.__init__(self, parent, id, title, size = wx.Size(700, 400),
                          style= wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.certMgr = certMgr

        # Toplevel vsizer with a notebook and a hsizer with
        # window ops buttons.
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Build the notebook.
        self.notebook = wx.Notebook(self, -1)
        sizer.Add(self.notebook, 1, wx.EXPAND)

        self.identBrowser = IdentityBrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.identBrowser, "Certificates")

        self.proxyBrowser = ProxyBrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.proxyBrowser, "Proxy Certificates")

        self.caBrowser = CABrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.caBrowser, "Trusted CA Certificates")

        self.statusBrowser = CertificateStatusBrowser(self.notebook, -1, self.certMgr, certMgrUI)
        self.notebook.AddPage(self.statusBrowser, "Certificate Requests")

        # Default to certificate pane.
        self.notebook.SetSelection(0)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(hsizer, 0)

        b = wx.Button(self, -1, "Close")
        wx.EVT_BUTTON(self, b.GetId(), self.OnOK)
        sizer.Add(b, 0, wx.ALIGN_RIGHT)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

        wx.EVT_CLOSE(self, self.OnClose)

    def OnClose(self, event):
        self.Destroy()

    def OnOK(self, event):
        if self.IsModal():
            self.EndModal(wx.OK)
        else:
            self.Close(1)


class CertificateManagerPanel(wx.Panel):
    def __init__(self, parent, id, certMgr, certMgrUI):
        wx.Panel.__init__(self, parent, id, size = wx.Size(700, 400))

        self.certMgr = certMgr

        # Toplevel vsizer with a notebook and a hsizer with
        # window ops buttons.
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Build the notebook.
        self.notebook = wx.Notebook(self, -1)
        sizer.Add(self.notebook, 1, wx.EXPAND)

        self.identBrowser = IdentityBrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.identBrowser, "Certificates")

        self.proxyBrowser = ProxyBrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.proxyBrowser, "Proxy Certificates")

        self.caBrowser = CABrowser(self.notebook, -1, self.certMgr)
        self.notebook.AddPage(self.caBrowser, "Trusted CA Certificates")

        self.statusBrowser = CertificateStatusBrowser(self.notebook, -1, self.certMgr, certMgrUI)
        self.notebook.AddPage(self.statusBrowser, "Certificate Requests")

        # Default to certificate pane.
        self.notebook.SetSelection(0)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(hsizer, 0)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)


if __name__ == "__main__":

    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(logging.StreamHandler())

    pyapp = wx.PySimpleApp()

    import AccessGrid.Toolkit
    app = AccessGrid.Toolkit.WXGUIApplication()
    app.Initialize()

    d = CertificateManagerDialog(None, -1, "CMGR", app.GetCertificateManager(), app.GetCertificateManagerUI())
    
    d.Show(1)

    pyapp.SetTopWindow(d)

    pyapp.MainLoop()
    
