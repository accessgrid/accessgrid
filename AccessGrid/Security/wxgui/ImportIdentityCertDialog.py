import os

import logging
log = logging.getLogger("AG.CertificateManagerWXGUI")

log.setLevel(logging.DEBUG)

from wxPython.wx import *

from AccessGrid.Security import CertificateRepository
from AccessGrid.UIUtilities import FileLocationWidget

class ImportIdentityCertDialog(wxDialog):

    """
    Dialog for importing a new identity certificate.

    This dialog doesn't actually do the heavy lifting of the
    import, but does obtain the certificate and performs
    some initial verification.

    """

    def __init__(self, parent, certMgr, id = -1, title = "Import Identity Certificate"):
        wxDialog.__init__(self, parent, id, title, size = wxSize(600, 200),
                          style = wxCAPTION | wxRESIZE_BORDER | wxSYSTEM_MENU)

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

        PKCS12. PKCS#12-formatted certificate, containing a private key.
        certFile is the certificate; privateKey is unused (it is part
        of the pkcs12 file).
        
        
        Otherwise, returns None.
        """

        ret = self.ShowModal()
        # print "Ret is", wxID_OK
        if ret != wxID_OK:
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

        topsizer = wxBoxSizer(wxVERTICAL)

        #
        # Introductory text.
        #

        introText = """Enter the pathname to your identity certificate below,
or use the Browse button to browse to it.         
    """
        intro = wxStaticText(self, -1, introText)
        topsizer.Add(intro, 0, wxEXPAND)

        #
        # Certificate file browser
        #

        self.certWidget = FileLocationWidget(self,
                                             "Certificate file",
                                             "Certificate file: ",
                                             [("PEM files (*.pem)", "*.pem"),
                                              ("PKCS12 files (*.p12)", "*.p12"),
                                              ("All files", "*")],
                                             self.OnCertSelect)
        topsizer.Add(self.certWidget, 0, wxEXPAND | wxALL, 3)
        
        #
        # Cert name.
        #
        
        hb = wxBoxSizer(wxHORIZONTAL)

        topsizer.Add(hb, 0, wxEXPAND)

        hb.Add(wxStaticText(self, -1, "Certificate name: "), 0, wxALL | wxALIGN_CENTER_VERTICAL, 3)
        
        self.certName = wxStaticText(self, -1, "")
        hb.Add(self.certName, 1, wxALL | wxALIGN_CENTER_VERTICAL, 3)

        #
        # Separate from PK stuff.
        #

        topsizer.Add(wxStaticLine(self, -1), 0, wxEXPAND | wxTOP | wxBOTTOM, 4)

        #
        # Private key text.
        #

        pkText = """\
Enter the filename of the private key for this identity
certificate below, or use the Browse button to browse for
it. The private key may be included in the certificate file.
    """
        sp = wxStaticText(self, -1, pkText)
        
        topsizer.Add(sp, 0, wxEXPAND)

        #
        # Private key box.
        #
        # Two radio buttons, plus another text/textctrl/browse button.
        #

        self.pkCertRadioButton = rb1 = wxRadioButton(self, -1, "Load private key from certificate file", style = wxRB_GROUP)
	self.pkFileRadioButton = rb2 = wxRadioButton(self, -1,
                                                     "Load private key from separate file")

        EVT_RADIOBUTTON(self, rb1.GetId(),
                        lambda event, self = self: self.SetRequirePKFile(0))
        
        EVT_RADIOBUTTON(self, rb2.GetId(), 
                        lambda event, self = self: self.SetRequirePKFile(1))

        topsizer.Add(rb1, 0, wxEXPAND | wxALL, 3)
        topsizer.Add(rb2, 0, wxEXPAND | wxALL, 3)

        self.pkWidget = FileLocationWidget(self,
                                           "Private key file",
                                           "Private key file: ",
                                           [("PEM files (*.pem)", "*.pem"),
                                            ("All files", "*")],
                                           self.OnPKSelect)
        topsizer.Add(self.pkWidget, 0, wxEXPAND | wxALL, 3)

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
            cns = filter(lambda a: a[0] == "CN",
                         cert.get_subject().get_name_components())
            name = ",".join(map(lambda a: a[1], cns))
            self.certName.SetLabel(name)
                
        elif certType == "PKCS12":

            if cert:

                xcert = cert.get_certificate()

                cns = filter(lambda a: a[0] == "CN",
                             xcert.get_subject().get_name_components())
                name = ",".join(map(lambda a: a[1], cns))
                self.certName.SetLabel(name)

        

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
            #print "Retrying"
            return
        else:
            self.EndModal(wxID_CANCEL)

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
            dlg = wxMessageDialog(self,
                                  "No certificate pathname provided.",
                                  "Import error",
                                  style = wxOK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # Check for invalid file.
        #

        if not os.path.isfile(certPath):
            dlg = wxMessageDialog(self,
                                  "Certificate pathname %s is not a readable file." % (certPath),
                                  "Import error",
                                  style = wxOK)
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

            dlg = wxMessageDialog(self,
                                  "Cannot identify the type of this certificate; it might not be valid\n\n" +
                                  "Attempt to import anyway?",
                                  "Possibly invalid certificate",
                                  style = wxYES_NO | wxNO_DEFAULT)
            rc = dlg.ShowModal()
            dlg.Destroy()

            if rc != wxID_YES:
                return
            else:
                suppressDialogs = 1

        (certType, cert, needPK ) = classify

        if certType == "Unknown" and not suppressDialogs:
            dlg = wxMessageDialog(self,
                                  "Cannot identify the type of this certificate; it might not be valid\n\n" +
                                  "Attempt to import anyway?",
                                  "Possibly invalid certificate",
                                  style = wxYES_NO | wxNO_DEFAULT)
            rc = dlg.ShowModal()
            dlg.Destroy()

            if rc != wxID_YES:
                return
            else:
                suppressDialogs = 1

        if needPK:
            #
            # Check if a private key was entered.
            #

            pkPath = self.pkWidget.GetPath()

            if pkPath == "" and not suppressDialogs:
                dlg = wxMessageDialog(self,
                                     "Private key file is required, but was not provided.\n\n" +
                                      "Attempt to import anyway?",
                                      "Private key required.",
                                      style = wxYES_NO | wxNO_DEFAULT)
                rc = dlg.ShowModal()
                dlg.Destroy()

                if rc != wxID_YES:
                    return
                else:
                    suppressDialogs = 1

            if pkPath != "" and not os.path.isfile(pkPath):
                dlg = wxMessageDialog(self,
                                      "Private key pathname %s is not a readable file." % (pkPath),
                                      "Import error",
                                      style = wxOK)
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

            if certType == "PKCS12":
                xcert = cert.get_certificate()
            else:
                xcert = cert

            repo = self.certMgr.GetCertificateRepository()
            matchingCerts = repo.FindCertificatesWithSubject(str(xcert.get_subject()))

            validCerts = filter(lambda a: not a.IsExpired(), matchingCerts)

            if validCerts != []:
                dlg = wxMessageDialog(
                    self, 
                    "Another certificate with this name is already present.\n\n" +
                    "Attempt to import anyway?",
                    "Certificate already exists",
                    style = wxYES_NO | wxNO_DEFAULT)
                ret = dlg.ShowModal()
                
                if ret == wxID_NO:
                    return
                
        self.certType = certType
        self.certFile = certPath
        self.pkFile = pkPath

        self.EndModal(wxID_OK)
            

if __name__ == "__main__":

    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(logging.StreamHandler())

    pyapp = wxPySimpleApp()

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
    
