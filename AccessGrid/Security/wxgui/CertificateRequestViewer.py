from wxPython.wx import *

import time
import os

from AccessGrid.Security.Utilities import GetCNFromX509Subject

class CertificateRequestViewerPanel(wxPanel):
    """
    Panel subclass that incorporates the majority of the
    certificate request viewer code.

    """
    
    def __init__(self, parent, id, request, certMgr):
        """
        Constructor.

        @param parent: parent widget
        @param id: widget id
        @param request: request to view
        @param certMgr: our certificate manager
        @type parent: wx widget
        @type id: number
        @type request: CertRequestWrapper (from CertificateStatusBrowser module)
        @type certMgr: CertificateManager instance

        """
        
        wxPanel.__init__(self, parent, id, style = 0)

        self.reqWrapper = request
        self.request, self.token, self.server, self.creationTime = request.GetRequestInfo()
        self.certMgr = certMgr

        self.__build()

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

        name = GetCNFromX509Subject(self.request.GetSubject())

        #
        # Write cert info into text.
        #
        self.text.SetDefaultStyle(hdr)
        self.text.AppendText(name + "\n\n")
        
        self._writeValue("Subject", str(self.request.GetSubject()))
        self.text.AppendText("\n")

        self._writeValue("Request token", self.token)
        self._writeValue("Server URL", self.server)
        self._writeValue("Creation time", time.strftime("%X %x", time.localtime(int(self.creationTime))))
        self.text.AppendText("\n")

        self._writeValue("Status from last update", self.reqWrapper.GetStatus())
        if self.reqWrapper.GetCertReady():
            self._writeValue("Certificate ready", "Yes")
            self._writeValue("Certificate", "")
            self.text.AppendText(self.reqWrapper.GetCert())
        else:
            self._writeValue("Certificate ready", "No")
            self._writeValue("Full status message", self.reqWrapper.GetFullStatus())

        self._writeValue("Modulus", self.request.GetModulus())
        self._writeValue("Modulus hash", self.request.GetModulusHash())

        #self._writeValue("Certificate location", cert.GetPath())
        #pkloc =  cert.GetKeyPath()
        #if pkloc and os.access(pkloc, os.R_OK):
        #    self._writeValue("Private key location", pkloc)
        
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

        panel = self
        
        self.text = wxTextCtrl(panel, -1, style = wxTE_READONLY | wxTE_MULTILINE | wxTE_LINEWRAP | wxTE_RICH)
        sizer.Add(self.text, 1, wxEXPAND)

        panel.SetSizer(sizer)
        panel.SetAutoLayout(1)
        panel.Fit()


class CertificateRequestViewer(wxDialog):
    def __init__(self, parent, id, req, certMgr):

        wxDialog.__init__(self, None, id, "", size = wxSize(700, 400),
                          style= wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER)

        title = req.GetShortName()
        self.SetTitle(title)

        sizer = wxBoxSizer(wxVERTICAL)
        
        self.panel = CertificateRequestViewerPanel(self, -1, req, certMgr)
        sizer.Add(self.panel, 1, wxEXPAND)

        b = wxButton(self, -1, "Close")
        sizer.Add(b, 0)
        EVT_BUTTON(self, b.GetId(), self.OnClose)
        EVT_CLOSE(self, self.OnClose)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def OnClose(self, event):
        self.Destroy()
