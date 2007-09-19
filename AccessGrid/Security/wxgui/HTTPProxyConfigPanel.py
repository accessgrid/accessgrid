import wx

from AccessGrid.Platform.Config import SystemConfig

class HTTPProxyConfigPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        sbox = wx.StaticBox(self, -1, "Proxy server")
        self.sizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)

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

        self.proxyEnabled = wx.CheckBox(self, -1, "Use a proxy server to connect to the certificate server")

        wx.EVT_CHECKBOX(self, self.proxyEnabled.GetId(), self.OnCheckbox)

        self.proxyText = wx.TextCtrl(self, -1, defaultProxyHost)
        self.proxyPort = wx.TextCtrl(self, -1, defaultProxyPort)

        self.proxyEnabled.SetValue(defaultEnabled)
        self.UpdateProxyEnabledState()

        self._Layout()
        self.Fit()

    def _Layout(self):
        #
        # Labelled box for the proxy stuff.
        #

        self.sizer.Add(self.proxyEnabled, 0, wx.EXPAND | wx.ALL, 5)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, "Address: "), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
        hsizer.Add(self.proxyText, 1, wx.EXPAND|wx.RIGHT, 5)
        hsizer.Add(wx.StaticText(self, -1, "Port: "), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
        hsizer.Add(self.proxyPort, 0, wx.EXPAND|wx.RIGHT, 5)
        
        self.sizer.Add(hsizer, 0, wx.EXPAND |wx.BOTTOM, 5)

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

