
from wxPython.wx import * 

class SelectorGUI(wxFrame): 
    def __init__(self, name, rtpObject = None):
        wxFrame.__init__(self, NULL, -1, name, size = wxSize(400, 500))
        self.panel = wxPanel(self, -1)
        self.scrolledWindow = wxScrolledWindow(self.panel, -1,
                                               size = wxSize(100,100),
                                               style = wxSIMPLE_BORDER)
        self.scrolledWindow.SetScrollbars(0,20,15,8)
        self.scrolledWindow.SetBackgroundColour('white')
        self.refreshButton = wxButton(self.panel, wxNewId(), "Refresh")
        self.closeButton = wxButton(self.panel, wxNewId(), "Close")
        self.rtpObject = rtpObject

        if rtpObject:
            self.sourceDict = rtpObject.GetSources()
        else:
            self.sourceDict = {1:"test1", 2:"test2", 3:"test3"}
        
        self.gridSizer = None
        self.widgets = {}
        self.__Layout()
        self.Show()
               
        EVT_BUTTON(self, self.closeButton.GetId(), self.OnClose) 
        EVT_BUTTON(self, self.refreshButton.GetId(), self.OnRefresh) 

    def OnClose(self, event):
        self.Destroy()

    def OnRefresh(self, event):
        self.sourceDict = self.rtpObject.GetSources()
        self.__Layout()

    def OnCheck(self, event):
        obj = event.GetEventObject()
        for checkbox in self.widgets.keys():
            if checkbox is not obj:
                checkbox.SetValue(0)

        ssrc = self.widgets[obj]
        self.rtpObject.SetAllowedSource(ssrc)
                                        
    def __Layout(self):
        if self.gridSizer:
            i = 0
            for w in self.widgets.keys():
                w.Destroy()

            self.widgets = {}
                                           
        s = wxBoxSizer(wxVERTICAL)
        s.Add(self.scrolledWindow, 1, wxEXPAND|wxALL, 10)

        s2 = wxBoxSizer(wxHORIZONTAL)
        s2.Add(self.refreshButton, 0)
        s2.Add(self.closeButton, 0)
        s.Add(s2, 0, wxALIGN_CENTER)
        
        self.panel.SetSizer(s)

        self.gridSizer = wxFlexGridSizer(1, 1, 6, 6)
        
        # Add sources
        for ssrc in self.sourceDict.keys():
            sourceOption = wxCheckBox(self.scrolledWindow, wxNewId(),
                                      str(self.sourceDict[ssrc]))
            self.gridSizer.Add(sourceOption, 0, wxEXPAND|wxALL, 5)
            EVT_CHECKBOX(self, sourceOption.GetId(), self.OnCheck)
            self.widgets[sourceOption] = ssrc
                
        self.gridSizer.AddGrowableCol(1)
        self.scrolledWindow.SetSizer(self.gridSizer)
        self.scrolledWindow.Layout()

        self.panel.Show(1) 
        self.panel.Layout()
        self.panel.SetAutoLayout(1)

                
if __name__ == "__main__": 

    wxapp = wxPySimpleApp()
    ui = SelectorGUI("test")
    wxapp.SetTopWindow(ui)
    wxapp.MainLoop()
