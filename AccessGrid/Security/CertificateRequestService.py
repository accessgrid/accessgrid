#-----------------------------------------------------------------------------
# Name:        CertificateRequestService.py
# Purpose:     Certificate Request Service code, to provide a client and
#              server that makes requesting, issuing, and retrieving
#              certificates easier.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CertificateRequestService.py,v 1.3 2004-03-10 23:17:08 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
"""

__revision__ = "$Id: CertificateRequestService.py,v 1.3 2004-03-10 23:17:08 eolson Exp $"
__docformat__ = "restructuredtext en"

from AccessGrid import Log

log = Log.GetLogger(Log.CertReqService)

class CertificateRequestService:
    pass

class CertificateRequestServiceSI(SOAPInterface):
    pass

class CertificateRequestServiceXI(XMLRPCInterface):
    pass

class CertificateRequestServiceIW:
    pass
