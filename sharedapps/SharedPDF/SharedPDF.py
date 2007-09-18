#-----------------------------------------------------------------------------
# Name:        SharedPDF.py
# Purpose:     Shared PDF viewer for Windows platform.
#
# Author:      Susanne Lefvert
#
# Created:     $Date: 2007-09-18 20:45:30 $
# RCS-ID:      $Id: SharedPDF.py,v 1.7 2007-09-18 20:45:30 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# wxPython imports
import wx

if wxPlatform == '__WXMSW__':
    from wx.lib.pdfwin import PDFWindow


try:
    from twisted.internet import threadedselectreactor
    threadedselectreactor.install()
except:
    pass

from twisted.internet import reactor

# AGTk imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.SharedAppClient import SharedAppClient
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid import icons
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.DataStoreClient import GetVenueDataStore

# Standard imports
import os
from optparse import Option
import sys

class PdfViewer(wx.Panel):
    '''
    Shared application that uses the ActiveX interface to
    Adobe Acrobate Reader version 4 and higher. This
    application only works on Windows platforms. It uses
    the defined pdf activex class provided by wxPython.
    '''
    
    def __init__(self, parent, name, appUrl, venueUrl, connectionId):
        wx.Panel.__init__(self, parent, -1)

        reactor.interleave(wx.CallAfter)
        
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
        self.log.debug("PdfViewer.__init__: Start pdf viewer, venueUrl: %s, appUrl: %s"%(venueUrl, appUrl))

        # Get client profile
        clientProfile = ClientProfile(UserConfig.instance().GetProfile())
       
        # Join the application session.
        self.sharedAppClient.Join(appUrl, clientProfile)
        self.id = self.sharedAppClient.GetPublicId()
                
        # Register callbacks for external events
        self.sharedAppClient.RegisterEventCallback("openFile", self.OpenCallback)
        self.sharedAppClient.RegisterEventCallback("changePage", self.ChangePageCallback)

        # Create data store interface
        self.dataStoreClient = GetVenueDataStore(venueUrl, connectionId)

        self.file = None
        self.pageNr = 1
        
        # Get current state
        self.file = str(self.sharedAppClient.GetData("file"))
        self.pageNr = int(self.sharedAppClient.GetData("page"))
        if not self.pageNr:
            self.pageNr = 1

        if self.file:
            try:
                self.dataStoreClient.Download(self.file, "tmp")
                self.pdf.LoadFile("tmp")
                self.pdf.setCurrentPage( int(self.pageNr))
            except:
                self.log.exception("PdfViewer.__init__: Download failed %s"%(self.file))

    #
    # Callbacks for local UI events.
    #

    def OnOpenButton(self, event):
        '''
        Invoked when user clicks the open button.
        '''
        dlg = FileSelectorDialog(self, -1, "Select File Location", self.dataStoreClient)

        if dlg.ShowModal() == wx.ID_OK:
            selectedFile = dlg.GetFile()
            if selectedFile:
                wx.BeginBusyCursor()

                # Get file from venue
                try:
                    self.dataStoreClient.Download(selectedFile, "tmp")
                    self.pdf.LoadFile("tmp")
                    self.pdf.setCurrentPage(1)
                    self.pageNr = 1
                    self.file = selectedFile

                except:
                    self.log.exception("PdfViewer.OnOpenButton: Failed to download %s"%(selectedFile))
                    dlg = wx.MessageDialog(self, 'Failed to download %s.'%(selectedFile),
                                          'Download Failed', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()

                else:
                    # Update shared app status
                    self.sharedAppClient.SetData("file", self.file)
                    self.sharedAppClient.SetData("page", self.pageNr)
                    
                    # Send event
                    self.sharedAppClient.SendEvent("openFile", self.file)
                    self.sharedAppClient.SendEvent("changePage",  str(self.pageNr))
                                       
                wx.EndBusyCursor()
          
    def OnPrevPageButton(self, event):
        '''
        Invoked when user clicks the previous button.
        '''
        self.pageNr = self.pageNr - 1
        self.pdf.setCurrentPage(self.pageNr)
        self.sharedAppClient.SendEvent("changePage", str(self.pageNr))
        self.sharedAppClient.SetData("page", self.pageNr)

    def OnNextPageButton(self, event):
        '''
        Invoked when user clicks the next button.
        '''
        self.pageNr = self.pageNr + 1
        self.pdf.setCurrentPage(self.pageNr)
        self.sharedAppClient.SendEvent("changePage", str(self.pageNr))
        self.sharedAppClient.SetData("page", self.pageNr)

    def OnExit(self, event):
        '''
        Shut down shared pdf.
        '''
        self.sharedAppClient.Shutdown()
        
    #    
    # Callbacks for external events
    #

    def OpenCallback(self, event):
        '''
        Invoked when a open event is received.
        '''
        self.file = str(event.GetData())
        id = event.GetSenderId()
        
        # Ignore my own events
        if self.id != id:
	    try:
                self.dataStoreClient.Download(self.file, "tmp")
            except:
                self.log.exception("PdfViewer.__OpenCallback: Download failed %s"%(self.file))
    	
	    wx.BeginBusyCursor()
            wx.CallAfter(self.pdf.LoadFile, "tmp")
            #wx.CallAfter(self.pdf.setCurrentPage, self.pageNr)
            wx.CallAfter(self.Refresh)
            wx.EndBusyCursor()
	              
    def ChangePageCallback(self, event):
        '''
        Invoked when a changePage event is received.
        '''
       
        id = event.GetSenderId()
        # Ignore my own events
        if self.id != id:
            self.pageNr = int(event.GetData())
            wx.CallAfter(self.pdf.setCurrentPage, int(self.pageNr))        
            wx.CallAfter(self.Refresh)
               
    def __Layout(self):
        '''
        Layout of ui components.
        '''

        # Create UI objects
        self.openButton = wx.Button(self, wx.NewId(), "Open PDF File")
        self.prevButton = wx.Button(self, wx.NewId(), "<-- Previous Page")
        self.nextButton = wx.Button(self, wx.NewId(), "Next Page -->")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add(self.pdf, proportion=1, flag=wx.EXPAND)

        btnSizer.Add(self.openButton, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        btnSizer.Add(self.prevButton, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        btnSizer.Add(self.nextButton, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

        btnSizer.Add((50,-1), proportion=2, flag=wx.EXPAND)
        sizer.Add(btnSizer, proportion=0, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

#----------------------------------------------------------------------

class FileSelectorDialog(wx.Dialog):
    def __init__(self, parent, id, title, dataStoreClient):
        wx.Dialog.__init__(self, parent, id, title)

        # Create UI components.
        self.infoText = wx.StaticText(self, -1, "Select pdf file to open: ",
                                     size = wx.Size(300, 20), style=wx.ALIGN_LEFT)
        self.infoText2 = wx.StaticText(self, -1, "File:")
        self.pdfList = wx.ComboBox(self, wx.NewId(), size = wx.Size(200, 20),
                                  choices = [], style=wx.CB_DROPDOWN|wx.CB_SORT)
        self.addFileButton = wx.Button(self, wx.NewId(), "Add File")
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.__Layout()

        EVT_BUTTON(self, self.addFileButton.GetId(), self.OpenFileDialog)
      
        # Create the data store client.
        self.dataStoreClient = dataStoreClient
        self.PopulateCombobox()
        
    def PopulateCombobox(self, default = None):
        # Get pdf files from venue
        fileNames = []

        wx.BeginBusyCursor()
        try:
            self.dataStoreClient.LoadData()
            fileNames = self.dataStoreClient.QueryMatchingFiles("*.pdf")
        except:
            self.log.exception("FileSelectorDialog.PopulateCombobox: QueryMatchingFiles failed.")
        wx.EndBusyCursor()
                
        self.pdfList.Clear()
        for file in fileNames:
            self.pdfList.Append(file)

        if default and not len(default) == 0:
            self.pdfList.SetValue(default)
        else:
            self.pdfList.SetSelection(0)

    def OpenFileDialog(self, event):
        dlg = wx.FileDialog(self, wildcard="*.pdf")
        filePath = None
                
        if dlg.ShowModal() == wx.ID_OK:
            wx.BeginBusyCursor()
            self.pageNr = 1
            filePath = dlg.GetPath()

            # Upload file to venue
         
            try:
                self.dataStoreClient.Upload(filePath)
            except:
                self.log.exception("OpenFileDialog: Upload file %s failed"%(filePath))

            self.PopulateCombobox(default = os.path.basename(filePath))
            wx.EndBusyCursor()

        dlg.Destroy()
               
    def GetFile(self):
        return self.pdfList.GetValue()
                            
    def __Layout(self):
        # Create UI objects
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(wx.Size(5,5))
        sizer.Add(self.infoText, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(wx.Size(5,5))

        btnSizer1.Add(self.infoText2, 0, wx.EXPAND|wx.ALL, 5)
        btnSizer1.Add(self.pdfList, 0, wx.EXPAND|wx.ALL, 5)
        btnSizer1.Add(self.addFileButton, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(btnSizer1, 0, wx.EXPAND, 10)
        
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 10)
        
        btnSizer.Add(self.okButton, 1, wx.RIGHT, 5)
        btnSizer.Add(self.cancelButton, 1)
        
        sizer.Add(btnSizer, 0, wx.ALIGN_CENTER)

        mainSizer.Add(sizer, 0, wx.ALL, 10)
        
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.SetAutoLayout(1)
        
#----------------------------------------------------------------------

def Usage():
    """
    How to use the program.
    """
    print "%s:" % sys.argv[0]
    print "    -a|--applicationURL : <url to application in venue>"
    print "    -v|--venueURL : <url to venue>"
    print "    -h|--help : print usage"
    print "    -d|--debug : print debugging output"
    
if __name__ == '__main__':
      
    # Create the wx python application
    wxapp = wx.PySimpleApp()
    wx.BeginBusyCursor()
       
    # Inizialize AG application
    app = WXGUIApplication()
    appurlOption = Option("-a", "--applicationURL", dest="appUrl", default=None,
                       help="Specify an application url on the command line")
    venueurlOption = Option("-v", "--venueURL", dest="venueUrl", default=None,
                       help="Specify a venue url on the command line")
    testOption = Option("-t", "--testMode", dest="test", action="store_true",
                        default=None, help="Automatically create application session in venue")
    connectionIdOption = Option("-i", "--connectionId", dest="connectionId", default=None,
                                help="Add connection id")
    app.AddCmdLineOption(connectionIdOption)
    app.AddCmdLineOption(appurlOption)
    app.AddCmdLineOption(venueurlOption)
    app.AddCmdLineOption(testOption)

    name = "SharedPDF"
    app.Initialize(name)

    appUrl = app.GetOption("appUrl")
    venueUrl = app.GetOption("venueUrl")
    test = app.GetOption("test")
    conId = app.GetOption("connectionId")
    if test:
        from AccessGrid.Venue import VenueIW
        # Create an application session in the venue
        # for testing. This should normally be done via
        # the Venue Client menu.
        venue = VenueIW("https://localhost:8000/Venues/default")
        appDesc = venue.CreateApplication("Shared PDF",
                                          "Shared PDF",
                                          "application/x-ag-shared-pdf")
        
        appUrl = appDesc.uri

    if not appUrl:
        Usage()
        sys.exit(0)
        
    if not appUrl or not venueUrl:
        Usage()
        sys.exit(0)

    if wxPlatform == '__WXMSW__':
        # Create the UI
        mainFrame = wx.Frame(None, -1, name, size = wx.Size(600, 600))
        mainFrame.SetIcon(icons.getAGIconIcon())
        viewer = PdfViewer(mainFrame, name, appUrl, venueUrl, conId)

        # Start the UI main loop
        mainFrame.Show()
        wx.EndBusyCursor()
           
        wxapp.MainLoop()

    else:
        wx.EndBusyCursor()
        dlg = wx.MessageDialog(frame, 'This application only works on MSW.',
                              'Sorry', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

  
