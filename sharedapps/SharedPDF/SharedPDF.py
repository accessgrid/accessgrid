
# wxPython imports
from wxPython.wx import *

if wxPlatform == '__WXMSW__':
    from wx.lib.pdfwin import PDFWindow

# AGTk imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.SharedAppClient import SharedAppClient
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid import icons
from AccessGrid.Toolkit import WXGUIApplication

# Standard imports
import os

class PdfViewer(wxPanel):
    '''
    Shared application that uses the ActiveX interface to
    Adobe Acrobate Reader version 4 and higher. This
    application only works on Windows platforms. It uses
    the defined pdf activex class provided by wxPython.
    '''
    
    def __init__(self, parent, name, appUrl):
        wxPanel.__init__(self, parent, -1)

        # Create ActiveX interface to adobe acrobate reader
        self.pdf = PDFWindow(self)
        
        # Do UI layout
        self.__Layout()

        # Create UI events
        EVT_BUTTON(self, self.openButton.GetId(), self.OnOpenButton)
        EVT_BUTTON(self, self.prevButton.GetId(), self.OnPrevPageButton)
        EVT_BUTTON(self, self.nextButton.GetId(), self.OnNextPageButton)
        EVT_WINDOW_DESTROY(self, self.OnExit)

        # Create shared application client        
        self.sharedAppClient = SharedAppClient(name)
        self.log = self.sharedAppClient.InitLogging()
        self.id = self.sharedAppClient.GetPublicId()

        # Get client profile
        clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(), "profile")
        clientProfile = ClientProfile(clientProfileFile)

        # Join the application session.
        self.sharedAppClient.Join(appUrl, clientProfile)
        
        # Register callbacks for external events
        self.sharedAppClient.RegisterEventCallback("open", self.OpenCallback)
        self.sharedAppClient.RegisterEventCallback("position", self.ChangePositionCallback)
        
        # Get current state
        ret = self.sharedAppClient.GetData("position")
        self.filePath = None
        self.pageNr = 1
      
        if ret:
            self.filePath, self.pageNr = ret
            self.pdf.LoadFile(self.filePath)
            self.pdf.setCurrentPage(self.pageNr)

        self.Show()
    #
    # Callbacks for local UI events.
    #

    def OnOpenButton(self, event):
        '''
        Invoked when user clicks the open button.
        '''
        dlg = wxFileDialog(self, wildcard="*.pdf")

        if dlg.ShowModal() == wxID_OK:
            wxBeginBusyCursor()
            self.pdf.LoadFile(dlg.GetPath())
            self.pageNr = 1
            self.filePath = dlg.GetPath()
            self.sharedAppClient.SetData("position", (self.filePath, self.pageNr))
            self.sharedAppClient.SendEvent("load", (self.filePath, self.pageNr))
            wxEndBusyCursor()

        dlg.Destroy()

    def OnPrevPageButton(self, event):
        '''
        Invoked when user clicks the previous button.
        '''
        self.pageNr = self.pageNr - 1
        self.pdf.setCurrentPage(self.pageNr)
        self.sharedAppClient.SendEvent("position", (self.id, self.filePath, self.pageNr))
        self.sharedAppClient.SetData("position", (self.id, self.pageNr))

    def OnNextPageButton(self, event):
        '''
        Invoked when user clicks the next button.
        '''
        self.pageNr = self.pageNr + 1
        self.pdf.setCurrentPage(self.pageNr)
        self.sharedAppClient.SendEvent("position", (self.filePath, self.pageNr))
        self.sharedAppClient.SetData("position", (self.id, self.pageNr))

    def OnExit(self, event):
        '''
        Shut down shared browser.
        '''
        self.sharedAppClient.Shutdown()
        
    #    
    # Callbacks for external events
    #

    def OpenCallback(self, event):
        '''
        Invoked when a open event is received.
        '''
        id, self.filePath, self.pageNr = event.data
        
        # Ignore my own events
        if self.id != id:
            wxBeginBusyCursor()
            wxCallAfter(self.pdf.LoadFile, self.filePath)
            wxCallAfter(self.pdf.setCurrentPage, self.pageNr)
            wxEndBusyCursor()
        
    def ChangePositionCallback(self, event):
        '''
        Invoked when a next event is received.
        '''
        id, pageNr = event.data
        self.pageNr = pageNr

        # Ignore my own events
        if self.id != id:
            wxCallAfter(self.pdf.setCurrentPage, self.pageNr)
               
    def __Layout(self):
        '''
        Layout of ui components.
        '''

        # Create UI objects
       
        self.openButton = wxButton(self, wxNewId(), "Open PDF File")
        self.prevButton = wxButton(self, wxNewId(), "<-- Previous Page")
        self.nextButton = wxButton(self, wxNewId(), "Next Page -->")
        
        sizer = wxBoxSizer(wxVERTICAL)
        btnSizer = wxBoxSizer(wxHORIZONTAL)
        
        sizer.Add(self.pdf, proportion=1, flag=wxEXPAND)

        btnSizer.Add(self.openButton, proportion=1, flag=wxEXPAND|wxALL, border=5)
        btnSizer.Add(self.prevButton, proportion=1, flag=wxEXPAND|wxALL, border=5)
        btnSizer.Add(self.nextButton, proportion=1, flag=wxEXPAND|wxALL, border=5)

        btnSizer.Add((50,-1), proportion=2, flag=wxEXPAND)
        sizer.Add(btnSizer, proportion=0, flag=wxEXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

#----------------------------------------------------------------------


if __name__ == '__main__':

    appUrl = 'https://zuz.mcs.anl.gov:8000/Venues/default/apps/00000103140ba74c008c00dd0022006dbd6'
    
    # Create the wx python application
    wxapp = wxPySimpleApp()

    # Inizialize AG application
    app = WXGUIApplication()
    name = "SharedPDF"

    #initArgs = ['--debug']
    initArgs = []
    app.Initialize(name, initArgs)

    if wxPlatform == '__WXMSW__':
        # Create the UI
        mainFrame = wxFrame(None, -1, name)
        viewer = PdfViewer(mainFrame, name, appUrl)

        # Start the UI main loop
        mainFrame.Show()
        wxapp.MainLoop()

    else:
        dlg = wxMessageDialog(frame, 'This application only works on MSW.',
                              'Sorry', wxOK | wxICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

  
