import os

import logging
log = logging.getLogger("AG.CertificateManagerWXGUI")

from wxPython.wx import *

from AccessGrid.Security import CertificateRepository

class ImportCACertDialog(wxDialog):

    """
    Dialog for importing a new trusted CA certificate.

    This dialog doesn't actually do the heavy lifting of the
    import, but does obtain the certificate and signing policy paths
    and some initial verification.

    """

    #
    # signing policy modes
    #

    SPConstruct = 1
    SPFile = 2

    def __init__(self, parent, certMgr, id = -1, title = "Import Trusted CA Certificate"):
        wxDialog.__init__(self, parent, id, title, size = wxSize(600, 200),
                          style = wxCAPTION | wxRESIZE_BORDER | wxSYSTEM_MENU)

        self.certMgr = certMgr
        
        self.__build()

        #
        # initialize lastFilterIndex for cert file browser.
        #

        self.lastFilterIndex = 0
        self.lastSPFilterIndex = 0

    def Run(self):
        """
        Run the dialog.

        If successful, returns a tuple (cert filename, signing-policy).
        Signing-policy is a text string.
        
        Otherwise, returns None.
        """

        ret = self.ShowModal()
        print "Ret is", wxID_OK
        if ret != wxID_OK:
            return None

        #
        # Success. On success, the dialog has filled in
        # self.certFile and self.signingPolicy.
        #

        return self.certFile, self.signingPolicy

    def __build(self):
        """
        Build import dialog.

        Overall layout:

        [Intro text]
        
        Certificate file: [------------------------------] [Browse]
        Certificate name: [static text for name]
        
        [Signing policy text]

        [X] Create signing policy from certificate
        [X] Create signing policy from file

        Signing policy file: [--------------------------] [ Browse ]

        ------

        [Import] [Cancel]

        We force the two static text strings on the file lines to be the
        same size so it's not too ugly.

        """

        topsizer = wxBoxSizer(wxVERTICAL)

        #
        # Create these and make them align in size.
        #
        static1 = wxStaticText(self, -1, "Certificate file:")
        static2 = wxStaticText(self, -1, "Signing policy file:")
        s1 = static1.GetSize()
        s2 = static2.GetSize()

        print "S1=%s S2=%s" % (s1, s2)

        if s1.GetWidth() > s2.GetWidth():
            s2.SetWidth(s1.GetWidth())
            static2.SetSize(s2)
            print "Force s2 to be ", s2
        else:
            s1.SetWidth(s2.GetWidth())
            static1.SetSize(s1)
            print "Force s1 to be ", s1
        
        #
        # Introductory text.
        #

        introText = """This talks about the stuff that one needs to know about cert imports.
    """
        intro = wxStaticText(self, -1, introText)
        topsizer.Add(intro, 0, wxEXPAND)

        #
        # Certificate file browser
        #

        hb = wxBoxSizer(wxHORIZONTAL)

        topsizer.Add(hb, 0, wxEXPAND)
        
        hb.Add(static1, 0, wxALIGN_CENTER_VERTICAL | wxALL, 3)

        self.certFileText = wxTextCtrl(self, -1, style = wxTE_PROCESS_ENTER)
        hb.Add(self.certFileText, 1, wxALL | wxALIGN_CENTER_VERTICAL, 3)
        EVT_TEXT_ENTER(self, self.certFileText.GetId(), self.OnCertFileEnter)

        b = wxButton(self, -1, "Browse")
        hb.Add(b, 0, wxALL, 3)
        EVT_BUTTON(self, b.GetId(), self.OnCertBrowse)

        #
        # Cert name.
        #
        
        hb = wxBoxSizer(wxHORIZONTAL)

        topsizer.Add(hb, 0, wxEXPAND)

        hb.Add(wxStaticText(self, -1, "Certificate name: "), 0, wxALL | wxALIGN_CENTER_VERTICAL, 3)
        
        self.certName = wxStaticText(self, -1, "")
        hb.Add(self.certName, 1, wxALL | wxALIGN_CENTER_VERTICAL, 3)

        #
        # Separate from SP stuff.
        #

        topsizer.Add(wxStaticLine(self, -1), 0, wxEXPAND | wxTOP | wxBOTTOM, 4)


        #
        # Signing policy text.
        #

        spText = """
This talks
about the weird stuff that one
needs to know about signing policies.
    """
        sp = wxStaticText(self, -1, spText)
        
        topsizer.Add(sp, 0, wxEXPAND)

        #
        # Signing policy box
        #
        # Two radio buttons, plus another text/textctrl/browse button.
        #

        rb1 = wxRadioButton(self, -1, "Construct from certificate", style = wxRB_GROUP)
        EVT_RADIOBUTTON(self, rb1.GetId(),
                        lambda event, self = self: self.setSPMode(self.SPConstruct))
        
        self.fileRadioButton = rb2 = wxRadioButton(self, -1, "Import from file")
        EVT_RADIOBUTTON(self, rb2.GetId(), 
                        lambda event, self = self: self.setSPMode(self.SPFile))

        topsizer.Add(rb1, 0, wxEXPAND | wxALL, 3)
        topsizer.Add(rb2, 0, wxEXPAND | wxALL, 3)

        #
        # Hsizer hb for the text label, file location, and browse button
        #

        hb = wxBoxSizer(wxHORIZONTAL)

        topsizer.Add(hb, 0, wxEXPAND | wxALL, 3)

        hb.Add(static2, 0, wxALIGN_CENTER_VERTICAL | wxALL, 3)

        self.signingPolicyFileText = wxTextCtrl(self, -1, style = wxTE_PROCESS_ENTER)
        EVT_TEXT_ENTER(self, self.signingPolicyFileText.GetId(), self.OnSPFileEnter)

        self.signingPolicyBrowseButton = b = wxButton(self, -1, "Browse")
        EVT_BUTTON(self, b.GetId(), self.OnSigningPolicyBrowse)

        hb.Add(self.signingPolicyFileText, 1, wxALL | wxEXPAND, 3)
        hb.Add(b, 0, wxALL, 3)

        #
        # and a hbox with signing policy's CA name.
        #
        
        hb = wxBoxSizer(wxHORIZONTAL)

        topsizer.Add(hb, 0, wxEXPAND)

        hb.Add(wxStaticText(self, -1, "Signing policy for CA: "), 0, wxALL | wxALIGN_CENTER_VERTICAL, 3)
        
        self.spName = wxStaticText(self, -1, "")
        hb.Add(self.spName, 1, wxALL | wxALIGN_CENTER_VERTICAL, 3)

        #
        # Import/Cancel buttons
        #

        hb = wxBoxSizer(wxHORIZONTAL)
        b = wxButton(self, -1, "Import")
        EVT_BUTTON(self, b.GetId(), self.OnImport)
        hb.Add(b, 0, wxALL, 3)

        b = wxButton(self, -1, "Cancel")
        EVT_BUTTON(self, b.GetId(),
                   lambda event, self = self: self.EndModal(wxID_CANCEL))
        hb.Add(b, 0, wxALL, 3)

        topsizer.Add(hb, 0, wxALIGN_RIGHT)

        #
        # Default to using file.
        #
        self.setSPMode(self.SPFile)

        #
        # done with gui setup.
        #
        
        self.SetSizer(topsizer)
        self.SetAutoLayout(1)
        self.Fit()

    def OnCertFileEnter(self, event):
        print "User hit enter"
        self.SetNewCertFile(self.certFileText.GetValue())

    def OnSPFileEnter(self, event):
        print "User hit enter on sp"
        self.SetNewSPFile(self.signingPolicyFileText.GetValue())

    def setSPMode(self, mode):
        self.spMode = mode
        enable = mode == self.SPFile
        self.fileRadioButton.SetValue(enable)
        self.signingPolicyFileText.Enable(enable)
        self.signingPolicyBrowseButton.Enable(enable)
        
    def ImportFail(self, message):
        """
        The import will fail. Show message in a dialog, query the user
        to see if he wants to try again or not.

        """

        dlg = wxMessageDialog(self, "%s\n\nRetry import?" % (message),
                              "Import problem",
                              style = wxYES_NO | wxYES_DEFAULT)
        ret = dlg.ShowModal()

        if ret == wxID_YES:
            print "Retrying"
            return
        else:
            self.EndModal(wxID_CANCEL)

    def OnImport(self, event):
        """
        User pressed "Import".

        Doublecheck validity of files.
        If we're creating a signing policy from the cert, create it, write
        to a temp file.
        """
        
        #
        # First check to see that the filenames aren't empty.
        #

        certPath = self.certFileText.GetValue().strip()
        print "certpath='%s'" % (certPath)
        if certPath == "":
            self.ImportFail("No certificate file selected.")
            return

        #
        # Does it exist?
        #

        if not os.path.isfile(certPath):
            self.ImportFail("Certificate file %s does not exist." % (certPath))
            return

        #
        # Load up a cert object from the certificate.
        #

        try:
            cert = CertificateRepository.Certificate(certPath)

        except Exception, e:
            self.ImportFail("Certificate file %s\ncannot be loaded. Is it really a certificate?"
                             % (certPath))
            return

        #
        # Check to see if we already have this certificate installed.
        #

        repo = self.certMgr.GetCertificateRepository()
        matchingCerts = repo.FindCertificatesWithSubject(str(cert.GetSubject()))

        validCerts = filter(lambda a: not a.IsExpired(), matchingCerts)

        if matchingCerts != []:
            dlg = wxMessageDialog(self, 
                                  "Another certificate with this name is already present\n\n" +
                                  "Attempt to import anyway?",
                                  "Certificate already exists",
                                  style = wxYES_NO | wxNO_DEFAULT)
            ret = dlg.ShowModal()

            if ret == wxID_NO:
                return

        #
        # See if we have to construct a signing policy. If we do, do so; otherwise
        # check the existence of the path to the signing policy file.
        #

        if self.spMode == self.SPFile:

            spFile = self.signingPolicyFileText.GetValue().strip()

            if spFile == "":
                self.ImportFail("No signing policy file selected.")
                return

            #
            # Does it exist?
            #

            if not os.path.isfile(spFile):
                self.ImportFail("Signing policy file %s does not exist." % (spFile))
                return

            #
            # Parse the signing policy.
            #

            caName = None
            try:
                fh = open(spFile)
                caName = CertificateRepository.ParseSigningPolicy(fh)
                fh.close()

            except Exception, e:
                self.ImportFail("Signing policy file %s\ncannot be parsed." % (spFile))
                return
            
            #
            # See if the CA name in the signing policy matches the subject name
            # of the certificate.
            #
            # Since our parsing may not be perfect, we give the user the option
            # to go ahead and import anyway.
            #

            subj = str(cert.GetSubject())
            if caName != subj:
                dlg = wxMessageDialog(self, 
                                      ("Name in certificate does not match name in signing policy:\n" +
                                       "   certificate:    %(subj)s\n" +
                                       "   signing policy: %(caName)s\n" +
                                       "Import anyway?" ) % locals(),
                                      "Error in signing policy",
                                      style = wxYES_NO | wxNO_DEFAULT)
                ret = dlg.ShowModal()

                if ret == wxID_NO:
                    return
            self.signingPolicy = open(spFile).read()
        else:
            #
            # We need to construct a signing policy.
            #

            self.signingPolicy = CertificateRepository.ConstructSigningPolicy(cert)

        self.certFile = certPath

        self.EndModal(wxID_OK)
            

    def OnSigningPolicyBrowse(self, event):
        """
        Browse for a signing policy file.
        """
        
        #
        # Defaults for file browser.
        #
        dir = file = ""

        path = self.signingPolicyFileText.GetValue().strip()
        if path != "":
            if os.path.isdir(path):
                dir = path
            elif os.path.isfile(path):
                dir, file = os.path.split(path)
            else:
                #
                # User entered an invalid file; point the browser
                # at the directory containing that file.
                #
                dir, file = os.path.split(path)
                file = ""

        #
        # Construct and show browser.
        #
            
        dlg = wxFileDialog(None, "Choose a signing policy file",
                           defaultDir = dir,
                           defaultFile = file,
                           wildcard = "Signing policy files (*.signing_policy)|*.signing_policy|All files|*",
                           style = wxOPEN)
        dlg.SetFilterIndex(self.lastSPFilterIndex)
        rc = dlg.ShowModal()

        #
        # If user cancelled, just return.
        #

        if rc != wxID_OK:
            dlg.Destroy()
            return

        #
        # Retain the last filter index so the same set of files shows up next time.
        #

        self.lastSPFilterIndex = dlg.GetFilterIndex()

        #
        # Process selected path.
        #

        path = dlg.GetPath()
        self.signingPolicyFileText.SetValue(path)
        self.signingPolicyFileText.SetInsertionPointEnd()

        self.SetNewSPFile(path)

    def OnCertBrowse(self, event):
        """
        Allow the user to browse for a CA certificate file.

        If a .signing_policy file exists with the same name as the cert
        file, change the dialog to load-signing-policy mode and fill
        in the filename.

        """
        
        print "Browse for cert"

        #
        # Defaults for file browser.
        #
        dir = file = ""

        path = self.certFileText.GetValue().strip()
        if path != "":
            if os.path.isdir(path):
                dir = path
            elif os.path.isfile(path):
                dir, file = os.path.split(path)
            else:
                #
                # User entered an invalid file; point the browser
                # at the directory containing that file.
                #
                dir, file = os.path.split(path)
                file = ""

        #
        # Construct and show browser.
        #
            
        dlg = wxFileDialog(None, "Choose a trusted CA certificate file",
                           defaultDir = dir,
                           defaultFile = file,
                           wildcard = "Trusted cert files (*.0)|*.0|PEM Files (*.pem)|*.pem|All files|*",
                           style = wxOPEN)
        dlg.SetFilterIndex(self.lastFilterIndex)
        rc = dlg.ShowModal()

        #
        # If user cancelled, just return.
        #

        if rc != wxID_OK:
            dlg.Destroy()
            return

        #
        # Retain the last filter index so the same set of files shows up next time.
        #

        self.lastFilterIndex = dlg.GetFilterIndex()

        #
        # Process selected path.
        #

        dir = dlg.GetDirectory()
        file = dlg.GetFilename()

        log.debug("Chose file=%s dir=%s", file, dir)

        path = os.path.join(dir, file)

        self.certFileText.SetValue(path)
        self.certFileText.SetInsertionPointEnd()

        self.SetNewCertFile(path)

    def SetNewCertFile(self, path):
        """
        Invoked when a new cert file has been chosen, either by
        a file browser or by the user hitting enter in the
        cert file text widget.
        """

        file, dir = os.path.split(path)
        
        root, ext = os.path.splitext(path)
        sp = os.path.join(dir, "%s.signing_policy" % (root))

        print "Check sp file ", sp
        print "path is ", path
        if os.path.isfile(sp):
            #
            # We have a signing policy.
            #
            # Set mode to load SP from a file, and fill in the pathname.
            #

            self.setSPMode(self.SPFile)
            self.signingPolicyFileText.SetValue(sp)
            self.signingPolicyFileText.SetInsertionPointEnd()
            self.SetNewSPFile(sp)

        else:
            #
            # if there wasn't one there, clear out the
            # sp text field so we don't get a spurious value.
            #

            self.signingPolicyFileText.SetValue("")
            self.SetNewSPFile(None)
            

        #
        # Inspect the certificate to determine its name.
        # Fill in the certName field in the GUI.
        #

        try:
            cert = CertificateRepository.Certificate(path)

            name = cert.GetShortSubject()
            print "Got cert ", name
            self.certName.SetLabel(name)

        except Exception, e:
            #
            # We couldn't load the cert for some reason, clear out the
            # name field.
            #
            self.certName.SetLabel("")

    def SetNewSPFile(self, path):
        """
        Invoked when a new signing policy file has been chosen, either by
        a file browser or by the user hitting enter in the
        signing policy file text widget.
        """

        #
        # Inspect the signing policy file to determine its name.
        # Fill in the spName field in the GUI.
        #

        caName = None

        try:
            fh = open(path)
            caName = CertificateRepository.ParseSigningPolicy(fh)

        except Exception, e:
            #
            # We couldn't load the signing policy for some reason, clear out the
            # name field.
            #
            pass

        if caName is None:
            self.spName.SetLabel("")
        else:
            m = re.search(r"CN=([^/]*)/?", caName)
            if m:
                caName = m.group(1)
                
            self.spName.SetLabel(caName)

