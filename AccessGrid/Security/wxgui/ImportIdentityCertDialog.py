import os

import logging
log = logging.getLogger("AG.CertificateManagerWXGUI")

log.setLevel(logging.DEBUG)

import wx

from AccessGrid.Security import CertificateRepository
from AccessGrid.UIUtilities import FileLocationWidget

class ImportIdentityCertDialog(wx.Dialog):

    """
    Dialog for importing a new identity certificate.

    This dialog doesn't actually do the heavy lifting of the
    import, but does obtain the certificate and performs
    some initial verification.

    """

    def __init__(self, parent, certMgr, id = -1, title = "Import Identity Certificate"):
        wx.Dialog.__init__(self, parent, id, title, size = wx.Size(600, 200),
                          style = wx.CAPTION | wx.RESIZE_BORDER | wx.SYSTEM_MENU)

        self.certMgr = certMgr
        
        self.__build()

        #
        # initialize lastFilterIndex for cert file browser.
        #

        self.lastFilterIndex = 0

    def Run(self):
        """
        Run the dialog.

        If successful, returns a tuple (certType, certFile, privateKey).

        certType is one of the following:

        PEM. PEM-formatted X509 certificate in certFile.
        privateKey is the file containing the private key. If it's in
        certFile, privateKey = certFile
        
        Otherwise, returns None.
        """

        ret = self.ShowModal()
        # print "Ret is", wx.ID_OK
        if ret != wx.ID_OK:
            return None

        #
        # Success. On success, the dialog has filled in
        # self.certFile and self.signingPolicy.
        #

        return self.certType, self.certFile, self.pkFile

    def __build(self):
        """
        Build import dialog.

        Overall layout:

        [Intro text]
        
        Certificate file: [------------------------------] [Browse]
        Certificate name: [static text for name]
        
        [Private key text]

        [X] Load private key from certificate file.
        [X] Load private key from separate file.

        Private key file: [--------------------------] [ Browse ]

        ------

        [Import] [Cancel]

        """

        topsizer = wx.BoxSizer(wx.VERTICAL)

        #
        # Introductory text.
        #

        introText = """Enter the pathname to your identity certificate below,
or use the Browse button to browse to it.         
    """
        intro = wx.StaticText(self, -1, introText)
        topsizer.Add(intro, 0, wx.EXPAND)

        #
        # Certificate file browser
        #

        self.certWidget = FileLocationWidget(self,
                                             "Certificate file",
                                             "Certificate file: ",
                                             [("PEM files (*.pem)", "*.pem"),
                                              ("All files", "*")],
                                             self.OnCertSelect)
        topsizer.Add(self.certWidget, 0, wx.EXPAND | wx.ALL, 3)
        
        #
        # Cert name.
        #
        
        hb = wx.BoxSizer(wx.HORIZONTAL)

        topsizer.Add(hb, 0, wx.EXPAND)

        hb.Add(wx.StaticText(self, -1, "Certificate name: "), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)
        
        self.certName = wx.StaticText(self, -1, "")
        hb.Add(self.certName, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)

        #
        # Separate from PK stuff.
        #

        topsizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)

        #
        # Private key text.
        #

        pkText = """\
Enter the filename of the private key for this identity
certificate below, or use the Browse button to browse for
it. The private key may be included in the certificate file.
    """
        sp = wx.StaticText(self, -1, pkText)
        
        topsizer.Add(sp, 0, wx.EXPAND)

        #
        # Private key box.
        #
        # Two radio buttons, plus another text/textctrl/browse button.
        #

        self.pkCertRadioButton = rb1 = wx.RadioButton(self, -1, "Load private key from certificate file", style = wx.RB_GROUP)
        self.pkFileRadioButton = rb2 = wx.RadioButton(self, -1,
                                                     "Load private key from separate file")

        wx.EVT_RADIOBUTTON(self, rb1.GetId(),
                        lambda event, self = self: self.SetRequirePKFile(0))
        
        wx.EVT_RADIOBUTTON(self, rb2.GetId(), 
                        lambda event, self = self: self.SetRequirePKFile(1))

        topsizer.Add(rb1, 0, wx.EXPAND | wx.ALL, 3)
        topsizer.Add(rb2, 0, wx.EXPAND | wx.ALL, 3)

        self.pkWidget = FileLocationWidget(self,
                                           "Private key file",
                                           "Private key file: ",
                                           [("PEM files (*.pem)", "*.pem"),
                                            ("All files", "*")],
                                           self.OnPKSelect)
        topsizer.Add(self.pkWidget, 0, wx.EXPAND | wx.ALL, 3)

        #
        # Import/Cancel buttons
        #

        hb = wx.BoxSizer(wx.HORIZONTAL)
        b = wx.Button(self, -1, "Import")
        wx.EVT_BUTTON(self, b.GetId(), self.OnImport)
        hb.Add(b, 0, wx.ALL, 3)

        b = wx.Button(self, -1, "Cancel")
        wx.EVT_BUTTON(self, b.GetId(),
                   lambda event, self = self: self.EndModal(wx.ID_CANCEL))
        hb.Add(b, 0, wx.ALL, 3)

        topsizer.Add(hb, 0, wx.ALIGN_RIGHT)

        #
        # Default to using file.
        #
        self.SetRequirePKFile(1)

        #
        # done with gui setup.
        #
        
        self.SetSizer(topsizer)
        self.SetAutoLayout(1)
        self.Fit()

    def SetRequirePKFile(self, requireFile):
        self.RequirePKFile = requireFile
        self.pkWidget.Enable(requireFile)
        #print "Set radio button to ", requireFile
        self.pkFileRadioButton.SetValue(requireFile)
        self.pkCertRadioButton.SetValue(not requireFile)
        
    def OnPKSelect(self, widget, file):
        self.pkFile = file

    def OnCertSelect(self, widget, path):
        """
        Invoked when a new cert file has been chosen, either by
        a file browser or by the user hitting enter in the
        cert file text widget.
        """

        classify = CertificateRepository.ClassifyCertificate(path)

        if classify is None:
            self.certName.SetLabel("")
            return
        
        (certType, cert, needPkey) = classify

        self.SetRequirePKFile(needPkey)

        #
        # Clear name first; if we find one we'll set it
        # below.
        #
        self.certName.SetLabel("")

        if certType == "PEM":
            self.certName.SetLabel(cert.get_subject().CN)
                
        

    def ImportFail(self, message):
        """
        The import will fail. Show message in a dialog, query the user
        to see if he wants to try again or not.

        """

        dlg = wx.MessageDialog(self, "%s\n\nRetry import?" % (message),
                              "Import problem",
                              style = wx.YES_NO | wx.YES_DEFAULT)
        ret = dlg.ShowModal()

        if ret == wx.ID_YES:
            #print "Retrying"
            return
        else:
            self.EndModal(wx.ID_CANCEL)

    def OnImport(self, event):
        """
        User pressed "Import".

        Perform some preliminary tests so that we can report status
        back to the user and possibly allow him to go back to the dialog
        to fix things.

        """
        
        certPath = self.certWidget.GetPath()
        pkPath = None

        #
        # Set this flag to suppress further dialogs.
        #

        suppressDialogs = 0

        #
        # Warn if no cert is provided.
        #

        if certPath == "":
            dlg = wx.MessageDialog(self,
                                  "No certificate pathname provided.",
                                  "Import error",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # Check for invalid file.
        #

        if not os.path.isfile(certPath):
            dlg = wx.MessageDialog(self,
                                  "Certificate pathname %s is not a readable file." % (certPath),
                                  "Import error",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # Attempt to classify the certificate.
        #

        classify = CertificateRepository.ClassifyCertificate(certPath)

        # print "Classify %s returns %s" % (certPath, classify)

        #
        # If it fails, we're most likely not going to be able
        # to import it. Give the user a chance to attempt to import,
        # though, in case the classify missed something.
        #


        if not classify and not suppressDialogs:

            dlg = wx.MessageDialog(self,
                                  "Cannot identify the type of this certificate; it might not be valid\n\n" +
                                  "Attempt to import anyway?",
                                  "Possibly invalid certificate",
                                  style = wx.YES_NO | wx.NO_DEFAULT)
            rc = dlg.ShowModal()
            dlg.Destroy()

            if rc != wx.ID_YES:
                return
            else:
                suppressDialogs = 1

        (certType, cert, needPK ) = classify

        if certType == "Unknown" and not suppressDialogs:
            dlg = wx.MessageDialog(self,
                                  "Cannot identify the type of this certificate; it might not be valid\n\n" +
                                  "Attempt to import anyway?",
                                  "Possibly invalid certificate",
                                  style = wx.YES_NO | wx.NO_DEFAULT)
            rc = dlg.ShowModal()
            dlg.Destroy()

            if rc != wx.ID_YES:
                return
            else:
                suppressDialogs = 1

        if needPK:
            #
            # Check if a private key was entered.
            #

            pkPath = self.pkWidget.GetPath()

            if pkPath == "" and not suppressDialogs:
                dlg = wx.MessageDialog(self,
                                     "Private key file is required, but was not provided.\n\n" +
                                      "Attempt to import anyway?",
                                      "Private key required.",
                                      style = wx.YES_NO | wx.NO_DEFAULT)
                rc = dlg.ShowModal()
                dlg.Destroy()

                if rc != wx.ID_YES:
                    return
                else:
                    suppressDialogs = 1

            if pkPath != "" and not os.path.isfile(pkPath):
                dlg = wx.MessageDialog(self,
                                      "Private key pathname %s is not a readable file." % (pkPath),
                                      "Import error",
                                      style = wx.OK)
                dlg.ShowModal()
                dlg.Destroy()
                return
        else:
            #
            # If we are PEm and we don't need a private key, that means the
            # private key is in the same file as the cert.
            #

            if certType == "PEM":
                pkPath = certPath
            

        #
        # Check to see if we already have this certificate installed.
        #

        if cert:

            repo = self.certMgr.GetCertificateRepository()
            matchingCerts = repo.FindCertificatesWithSubject(str(cert.get_subject()))

            validCerts = filter(lambda a: not a.IsExpired(), matchingCerts)

            if validCerts != []:
                dlg = wx.MessageDialog(
                    self, 
                    "Another certificate with this name is already present.\n\n" +
                    "Attempt to import anyway?",
                    "Certificate already exists",
                    style = wx.YES_NO | wx.NO_DEFAULT)
                ret = dlg.ShowModal()
                
                if ret == wx.ID_NO:
                    return
                
        self.certType = certType
        self.certFile = certPath
        self.pkFile = pkPath

        self.EndModal(wx.ID_OK)
            

if __name__ == "__main__":

    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(logging.StreamHandler())

    pyapp = wx.PySimpleApp()

    import AccessGrid.Toolkit
    app = AccessGrid.Toolkit.WXGUIApplication()
    # app.GetCertificateManager().InitEnvironment()

    # id = app.GetCertificateManager().GetDefaultIdentity()
    # print "id is ", id.GetSubject()

    ca = app.GetCertificateManager().GetCACerts()

    # d = ExportIDCertDialog(None, id)

    # d = ExportCACertDialog(None, ca[0])

    d = ImportIdentityCertDialog(None, app.GetCertificateManager())
    
    ret = d.Run()

    if ret is not None:
        print "ret is ", ret
    
