import os.path
import time
import md5
import tempfile
import StringIO

from AccessGrid.Platform.Config import UserConfig
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from AccessGrid.Security import CertificateRepository
from AccessGrid.Security.CRSClient import CRSClient

from AccessGrid import Log
log = Log.GetLogger("CertificateStatus")

from wxPython.wx import *

from AccessGrid.Security.Utilities import GetCNFromX509Subject

from CertificateRequestViewer import CertificateRequestViewer
from CertificateBrowserBase import CertificateBrowserBase

from HTTPProxyConfigPanel import HTTPProxyConfigPanel

import ImportExportUtils

class CertRequestWrapper:
    """
    Small wrapper class to hold the information about a certificate request
    so we can cache information, and make updating the information easier.
    """

    def __init__(self, browser, reqInfo):
        """
        Constructor.

        @param browser: the certificate browser this request is being viewed in
        @param reqInfo: information about this certificate request, as returned
        by CertificateManager.GetPendingRequests().
        @type browser: CertificateStatusBrowser instance
        @type reqInfo: tuple containing (requestObj, token, server, creationTime)
        """

        self.request, self.token, self.server, self.creationTime = reqInfo
        self.status = "Unknown"
        self.fullStatus = "Unknown"
        self.certReady = 0
        self.browser = browser
        self.cert = ""

        self.CheckPrivateKey()
        
    def GetCert(self):
        return self.cert

    def GetShortName(self):
        return GetCNFromX509Subject(self.request.GetSubject())        

    def GetStatus(self):
        return self.status

    def GetRequest(self):
        return self.request

    def GetFullStatus(self):
        return self.fullStatus

    def GetCertReady(self):
        return self.certReady

    def Install(self):
        """
        Install this certificate into the local repo:

            Write cert to a tempfile.
            Invoke cert mgr's import method.
            Delete the tempfile.

        """

        if not self.certReady:
            raise Exception("Certificate is not ready for installation")
        
        certText = self.fullStatus

        impCert = None

        hash = md5.new(certText).hexdigest()
        temp_path = os.path.join(UserConfig.instance().GetTempDir(), "%s.pem" % (hash))

        try:
            try:

                #
                # Check to see if there's a lingering copy of the file from before.
                #

                if os.path.isfile(temp_path):
                    log.debug("Cert import temporary file %s already exists, deleting", tempfile)

                    try:
                        os.unlink(temp_path)

                    except:
                        log.exception("Unlink of tempfile %s failed", temp_path)

                        #
                        # Hmm, weird. Make up a new filename instead.
                        #

                        new_path = tempfile.mktemp(".pem")

                        #
                        # Use just the name part on the user's temp dir.
                        #

                        new_head, new_tail = os.path.split(new_path)

                        temp_path = os.path.join(UserConfig.instance().GetTempDir(),
                                                 new_tail)

                #
                # back to our normal life.
                #
                                      
                fh = open(temp_path, "wb")
                fh.write(certText)
                fh.close()

                #
                # Be more paranoid. Ensure the file was created.
                #

                try:
                    fileInfo = os.stat(temp_path)
                except OSError:
                    log.exception("Installing certificate: temp file %s was not created", temp_path)
                    ErrorDialog(self.browser,
                                "The system could not create a temporary file for this certificate import.\n" +
                                "Try restarting the software or rebooting your computer."
                                "Import Failed")
                    return

                if fileInfo.st_size != len(certText):
                    log.error("File %s write did not work: fileSize=%s certSize=%s",
                              temp_path, fileInfo.st_size, len(certText))
                
                certMgr = self.browser.GetCertificateManager()
                impCert = certMgr.ImportRequestedCertificate(temp_path)

                certName = str(impCert.GetSubject())
                
                log.debug("Successfully imported certificate for %s", certName)

                MessageDialog(self.browser,
                              "Successfully imported certificate for\n" + certName,
                              "Import Successful")
                self.browser.Load()

            except CertificateRepository.RepoInvalidCertificate, e:
                log.exception("Invalid certificate")
                msg = e[0]
                ErrorDialog(self.browser,
                            "The import of your approved certificate failed:\n"+
                            msg,
                            "Import Failed")

            except:
                log.exception("Import of requested cert failed")
                ErrorDialog(self.browser,
                            "The import of your approved certificate failed.",
                            "Import Failed")

        finally:
            try:
                os.unlink(temp_path)
            except:
                pass


        if impCert is None:
            return
        
        #
        # If the import succeeded, check to see if we have the issuing
        # certificate for this cert If not, try to load it from the
        # cert server via teh GetCACertificates() method.
        #
        
        path = certMgr.GetCertificatePath(impCert)

        print "Got path: ", path
        last = path[-1]
        if last.GetSubject().get_der() == last.GetIssuer().get_der():
            print "Have full path"
        else:
            print "Missing component: ", last.GetIssuer()

            proxyEnabled, proxyHost, proxyPort = self.browser.GetProxyInfo()
            if proxyEnabled:
                crs = CRSClient(self.server, proxyHost, proxyPort)
            else:
                crs = CRSClient(self.server)

            caCerts = None

            try:
                caInfo = crs.RetrieveCACertificates()

                if caInfo[0]:
                    caCerts = caInfo[1]
                else:
                    log.debug("Erorr retrieving CA certs: %s", caInfo[1])
                
            except:
                log.exception("Could not retrieve ca certs")

            if caCerts:
                print "Got ca: ", caCerts

                for caCert, signingPolicy in caCerts:
                    #
                    # See if this one is already installed.
                    #

                    caObj = None
                    
                    try:

                        caObj = CertificateRepository.Certificate(None,
                                                                  certText = caCert)

                    except:
                        log.exception("Error loading cacert");
                        continue

                    #
                    # Predicate that returns true for an unexpired certificate
                    # having a subject name of this CA cert.
                    #
                    pred = lambda c, der = caObj.GetSubject().get_der(): \
                        c.GetSubject().get_der() == der and not c.IsExpired()

                    #
                    # Determine the list of certs with that name.
                    #
                    matchingCerts = list(certMgr.GetCertificateRepository().FindCertificates(pred))


                    #
                    # If none were found, see about installing.
                    #
                    if matchingCerts == []:
                        #
                        # prompt to install at some point, but just install now.
                        #
                        try:
                            tmp = tempfile.mktemp()
                            fh = open(tmp, "w")
                            fh.write(caCert)
                            fh.close()
                            impCa = certMgr.ImportCACertificatePEM(certMgr.GetCertificateRepository(),
                                                                   tmp)
                            os.unlink(tmp)
                            print "Imported cert ", impCa, impCa.GetSubject()

                            if signingPolicy != "":
                                spPath = impCa.GetFilePath("signing_policy")
                                print "sp path is ", spPath
                                if spPath:
                                    fh = open(spPath, "w")
                                    fh.write(signingPolicy)
                                    fh.close()

                        except:
                            log.exception("Exception while importing CA")
                            

            else:
                print "Didn't get, need a dialog here"
            
    def CheckPrivateKey(self):
        """
        Check to see if the private key for this request exists.

        If it does not, update status and fullStatus, and return 0.

        Otherwise, return 1.

        """
        
        certMgr = self.browser.GetCertificateManager()
        certRepo = certMgr.GetCertificateRepository()
        
        hash = self.request.GetModulusHash()
        pkeyPath = certRepo.GetPrivateKeyPath(hash)

        if not os.path.isfile(pkeyPath):
            self.status = "Private key not found"
            self.fullStatus = "Private key not found (%s)" % (pkeyPath)
            return 0

        return 1

    def UpdateStatus(self):
        """
        Update the status of this request by querying the request server.

        @return: new status
        """

        if not self.CheckPrivateKey():
            return self.status

        if self.server is None or self.token is None:
            self.status = "Invalid"
            return self.status

        proxyEnabled, proxyHost, proxyPort = self.browser.GetProxyInfo()

        certMgr = self.browser.GetCertificateManager()
        if proxyEnabled:
            certReturn = certMgr.CheckRequestedCertificate(self.request, self.token, self.server,
                                                           proxyHost, proxyPort)
        else:
            certReturn = certMgr.CheckRequestedCertificate(self.request, self.token, self.server)

        success, msg = certReturn
        if not success:

            #
            # Map nonobvious errors
            #

            if msg.startswith("Couldn't open certificate file."):
                self.status = "Not ready"
            elif msg.startswith("Couldn't read from certificate file."):
                self.status = "Not ready"
            elif msg.startswith("There is no certificate for this token."):
                self.status = "Request not found"
            else:
                self.status = msg

        else:
            self.status = "Ready for installation"
            self.cert = msg

        self.certReady = success
        self.fullStatus = msg

        return self.status
        
    def GetRequestInfo(self):
        """
        Return the tuple form of this request description.
        """
        
        return (self.request, self.token, self.server, self.creationTime)

    def Format(self):
        """
        Format the certificate request for display in the browser.

        """
        
        typeMeta = self.request.GetMetadata("AG.CertificateManager.requestType")

        if typeMeta is None or typeMeta == "":
            type = "Identity"
        else:
            type = typeMeta[0].upper() + typeMeta[1:]
            
        # subject = str(requestDescriptor.GetSubject())
        
        subject = GetCNFromX509Subject(self.request.GetSubject())
        if self.creationTime is not None:
            date = time.strftime("%x %X", time.localtime(int(self.creationTime)))
        else:
            date = ""

        return [type, subject, date, self.status]        
    

class CertificateStatusBrowser(CertificateBrowserBase):
    def __init__(self, parent, id, certMgr):
        self.updateStatus = 0

        CertificateBrowserBase.__init__(self, parent, id, certMgr)


    def _buildButtons(self, sizer):

        #
        # Buttons that are only valid when a cert is selected.
        #
        self.certOnlyButtons = []

        b = wxButton(self, -1, "Install Certificate")
        EVT_BUTTON(self, b.GetId(), self.OnInstallCert)
        sizer.Add(b, 0, wxEXPAND | wxALL, 3)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Delete Request")
        EVT_BUTTON(self, b.GetId(), self.OnDeleteRequest)
        sizer.Add(b, 0, wxEXPAND | wxALL, 3)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "View request")
        EVT_BUTTON(self, b.GetId(), self.OnViewRequest)
        sizer.Add(b, 0, wxEXPAND | wxALL, 3)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Check status")
        EVT_BUTTON(self, b.GetId(), self.OnCheckStatus)
        sizer.Add(b, 0, wxEXPAND | wxALL, 3)

        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND | wxALL , 3)

        b = wxButton(self, -1, "Request a new certificate")
        EVT_BUTTON(self, b.GetId(), self.OnRequestNewCertificate)
        sizer.Add(b, 0, wxEXPAND | wxALL, 3)

        for b in self.certOnlyButtons:
            b.Enable(0)

    def _buildExtra(self, panel, sizer):
        """
        Put a http proxy panel in the window.
        """

        self.httpProxyPanel = HTTPProxyConfigPanel(panel)
        sizer.Add(self.httpProxyPanel, 0, wxEXPAND)

    def OnRequestNewCertificate(self, event):

        self.certMgr.GetUserInterface().RunCertificateRequestTool(self)

    def OnInstallCert(self, event):
        req = self.GetSelectedCertificate()
        if req is None:
            return

        req.Install()
        

    def OnDeleteRequest(self, event):
        req = self.GetSelectedCertificate()

        dlg = wxMessageDialog(self,
                              "Deleting a certificate request is an irreversible operation.\n" +
                              "If you delete this request, you will not be able to retreive the certificate.\n" +
                              "Really delete certificate request for identity " +
                              req.GetShortName() + "?",
                              "Really delete?",
                              style = wxYES_NO | wxNO_DEFAULT)
        ret = dlg.ShowModal()
        dlg.Destroy()

        if ret == wxID_NO:
            return

        log.debug("Removing request %s", req.GetRequest().GetSubject())
        self.certMgr.GetCertificateRepository().RemoveCertificateRequest(req.GetRequest())

        #
        # Turn off update so the load goes quickly.
        #
        self.updateStatus = 0
        self.Load()

    def OnViewRequest(self, event):

        req = self.GetSelectedCertificate()
        if req is None:
            return

        dlg = CertificateRequestViewer(self, -1, req, self.certMgr)
        dlg.Show()

    def OnCheckStatus(self, event):
        """
        Start a reload after setting the updateStatus flag; we don't
        do an update when we first load the browser because it can be
        an expensive operation.
        """
        
        self.updateStatus = 1

        self.Load()
        
    def OnCertActivated(self, event, req):
        if req is None:
            return

        dlg = CertificateRequestViewer(self, -1, req, self.certMgr)
        dlg.Show()

    def GetProxyInfo(self):
        return self.httpProxyPanel.GetInfo()

    def GetCertificateManager(self):
        return self.certMgr

    #
    # Overrides.
    #

    def OnCertSelected(self, event, cert):
        if cert is None:
            return

        for b in self.certOnlyButtons:
            b.Enable(1)

    def OnCertDeselected(self, event, cert):
        for b in self.certOnlyButtons:
            b.Enable(0)

    def _LoadCerts(self):

        #
        # Set up a progress dialog since this might take some time.
        #

        reqList = self.certMgr.GetPendingRequests()

        if self.updateStatus:
            progressDlg = wxProgressDialog("Checking request status",
                                                "Checking request status",
                                                len(reqList) * 2,
                                                self,
                                                style = wxPD_CAN_ABORT | wxPD_AUTO_HIDE | wxPD_APP_MODAL)
        l = []
        n = 1
        for r in reqList:
            w = CertRequestWrapper(self, r)
            if self.updateStatus:
                ok = progressDlg.Update(n, "Checking %s..." % (w.GetShortName()))
                n += 1

                if not ok:
                    progressDlg.Destroy()
                    self.updateStatus = 0
                else:
                    w.UpdateStatus()

                ok = progressDlg.Update(n)
                if not ok:
                    progressDlg.Destroy()
                    self.updateStatus = 0
                n += 1                
            l.append(w)

        if self.updateStatus:
            progressDlg.Destroy()

        return l
    
    def _FormatCert(self, cert):

        print "Format ", cert
        return cert, cert.Format()

    def _getListColumns(self):
        return ["Certificate Type", "Subject Name", "Date Requested", "Status"]

    def _getListColumnWidths(self):
        return [wxLIST_AUTOSIZE_USEHEADER, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE]

