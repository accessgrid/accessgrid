import wx

import time
import os

from AccessGrid import Toolkit
from AccessGrid import Log
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from AccessGrid.Security.CertificateRepository import RepoInvalidCertificate
from AccessGrid.Security.Utilities import NewMd5Hash
import CertificateRequestTool

log = Log.GetLogger('CertificateStatusDialog')

class CertificateStatusDialog(wx.Dialog):
    '''
    Dialog showing submitted certificate requests.  It allows users to check status
    of requests and store them to right location.
    '''
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title,
                          style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER )

        self.SetSize(wx.Size(700,350))

        self.info = wx.StaticText(self, -1, "You have requested following certificates:")
        self.list = wx.ListCtrl(self, wx.NewId(),
                               style = wx.LC_REPORT | wx.SUNKEN_BORDER)
        
        self.importButton = wx.Button(self, -1, "Import certificate")
        self.importButton.Enable(0)

        self.deleteButton = wx.Button(self, -1, "Delete request")
        self.deleteButton.Enable(0)

        self.getStatusButton = wx.Button(self, -1, "Update Status")
        self.closeButton = wx.Button(self, wx.ID_CLOSE, "Close")

        self.proxyPanel = CertificateRequestTool.HTTPProxyConfigPanel(self)
        
        self.newRequestButton = wx.Button(self, wx.NewId(), "New Request")

        self.certReqDict = {}
        self.certStatus = {}
        self.beforeStatus = 0
        self.afterStatus = 1
        self.state = self.beforeStatus
        self.selectedItem = None
        
        self.__setProperties()
        self.__layout()
        self.__setEvents()

        self.AddCertificates()
                                     
    def __setEvents(self):
        wx.EVT_BUTTON(self, self.importButton.GetId(), self.OnImportCertificate)
        wx.EVT_BUTTON(self, self.deleteButton.GetId(), self.OnDeleteRequest)
        wx.EVT_BUTTON(self, self.getStatusButton.GetId(), self.OnUpdateStatus)
        wx.EVT_BUTTON(self, self.closeButton.GetId(), self.OnClose)
        wx.EVT_BUTTON(self, self.newRequestButton.GetId(), self.RequestCertificate)

        wx.EVT_LIST_ITEM_SELECTED(self.list, self.list.GetId(),
                               self.OnCertSelected)

    def __layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.info, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 10)

        hs = wx.BoxSizer(wx.HORIZONTAL)
        vs = wx.BoxSizer(wx.VERTICAL)
        
        hs.Add(self.list, 1, wx.EXPAND|wx.ALL, 10)
        hs.Add(vs, 0, wx.EXPAND)
        
        vs.Add(self.importButton, 0, wx.ALL | wx.EXPAND, 2)
        vs.Add(self.deleteButton, 0, wx.ALL | wx.EXPAND, 2)
        
        sizer.Add(hs, 1, wx.EXPAND | wx.RIGHT, 8)
        
        sizer.Add(self.proxyPanel, 0, wx.EXPAND | wx.ALL, 10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.getStatusButton, 0 , wx.ALL, 5)
        box.Add(self.newRequestButton, 0 , wx.ALL, 5)
        box.Add(self.closeButton, 0 , wx.ALL, 5)
        sizer.Add(box, 0, wx.CENTER | wx.BOTTOM, 5)

        self.SetAutoLayout(1)
        self.SetSizer(sizer)
        self.Layout()

        #self.list.SetColumnWidth(0, self.list.GetSize().GetWidth()/3.0)
        #self.list.SetColumnWidth(1, self.list.GetSize().GetWidth()/3.0)
        #self.list.SetColumnWidth(2, self.list.GetSize().GetWidth()/3.0)
                
    def __setProperties(self):
        self.list.InsertColumn(0, "Certificate Type")
        self.list.InsertColumn(1, "Subject Name")
        self.list.InsertColumn(2, "Date Requested")
        self.list.InsertColumn(3, "Status")
           
    def OnUpdateStatus(self, event):
        self.CheckStatus()
            
    def OnClose(self, event):
        self.Close()

    def OnCertSelected(self, event):
        row = event.m_itemIndex
        self.selectedItem = row

        if row in self.certStatus:
            status = self.certStatus[row][0]

            if status == "Ready":
                self.importButton.Enable(1)
                
            else:
                self.importButton.Enable(0)

        self.deleteButton.Enable(1)
            
    def OnDeleteRequest(self, event):

        if self.selectedItem is None:
            return

        try:
            certMgr = Toolkit.Application.instance().GetCertificateManager()
            req = self.reqList[self.selectedItem][0]
            log.debug("Removing request %s", req.GetSubject())
            certMgr.GetCertificateRepository().RemoveCertificateRequest(req)
        except:
            log.exception("Error removing cert request")

        self.AddCertificates()
        
    def OnImportCertificate(self, event):

        if self.selectedItem is None:
            return
        
        item = self.reqList[self.selectedItem]
        status = self.certStatus[self.selectedItem]

        cert = status[1]

        #
        # Write the cert out to a tempfile, then import.
        #

        hash = NewMd5Hash(cert).hexdigest()
        tempfile = os.path.join(UserConfig.instance().GetTempDir(), "%s.pem" % (hash))

        try:
            try:
                fh = open(tempfile, "w")
                fh.write(cert)
                fh.close()

                certMgr = Toolkit.Application.instance().GetCertificateManager()
                impCert = certMgr.ImportRequestedCertificate(tempfile)

                MessageDialog(self,
                              "Successfully imported certificate for\n" +
                              str(impCert.GetSubject()),
                              "Import Successful")
                self.AddCertificates()

            except RepoInvalidCertificate, e:
                log.exception("Invalid certificate")
                msg = e[0]
                ErrorDialog(self,
                            "The import of your approved certificate failed:\n"+
                            msg,
                            "Import Failed")


            except:
                log.exception("Import of requested cert failed")
                ErrorDialog(self,
                            "The import of your approved certificate failed.",
                            "Import Failed")

        finally:
            os.unlink(tempfile)

            

    def RequestCertificate(self, event):
        self.Hide()
        reqTool = CertificateRequestTool.CertificateRequestTool(None,
                                                                certificateType = None)
        reqTool.Destroy()
                                  
    def AddCertificates(self):

        certMgr = Toolkit.Application.instance().GetCertificateManager()

        #
        # reqList is a list of tuples (requestDescriptor, token, server, creationTime)
        #
        
        self.reqList = certMgr.GetPendingRequests()

        self.list.DeleteAllItems()

        row = 0
        for reqItem in self.reqList:

            self.certStatus[row] = ("Unknown")
            requestDescriptor, token, server, creationTime = reqItem

            typeMeta = requestDescriptor.GetMetadata("AG.CertificateManager.requestType")

            if typeMeta is None or typeMeta == "":
                type = "Identity"
            else:
                type = typeMeta[0].upper() + typeMeta[1:]
            subject = str(requestDescriptor.GetSubject())

            if creationTime is not None:
                date = time.strftime("%x %X", time.localtime(int(creationTime)))
            else:
                date = ""

            status = "?"

            self.list.InsertStringItem(row, type)
            self.list.SetStringItem(row, 1, subject)
            self.list.SetStringItem(row, 2, date)
            self.list.SetStringItem(row, 3, status)
            self.list.SetItemData(row, row)
            row = row+1

        if len(self.reqList) == 0:
            self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
            self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
        else:
            self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
            
        self.list.SetColumnWidth(2, wx.LIST_AUTOSIZE_USEHEADER)
        self.list.SetColumnWidth(3, wx.LIST_AUTOSIZE_USEHEADER)

        self.CheckStatus()
                                
    def CheckStatus(self):
        """
        Update the status of the certificate requests we have listed in the GUI.

        """

        certMgr = Toolkit.Application.instance().GetCertificateManager()

        proxyEnabled, proxyHost, proxyPort = self.proxyPanel.GetInfo()
        
        # Check status of certificate requests
        for row in range(0, self.list.GetItemCount()):

            self.certStatus[row] = ("Unknown")
            
            itemId = self.list.GetItemData(row)
            reqItem = self.reqList[itemId]
            requestDescriptor, token, server, creationTime = reqItem

            #print "Testing request %s server=%s token=%s" % (requestDescriptor,
            #                                                 server, token)
            self.list.SetStringItem(row, 3, "Checking...")
            self.Refresh()
            self.Update()
            if server is None or token is None:
                #
                # Can't check.
                #
                self.list.SetStringItem(row, 3, "Invalid")
                continue

            if proxyEnabled:
                certReturn = certMgr.CheckRequestedCertificate(requestDescriptor, token, server,
                                                               proxyHost, proxyPort)
            else:
                certReturn = certMgr.CheckRequestedCertificate(requestDescriptor, token, server)

            success, msg = certReturn
            if not success:

                #
                # Map nonobvious errors
                #

                if msg.startswith("Couldn't open certificate file."):
                    msg = "Not ready"
                elif msg.startswith("Couldn't read from certificate file."):
                    msg = "Not ready"
                elif msg.startswith("There is no certificate for this token."):
                    msg = "Request not found"
                
                self.list.SetStringItem(row, 3, msg)
                self.certStatus[row] = ("NotReady")
            else:
                self.list.SetStringItem(row, 3, "Ready for installation")
                self.certStatus[row] = ("Ready", msg)

            self.list.SetColumnWidth(3, wx.LIST_AUTOSIZE)
            
#              self.cancelButton.Enable(False)

#              if cert != "":
#                  self.certificateClient.SaveCertificate(cert)
#                  nrOfApprovedCerts = nrOfApprovedCerts + 1
#                  # Change the status text
#                  self.text.SetLabel("%i of you certificates are installed. Click 'Ok' to start using them." %nrOfApprovedCerts)
#                  self.list.SetStringItem(row, 2, "Installed")

#              else:
#                  # Change status text to something else
#                  self.list.SetStringItem(row, 2, "Not approved")
#                  self.text.SetLabel("Your certificates have not been approved yet. \nPlease try again later.")
                
