#-----------------------------------------------------------------------------
# Name:        CertificateRequestService.py
# Purpose:     Certificate Request Service code, to provide a client and
#              server that makes requesting, issuing, and retrieving
#              certificates easier.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CertificateRequestService.py,v 1.2 2004-02-24 21:33:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
"""

__revision__ = "$Id: CertificateRequestService.py,v 1.2 2004-02-24 21:33:07 judson Exp $"
__docformat__ = "restructuredtext en"

import logging

log = logging.getLogger("CertReqService")

class CertificateRequestService:
    pass

class CertificateRequestServiceSI(SOAPInterface):
    pass

class CertificateRequestServiceXI(XMLRPCInterface):
    pass

class CertificateRequestServiceIW:
    pass
