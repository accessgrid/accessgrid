from wxPython.wx import *

from AccessGrid.Platform.Config import SystemConfig

class HTTPProxyConfigPanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1)

        sbox = wxStaticBox(self, -1, "Proxy server")
        self.sizer = wxStaticBoxSizer(sbox, wxVERTICAL)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        
        #
        # Stuff for the proxy configuration.
        #
        
        proxies = SystemConfig.instance().GetProxySettings()

        defaultProxyHost = ""
        defaultProxyPort = ""
        defaultEnabled = 0
        
        if proxies != []:
            defaultProxy, defaultEnabled = proxies[0]
            defaultProxyHost, defaultProxyPort = defaultProxy
            if defaultProxyPort is None:
                defaultProxyPort = ""

        self.proxyEnabled = wxCheckBox(self, -1, "Use a proxy server to connect to the certificate server")

        EVT_CHECKBOX(self, self.proxyEnabled.GetId(), self.OnCheckbox)

        self.proxyText = wxTextCtrl(self, -1, defaultProxyHost)
        self.proxyPort = wxTextCtrl(self, -1, defaultProxyPort)

        self.proxyEnabled.SetValue(defaultEnabled)
        self.UpdateProxyEnabledState()

        self._Layout()
        self.Fit()

    def _Layout(self):
        #
        # Labelled box for the proxy stuff.
        #

        self.sizer.Add(self.proxyEnabled, 0, wxEXPAND | wxALL, 5)
        hsizer = wxBoxSizer(wxHORIZONTAL)
        hsizer.Add(wxStaticText(self, -1, "Address: "), 0, wxALIGN_CENTER_VERTICAL | wxALL, 2)
        hsizer.Add(self.proxyText, 1, wxEXPAND|wxRIGHT, 5)
        hsizer.Add(wxStaticText(self, -1, "Port: "), 0, wxALIGN_CENTER_VERTICAL | wxALL, 2)
        hsizer.Add(self.proxyPort, 0, wxEXPAND|wxRIGHT, 5)
        
        self.sizer.Add(hsizer, 0, wxEXPAND |wxBOTTOM, 5)

    def OnCheckbox(self, event):
        self.UpdateProxyEnabledState()
        
    def UpdateProxyEnabledState(self):

        en = self.proxyEnabled.GetValue()

        self.proxyText.Enable(en)
        self.proxyPort.Enable(en)

    def GetInfo(self):
        return (self.proxyEnabled.GetValue(),
                self.proxyText.GetValue(),
                self.proxyPort.GetValue())

