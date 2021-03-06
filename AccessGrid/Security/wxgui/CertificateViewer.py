import wx

import os

from AccessGrid.Security.Utilities import GetCNFromX509Subject

class CertificateViewerPanel(wx.Panel):
    """
    Panel subclass that incorporates the majority of the
    certificate viewer code.

    Contains a notebook with two views: a general view showing all
    of the certificate information, and a certification path view, showing
    the available certificates form the root down to certificate we're
    viewing.
    """
    
    def __init__(self, parent, id, cert, certMgr):
        wx.Panel.__init__(self, parent, id, style = 0)

        self.cert = cert
        self.certMgr = certMgr

        self.__build()

        # self.htmlWindow.SetPage(cert.GetVerboseHtml())

        #
        # Set up text styles.
        #

        defaultPoints = self.text.GetFont().GetPointSize()
        boldFont = wx.Font(defaultPoints, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.bold = bold = wx.TextAttr()
        self.bold.SetFont(boldFont)

        normalFont = wx.Font(defaultPoints, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.normal = normal = wx.TextAttr()
        self.normal.SetFont(normalFont)

        hdrFont = wx.Font(defaultPoints + 4, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.hdr = hdr = wx.TextAttr()
        self.hdr.SetFont(hdrFont)

        name = GetCNFromX509Subject(cert.GetSubject())

        #
        # Write cert info into text.
        #
        self.text.SetDefaultStyle(hdr)
        self.text.AppendText(name + "\n\n")
        
        self._writeValue("Validity", self.certMgr.CheckValidity(cert))
        self.text.AppendText("\n")
        
        self._writeValue("Subject", str(cert.GetSubject()))
        self._writeValue("Issuer", str(cert.GetIssuer()))
        self.text.AppendText("\n")

        self._writeValue("Not valid before", cert.GetNotValidBeforeText())
        self._writeValue("Not valid after", cert.GetNotValidAfterText())
        self.text.AppendText("\n")

        self._writeValue("Version", cert.GetVersion())
        self._writeValue("Serial number", cert.GetSerialNumber())
        fptype, fp = cert.GetFingerprint()
        self._writeValue(fptype + " Fingerprint", fp)

        self.text.AppendText("\n")
        self._writeValue("Certificate location", cert.GetPath())
        pkloc =  cert.GetKeyPath()
        if pkloc and os.access(pkloc, os.R_OK):
            self._writeValue("Private key location", pkloc)

        self._writeValue("Modulus", cert.GetModulus())
        self._writeValue("Modulus hash", cert.GetModulusHash())

        self.text.SetInsertionPoint(0)

        path = self.certMgr.GetCertificatePath(cert)

        #
        # Reverse path, then build tree widget (so that
        # the root is the root of the cert path.
        #

        path.reverse()

        #
        # Check to see if head of path is self-signed; if it is not,
        # we are missing the issuing certificate. In that case,
        # add the issuer name, but make it greyed out.
        #

        cert = path[0]

        if cert.GetSubject().as_der() == cert.GetIssuer().as_der():
            #
            # Root is valid.
            #
        
            name = GetCNFromX509Subject(cert.GetSubject())
            item = self.tree.AddRoot(name, data = wx.TreeItemData(cert))
            del path[0]

        else:
            #
            # We're missing our  toplevel issuer.
            # Grey out the name, and insert the name as the
            # tree item data so we can do something reasonable with
            # it if this item is doubleclicked.
            #
            name = GetCNFromX509Subject(cert.GetIssuer())
            item = self.tree.AddRoot(name + "(missing)", data = wx.TreeItemData(name))
            self.tree.SetItemTextColour(item, wx.LIGHT_GREY)
            
        self.tree.Expand(item)
        for cert in path:
            name = GetCNFromX509Subject(cert.GetSubject())
            nitem = self.tree.AppendItem(item, name, data = wx.TreeItemData(cert))
            self.tree.Expand(item)
            item = nitem

        self.tree.SelectItem(item)

    def _writeValue(self, tag, value):
        """
        Write a tag/value pair into the text widget.
        Make tag bold, value normal.
        """

        self.text.SetDefaultStyle(self.bold)
        self.text.AppendText(str(tag) + ": ")
        self.text.SetDefaultStyle(self.normal)
        self.text.AppendText(str(value) + "\n")

    def __build(self):
        """
        Construct the GUI.

        """

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        nb = self.notebook = wx.Notebook(self, -1)
        sizer.Add(nb, 1, wx.EXPAND)

        #self.htmlWindow = wx.HtmlWindow(nb, -1)
        self.text = wx.TextCtrl(nb, -1, style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_LINEWRAP | wx.TE_RICH)
        nb.AddPage(self.text, "General")

        self.tree = wx.TreeCtrl(nb, -1,
                               style = wx.TR_NO_BUTTONS | wx.TR_SINGLE)
        nb.AddPage(self.tree, "Certification path")

        #
        # Force the tree to stay open.
        #
        wx.EVT_TREE_ITEM_COLLAPSING(self, self.tree.GetId(), lambda event: event.Veto())
        wx.EVT_TREE_ITEM_ACTIVATED(self, self.tree.GetId(), self.OnTreeItemActivated)


        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        self.Fit()

    def OnTreeItemActivated(self, event):
        item = event.GetItem()
        data = self.tree.GetItemData(item)
        cert = data.GetData()

        #
        # We're encoding a missing cert by placing the name of the cert in
        # the data field.
        #

        if type(cert) == str:
            dlg = wx.MessageDialog(self, "No certificate for %s is installed." % (cert),
                                  "Missing certificate",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            dlg = CertificateViewer(self, -1, cert, self.certMgr)
            dlg.Show()
        

class CertificateViewer(wx.Dialog):
    def __init__(self, parent, id, cert, certMgr):

        wx.Dialog.__init__(self, None, id, "", size = wx.Size(700, 400),
                          style= wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        title = GetCNFromX509Subject(cert.GetSubject())
        self.SetTitle(title)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.panel = CertificateViewerPanel(self, -1, cert, certMgr)
        sizer.Add(self.panel, 1, wx.EXPAND)

        b = wx.Button(self, -1, "Close")
        sizer.Add(b, 0)
        wx.EVT_BUTTON(self, b.GetId(), self.OnClose)
        wx.EVT_CLOSE(self, self.OnClose)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def OnClose(self, event):
        self.Destroy()

if __name__ == "__main__":

    pyapp = wx.PySimpleApp()

    import AccessGrid.Toolkit
    app = AccessGrid.Toolkit.WXGUIApplication()
    # app.GetCertificateManager().InitEnvironment()

    # id = app.GetCertificateManager().GetDefaultIdentity()
    # print "id is ", id.GetSubject()

    ca = app.GetCertificateManager().GetCACerts()

    # d = ExportIDCertDialog(None, id)

    # d = ExportCACertDialog(None, ca[0])

    d = CertificateViewer(None, -1, ca[0], app.GetCertificateManager())
    
    ret = d.Show(1)

    pyapp.SetTopWindow(d)
    pyapp.MainLoop()
    
