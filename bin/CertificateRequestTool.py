#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        CertificateRequestTool.py
# Purpose:     Starts the CertificateRequestTool
#
# Author:      lefvert
#
#
# Created:     2003/08/12
# RCS_ID:      $Id: CertificateRequestTool.py,v 1.4 2004-03-12 05:23:12 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
This is the tool used to get certificates.
"""
__revision__ = "$Id: CertificateRequestTool.py,v 1.4 2004-03-12 05:23:12 judson Exp $"
__docformat__ = "restructuredtext en"

import sys

from AccessGrid.Toolkit import WXGUIApplication
from wxPython.wx import wxPySimpleApp

def Usage():
    """
    How to use the program.
    """
    print "%s:" % (sys.argv[0])
    print "  --help:        print usage"
#    print "  -i|--identity: request identity certificate"
#    print "  -h|--host:     request host certificate"
#    print "  -s|--service:  request service certificate"

def Main():
    """
    The main routine.
    """

#    certType = None
#
#if len(sys.argv) == 1:
#    certType = None

#elif len(sys.argv) == 2:
#    arg = sys.argv[1]
#    if arg == '-i' or '-identity':
#        certType = "IDENTITY"
#
#    elif arg == '-s' or '-service':
#        certType = "SERVICE"
#
#    elif arg == '-h' or '-host':
#        certType = "HOST"
#
#    else:
#        Usage()
#        return

#else:
#    Usage()
#    return

    app = WXGUIApplication()
    args = app.Initialize(sys.argv)

    # This will not work if we don't have any certificates
    try:
        app.certificateManager.InitEnvironment()
    except:
        # Doesn't matter if we have certificates or proxies
        # we just want to request a new certificate
        pass

    certMgrUI = app.GetCertMgrUI()
    certMgrUI.HandleNoCertificateInteraction()

if __name__ == "__main__":
    pp = wxPySimpleApp()
    Main()
