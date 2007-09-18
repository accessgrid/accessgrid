#-----------------------------------------------------------------------------
# Name:        ImportExportUtils.py
# Purpose:     Cert management code - import and export utilities and small dialogs.
#
# Author:      Robert Olson
#
# Created:     2003
# RCS-ID:      $Id: ImportExportUtils.py,v 1.8 2007-09-18 20:23:45 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

__revision__ = "$Id: ImportExportUtils.py,v 1.8 2007-09-18 20:23:45 turam Exp $"
__docformat__ = "restructuredtext en"

import time
import string

import os
import os.path
import re
import shutil

import wx

from AccessGrid.UIUtilities import MessageDialog, ErrorDialog, ErrorDialogWithTraceback
from AccessGrid import Log
from AccessGrid import Toolkit

log = Log.GetLogger(Log.CertificateManagerWXGUI)

from AccessGrid.Security import CertificateManager
from AccessGrid.Security import CertificateRepository

def ValidateExportPath(path):
    """
    Validate the path for exporting.

    @param path: Pathname to be validated.
    
    @return: A tuple (success, message).

    Success is 0 for success, 1 for can't write, 2 for file exists. Yes, this
    is a little arbitrary but this isn't a general purpose routine, it's to
    make the code clearer in the dialogs.
    """
        
    if os.path.isfile(path):
        return (2, "Path %s already exists" % (path))

    if os.path.isdir(path):
        return (1, "Path %s is a directory" % (path))

    dir, file = os.path.split(path)
    if not os.path.isdir(dir):
        return (1, "Target directory %s does not exist" % (dir))

    #
    # That's all for now.
    #

    return (0, "OK")

class ExportIDCertDialog(wx.Dialog):
    """
    Dialog for exporting an identity certificate.

    User can select to have the cert and key in one file or two.

           _
          |X|  Cert and key in one file
           _
          |_|  Cert and key in separate files

                                                 _________
      Certificate file: ____________________     |_Browse_|

                                                 _________
      Private key file: ____________________     |_Browse_|

       ________    ________
      |_Export_|  |_Cancel_|

    When the one-file option is selected, the private key file items
    are greyed out.

    """

    def __init__(self, parent, cert, id = -1, title = "Export Identity Certificate"):
        wx.Dialog.__init__(self, parent, id, title,
                          size = wx.Size(600,200),
                          style = wx.CAPTION | wx.RESIZE_BORDER | wx.SYSTEM_MENU)

        self.cert = cert

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

        #
        # Title.
        #


        hb = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self, -1, "Export identity ")
        t.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))

        hb.Add(t, 0)

        t = wx.StaticText(self, -1, str(cert.GetShortSubject()))
        t.SetFont(wx.Font(12, wx.SWISS, wx.ITALIC, wx.BOLD))

        hb.Add(t, 0)
        self.sizer.Add(hb, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Create radio boxes.
        #

        rb1 = wx.RadioButton(self, -1, "Write certificate and private key to a single file",
                                   style = wx.RB_GROUP)
        rb2 = wx.RadioButton(self, -1, "Write certificate and private key to separate files")
        EVT_RADIOBUTTON(self, rb1.GetId(), self.OnSelectOne)
        EVT_RADIOBUTTON(self, rb2.GetId(), self.OnSelectSep)

        self.sizer.Add(rb1, 0, wx.EXPAND | wx.ALL, 3)
        self.sizer.Add(rb2, 0, wx.EXPAND | wx.ALL, 3)

        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND)

        #
        # Create text input grid.
        #

        gs = wx.FlexGridSizer(cols = 3, hgap = 3, vgap = 3)

        t = wx.StaticText(self, -1, "Certificate file:")
        gs.Add(t, 0, wx.ALIGN_CENTER_VERTICAL)
        self.certFileText = wx.TextCtrl(self, -1, "")
        gs.Add(self.certFileText, 1, wx.EXPAND)
        b = wx.Button(self, -1, "Browse")
        EVT_BUTTON(self, b.GetId(), self.OnCertBrowse)
        gs.Add(b, 0)

        t = wx.StaticText(self, -1, "Private key file:")
        gs.Add(t, 0, wx.ALIGN_CENTER_VERTICAL)
        self.keyFileText = wx.TextCtrl(self, -1, "")
        gs.Add(self.keyFileText, 1, wx.EXPAND)
        b = wx.Button(self, -1, "Browse")
        EVT_BUTTON(self, b.GetId(), self.OnKeyBrowse)
        gs.Add(b, 0)

        gs.AddGrowableCol(1)

        self.sizer.Add(gs, 1, wx.EXPAND | wx.ALL, 4)

        #
        # These will get disabled if we're not using a separate key file.
        #
        self.keyWidgets = [t, self.keyFileText, b]

        #
        # Initialize to one file.
        #

        rb1.SetValue(1)
        self.OnSelectOne(None)

        #
        # And the export/cancel buttons.
        #

        hs = wx.BoxSizer(wx.HORIZONTAL)
        b = wx.Button(self, -1, "Export Certificate")
        b.SetDefault()
        EVT_BUTTON(self, b.GetId(), self.OnExport)
        hs.Add(b, 0, wx.ALL, 4)
        
        b = wx.Button(self, wx.ID_CANCEL, "Cancel")
        # EVT_BUTTON(self, b.GetId(), self.OnCancel)
        hs.Add(b, 0, wx.ALL, 4)

        self.sizer.Add(hs, 0, wx.ALIGN_CENTER_HORIZONTAL)
        
    def enableKeyWidgets(self, val):
        for w in self.keyWidgets:
            w.Enable(val)

    def OnSelectOne(self, event):
        print "Selected one file"
        self.enableKeyWidgets(0)
        self.useKeyFile = 0

    def OnSelectSep(self, event):
        print "Selected separate files"
        self.enableKeyWidgets(1)
        self.useKeyFile = 1

    def OnCertBrowse(self, event):
        self.HandleBrowse("Choose certificate file", self.certFileText)

    def OnKeyBrowse(self, event):
        self.HandleBrowse("Choose private key file", self.keyFileText)

    def HandleBrowse(self, title, textCtrl):

        dlg = wx.FileDialog(self, title,
                           wildcard = "PEM files (*.pem)|*.pem|All files|*.*",
                           style = wx.SAVE)

        txtVal =  textCtrl.GetValue()
        if txtVal != "":
            if os.path.isdir(txtVal):
                dlg.SetDirectory(txtVal)
            else:
                dlg.SetPath(txtVal)

        rc = dlg.ShowModal()

        if rc == wx.ID_CANCEL:
            return

        print "Got path ", dlg.GetPath()

        textCtrl.SetValue(dlg.GetPath())

    def OnExport(self, event):
        print "Export"

        #
        # Time to export.
        #
        # Validity checks first:
        #
        #   See if certFile is specified, if it is a file that exists,
        #   if its directory exists, if the directory is writable.
        #
        #   If we're writing a separate key file, do the same checks.
        #
        # Then do the export.
        #

        certPath = self.certFileText.GetValue()

        if certPath == "":
            dlg = wx.MessageDialog(self, "Please specify a certificate file",
                                  "Please specify a certificate file",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.useKeyFile:
            keyPath = self.keyFileText.GetValue()
        else:
            keyPath = None

        if self.useKeyFile and keyPath == "":
            dlg = wx.MessageDialog(self, "Please specify a private key file",
                                  "Please specify a private key file",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return


        certStatus, certMsg = ValidateExportPath(certPath)

        if certStatus == 1:
            dlg = wx.MessageDialog(self,
                                  "Cannot write to certificate file:\n" + certMsg,
                                  "Cannot write certificate file",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        elif certStatus == 2:
            dlg = wx.MessageDialog(self,
                                  "Certificate file %s already exists.\nOverwrite it?" % (certPath),
                                  "Certificate file already exists",
                                  style = wx.YES_NO | wx.NO_DEFAULT)
            rc = dlg.ShowModal()
            dlg.Destroy()
            if rc != wx.ID_YES:
                return

        #
        # Finished validating cert file
        #

        if keyPath is not None:
            keyStatus, keyMsg = ValidateExportPath(keyPath)

            if keyStatus == 1:
                dlg = wx.MessageDialog(self,
                                      "Cannot write to private key file:\n" + keyMsg,
                                      "Cannot write private key file",
                                      style = wx.OK)
                dlg.ShowModal()
                dlg.Destroy()
                return
            elif keyStatus == 2:
                dlg = wx.MessageDialog(self,
                                      "Private key file %s already exists.\nOverwrite it?" % (keyPath),
                                      "Private key file already exists",
                                      style = wx.YES_NO | wx.NO_DEFAULT)
                rc = dlg.ShowModal()
                dlg.Destroy()
                if rc != wx.ID_YES:
                    return

        #
        # Finished validating key file.
        #

        self.exportIdentityCert(self.cert, certPath, keyPath)

        #
        # If we successfully exported, we're done.
        #

        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Show(0)
        
    def exportIdentityCert(self, cert, certFile, keyFile):
        try:
            fh = open(certFile, "w")
            fh.write(cert.cert.cert.as_pem())
            
            if keyFile is not None:
                fh.close()

                fh = open(keyFile, "w")

            #
            # We'll just copy the private key file, so we don't
            # have to deal with passphrases.
            #

            kpath = cert.GetKeyPath()
            kfh = open(kpath, "r")

            shutil.copyfileobj(kfh, fh)

            kfh.close()
            fh.close()
            return 1
        
        except Exception, e:
            log.exception("Export failed")
            dlg = wx.MessageDialog(self, "Certificate export failed:\n" + str(e),
                                  "Export failed",
                                  wx.ID_OK)
            dlg.ShowModal()
            dlg.Destroy()
            return 0

    def exportCACert(self, cert, certFile):
        try:
            fh = open(certFile, "w")
            fh.write(cert.cert.cert.as_pem())
            fh.close()
        except Exception, e:
            print "Export failed: ", e



    def OnCancel(self, event):
        print "Cancel"

class ExportCACertDialog(wx.Dialog):
    """
    Dialog for exporting a trusted CA certificate.

                                                     _________
      Certificate file:     ____________________     |_Browse_|

                                                     _________
      Signing policy file:  ____________________     |_Browse_|

       ________    ________
      |_Export_|  |_Cancel_|


    """

    def __init__(self, parent, cert, id = -1, title = "Export Trusted CA Certificate"):
        wx.Dialog.__init__(self, parent, id, title,
                          size = wx.Size(600,200),
                          style = wx.CAPTION | wx.RESIZE_BORDER | wx.SYSTEM_MENU)

        self.cert = cert

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

        #
        # Title.
        #

        hb = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self, -1, "Export trusted CA cert for ")
        t.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))

        hb.Add(t, 0)

        t = wx.StaticText(self, -1, str(cert.GetShortSubject()))
        t.SetFont(wx.Font(12, wx.SWISS, wx.ITALIC, wx.BOLD))

        hb.Add(t, 0)

        self.sizer.Add(hb, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Create text input grid.
        #

        gs = wx.FlexGridSizer(cols = 3, hgap = 3, vgap = 3)

        t = wx.StaticText(self, -1, "Certificate file:")
        gs.Add(t, 0, wx.ALIGN_CENTER_VERTICAL)
        self.certFileText = wx.TextCtrl(self, -1, "")
        EVT_KILL_FOCUS(self.certFileText, self.OnCertFileText)
        gs.Add(self.certFileText, 1, wx.EXPAND)
        b = wx.Button(self, -1, "Browse")
        EVT_BUTTON(self, b.GetId(), self.OnCertBrowse)
        gs.Add(b, 0)

        t = wx.StaticText(self, -1, "Signing policy file:")
        gs.Add(t, 0, wx.ALIGN_CENTER_VERTICAL)
        self.spFileText = wx.TextCtrl(self, -1, "")
        EVT_CHAR(self.spFileText, self.OnSPFileChar)
        gs.Add(self.spFileText, 1, wx.EXPAND)

        b = wx.Button(self, -1, "Browse")
        EVT_BUTTON(self, b.GetId(), self.OnSPBrowse)
        gs.Add(b, 0)

        gs.AddGrowableCol(1)

        self.sizer.Add(gs, 1, wx.EXPAND)

        #
        # And the export/cancel buttons.
        #

        hs = wx.BoxSizer(wx.HORIZONTAL)
        b = wx.Button(self, -1, "Export Certificate")
        b.SetDefault()
        EVT_BUTTON(self, b.GetId(), self.OnExport)
        hs.Add(b, 0, wx.ALL, 4)
        
        b = wx.Button(self, wx.ID_CANCEL, "Cancel")
        # EVT_BUTTON(self, b.GetId(), self.OnCancel)
        hs.Add(b, 0, wx.ALL, 4)

        self.sizer.Add(hs, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.userEnteredSPFile = 0

    def OnCertFileText(self, event):
        print "Got certfile text ", self.certFileText.GetValue()
        self.SetSPDefault()
        
    def OnSPFileChar(self, event):
        self.userEnteredSPFile = 1
        event.Skip()

    def OnCertBrowse(self, event):

        try:
            f = self.cert.GetSubject().get_hash()
            f += ".0"
        except:
            log.exception("getsubj gethash failed")
            f = None
        
        self.HandleBrowse("Choose certificate file", self.certFileText,
                          "CA files (*.0)|*.0|PEM files (*.pem)|*.pem|All files|*.*",
                          defaultFile = f)

        self.SetSPDefault()

    def SetSPDefault(self):
        #
        # If the user hasn't entered a signing policy name yet,
        # fill in a default.
        #

        if self.userEnteredSPFile:
            return

        path = self.certFileText.GetValue()
        if path == "":
            return

        base, ext = os.path.splitext(path)
        
        self.spFileText.SetValue(base + ".signing_policy")

    def OnSPBrowse(self, event):
        self.HandleBrowse("Choose signing policy file", self.spFileText,
                          "Signing policy files (*.signing_policy)|*.signing_policy|All files|*.*",)

    def HandleBrowse(self, title, textCtrl, wildcard, defaultFile = None):

        dlg = wx.FileDialog(self, title,
                           wildcard = wildcard,
                           style = wx.SAVE)

        txtVal =  textCtrl.GetValue()
        if txtVal != "":
            if os.path.isdir(txtVal):
                dlg.SetDirectory(txtVal)
            else:
                dlg.SetPath(txtVal)
        elif defaultFile is not None:
            dlg.SetFilename(defaultFile)

        rc = dlg.ShowModal()

        if rc == wx.ID_CANCEL:
            return

        print "Got path ", dlg.GetPath()

        textCtrl.SetValue(dlg.GetPath())

    def OnExport(self, event):
        print "Export"

        #
        # Time to export.
        #
        # Validity checks first:
        #
        #   See if certFile is specified, if it is a file that exists,
        #   if its directory exists, if the directory is writable.
        #
        #   Also check the signing policy file.
        #
        # Then do the export.
        #

        certPath = self.certFileText.GetValue()

        if certPath == "":
            dlg = wx.MessageDialog(self, "Please specify a certificate file",
                                  "Please specify a certificate file",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        spPath = self.spFileText.GetValue()

        if spPath == "":
            dlg = wx.MessageDialog(self, "Please specify a signing policy file",
                                  "Please specify a signing policy file",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        certStatus, certMsg = ValidateExportPath(certPath)

        if certStatus == 1:
            dlg = wx.MessageDialog(self,
                                  "Cannot write to certificate file:\n" + certMsg,
                                  "Cannot write certificate file",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        elif certStatus == 2:
            dlg = wx.MessageDialog(self,
                                  "Certificate file %s already exists.\nOverwrite it?" % (certPath),
                                  "Certificate file already exists",
                                  style = wx.YES_NO | wx.NO_DEFAULT)
            rc = dlg.ShowModal()
            dlg.Destroy()
            if rc != wx.ID_YES:
                return

        #
        # Finished validating cert file
        #


        spStatus, spMsg = ValidateExportPath(spPath)

        if spStatus == 1:
            dlg = wx.MessageDialog(self,
                                  "Cannot write to signing policy file:\n" + spMsg,
                                  "Cannot write signing policy file",
                                  style = wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        elif spStatus == 2:
            dlg = wx.MessageDialog(self,
                                  "Signing policy file %s already exists.\nOverwrite it?" % (spPath),
                                  "Signing policy file already exists",
                                  style = wx.YES_NO | wx.NO_DEFAULT)
            rc = dlg.ShowModal()
            dlg.Destroy()
            if rc != wx.ID_YES:
                return

        #
        # Finished validating signing policy file.
        #

        self.exportCACert(self.cert, certPath, spPath)

        #
        # If we successfully exported, we're done.
        #

        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Show(0)
        
    def exportCACert(self, cert, certFile, spFile):
        try:
            fh = open(certFile, "w")
            fh.write(cert.cert.cert.as_pem())
            fh.close()

            shutil.copyfile(cert.GetFilePath("signing_policy"), spFile)
        except Exception, e:
            print "Export failed: ", e



    def OnCancel(self, event):
        print "Cancel"


def ImportPEMIdentityCertificate(certMgr, certFile, keyFile):
    """
    Import a PEM-formatted X509 identity certificate.

    @param certFile: File containing the certificate.
    @param keyFile: File containing the private key.
    
    """

    try:
        print "Import PEM, looking for cb"
        cb = Toolkit.GetDefaultApplication().GetCertificateManagerUI().GetPassphraseCallback("Private key passphrase",
                                                               "Enter the passphrase to your private key.")
        impCert = certMgr.ImportIdentityCertificatePEM(certMgr.GetCertificateRepository(),
                                                       certFile, keyFile, cb)
        log.debug("Imported identity %s", str(impCert.GetSubject()))

    except CertificateRepository.RepoInvalidCertificate, ex:
        why = ex.args[0]
        log.exception("Import fails: %s. cert file %s keyfile %s",
                      why, certFile, keyFile)
        dlg = wx.MessageDialog(None, "Error occurred during certificate import:\n" + why,
                              "Error on import",
                              style = wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return
    
    except:
        log.exception("Error importing certificate from %s keyfile %s",
                      certFile, keyFile)
        dlg = wx.MessageDialog(None, "Error occurred during certificate import.",
                              "Error on import",
                              style = wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return


    #
    # Check to see if we have the CA cert for the issuer of this cert.
    #

    if not certMgr.VerifyCertificatePath(impCert):
        log.warn("can't verify issuer")
        dlg = wx.MessageDialog(None, "Cannot verify the certificate path for \n" +
                              str(impCert.GetSubject()) + "\n"
                              "This certificate may not be usable until the \n" +
                              "appropriate CA certificates are imported. At the least,\n" +
                              "the certificate for this CA must be imported:\n" +
                              str(impCert.GetIssuer()) + "\n" +
                              "It might be found in a file %s.0." % hex(impCert.GetIssuer().as_hash())[2:],
                              "Cannot verify certificate path")
        dlg.ShowModal()
        dlg.Destroy()

    #
    # Check to see if there is a default identity cert. If not, make
    # this the default.
    #

    idCerts = certMgr.GetDefaultIdentityCerts()
    log.debug("ID certs: %s", idCerts)

    if len(idCerts) == 0:
        log.debug("Setting newly imported identity as default")
        certMgr.SetDefaultIdentity(impCert)

    try:
        #
        # Invoke InitEnvironment to ensure that
        # the cert runtime is in the correct state after
        # loading a new certificate. Ignore proxy errors
        # here as we don't care at this point
        # 
        certMgr.InitEnvironment()

    except CertificateManager.NoProxyFound:
        pass
    except CertificateManager.ProxyExpired:
        pass
    except Exception, e:
        log.exception("InitEnvironment raised an exception during import")


    dlg = wx.MessageDialog(None, "Certificate imported successfully. Subject is\n" +
                          str(impCert.GetSubject()),
                          "Import successful",
                          style = wx.OK | wx.ICON_INFORMATION)

    dlg.ShowModal()
    dlg.Destroy()

def ImportCACertificate(certMgr, certFile, signingPolicy):
    """
    Import a new CA certificate.

    @param certMgr: Current certificate manager instance.
    @type certMgr: L{CertificateManager}
    @param certFile: File containing new CA certificate.
    @type certFile: C{string}
    @param signingPolicy: Actual text of the signing policy.
    @type signingPolicy: C{string}

    """

    try:

        impCert = certMgr.ImportCACertificatePEM(certMgr.GetCertificateRepository(),
                                                      certFile)
        log.debug("Imported identity %s", str(impCert.GetSubject()))

        spPath = impCert.GetFilePath("signing_policy")
        fh = open(spPath, "w")
        fh.write(signingPolicy)
        fh.close()

        certMgr.InitEnvironment()

        return impCert

    except:
        log.exception("Error importing certificate from %s", certFile)
        dlg = wx.MessageDialog(None, "Error occurred during certificate import.",
                              "Error on import",
                              style = wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return None
