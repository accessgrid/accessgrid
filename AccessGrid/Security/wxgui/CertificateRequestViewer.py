import wx

import time
import os

from AccessGrid.Security.Utilities import GetCNFromX509Subject

class CertificateRequestViewerPanel(wx.Panel):
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
        
        wx.Panel.__init__(self, parent, id, style = 0)

        self.reqWrapper = request
        self.request, self.token, self.server, self.creationTime = request.GetRequestInfo()
        self.certMgr = certMgr

        self.__build()

        #
        # Set up text styles.
        #

        boldFont = wx.Font(-1, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.bold = bold = wx.TextAttr()
        self.bold.SetFont(boldFont)
      
        normalFont = wx.Font(-1, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.normal = normal = wx.TextAttr()
        self.normal.SetFont(normalFont)

        defaultPoints = self.text.GetFont().GetPointSize()
        hdrFont = wx.Font(defaultPoints + 4, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.hdr = hdr = wx.TextAttr()
        self.hdr.SetFont(hdrFont)

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

        self.text.SetInsertionPoint(0)

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

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        panel = self
        
        self.text = wx.TextCtrl(panel, -1, style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_LINEWRAP | wx.TE_RICH)
        sizer.Add(self.text, 1, wx.EXPAND)

        panel.SetSizer(sizer)
        panel.SetAutoLayout(1)
        panel.Fit()


class CertificateRequestViewer(wx.Dialog):
    def __init__(self, parent, id, req, certMgr):

        wx.Dialog.__init__(self, None, id, "", size = wx.Size(700, 400),
                          style= wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        title = req.GetShortName()
        self.SetTitle(title)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.panel = CertificateRequestViewerPanel(self, -1, req, certMgr)
        sizer.Add(self.panel, 1, wx.EXPAND)

        b = wx.Button(self, -1, "Close")
        sizer.Add(b, 0)
        wx.EVT_BUTTON(self, b.GetId(), self.OnClose)
        wx.EVT_CLOSE(self, self.OnClose)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def OnClose(self, event):
        self.Destroy()
