from wxPython.wx import *

import os

from AccessGrid.Security.Utilities import GetCNFromX509Subject

class CertificateViewerPanel(wxPanel):
    """
    Panel subclass that incorporates the majority of the
    certificate viewer code.

    Contains a notebook with two views: a general view showing all
    of the certificate information, and a certification path view, showing
    the available certificates form the root down to certificate we're
    viewing.
    """
    
    def __init__(self, parent, id, cert, certMgr):
        wxPanel.__init__(self, parent, id, style = 0)

        self.cert = cert
        self.certMgr = certMgr

        self.__build()

        # self.htmlWindow.SetPage(cert.GetVerboseHtml())

        #
        # Set up text styles.
        #

        boldFont = wxFont(-1, wxDEFAULT, wxNORMAL, wxBOLD)
        self.bold = bold = wxTextAttr(font = boldFont)

        normalFont = wxFont(-1, wxDEFAULT, wxNORMAL, wxNORMAL)
        self.normal = normal = wxTextAttr(font = normalFont)

        defaultPoints = self.text.GetFont().GetPointSize()
        hdrFont = wxFont(defaultPoints + 4, wxDEFAULT, wxNORMAL, wxBOLD)
        self.hdr = hdr = wxTextAttr(font = hdrFont)

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

        if cert.GetSubject().get_der() == cert.GetIssuer().get_der():
            #
            # Root is valid.
            #
        
            name = GetCNFromX509Subject(cert.GetSubject())
            item = self.tree.AddRoot(name, data = wxTreeItemData(cert))
            del path[0]

        else:
            #
            # We're missing our  toplevel issuer.
            # Grey out the name, and insert the name as the
            # tree item data so we can do something reasonable with
            # it if this item is doubleclicked.
            #
            name = GetCNFromX509Subject(cert.GetIssuer())
            item = self.tree.AddRoot(name + "(missing)", data = wxTreeItemData(name))
            self.tree.SetItemTextColour(item, wxLIGHT_GREY)
            
        self.tree.Expand(item)
        for cert in path:
            name = GetCNFromX509Subject(cert.GetSubject())
            nitem = self.tree.AppendItem(item, name, data = wxTreeItemData(cert))
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

        sizer = wxBoxSizer(wxHORIZONTAL)
        
        nb = self.notebook = wxNotebook(self, -1)
        sizer.Add(nb, 1, wxEXPAND)

        #self.htmlWindow = wxHtmlWindow(nb, -1)
        self.text = wxTextCtrl(nb, -1, style = wxTE_READONLY | wxTE_MULTILINE | wxTE_LINEWRAP | wxTE_RICH)
        nb.AddPage(self.text, "General")

        self.tree = wxTreeCtrl(nb, -1,
                               style = wxTR_NO_BUTTONS | wxTR_SINGLE)
        nb.AddPage(self.tree, "Certification path")

        #
        # Force the tree to stay open.
        #
        EVT_TREE_ITEM_COLLAPSING(self, self.tree.GetId(), lambda event: event.Veto())
        EVT_TREE_ITEM_ACTIVATED(self, self.tree.GetId(), self.OnTreeItemActivated)


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
            dlg = wxMessageDialog(self, "No certificate for %s is installed." % (cert),
                                  "Missing certificate",
                                  style = wxOK)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            dlg = CertificateViewer(self, -1, cert, self.certMgr)
            dlg.Show()
        

class CertificateViewer(wxDialog):
    def __init__(self, parent, id, cert, certMgr):

        wxDialog.__init__(self, None, id, "", size = wxSize(700, 400),
                          style= wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER)

        title = GetCNFromX509Subject(cert.GetSubject())
        self.SetTitle(title)

        sizer = wxBoxSizer(wxVERTICAL)
        
        self.panel = CertificateViewerPanel(self, -1, cert, certMgr)
        sizer.Add(self.panel, 1, wxEXPAND)

        b = wxButton(self, -1, "Close")
        sizer.Add(b, 0)
        EVT_BUTTON(self, b.GetId(), self.OnClose)
        EVT_CLOSE(self, self.OnClose)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def OnClose(self, event):
        self.Destroy()

if __name__ == "__main__":

    pyapp = wxPySimpleApp()

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
    
