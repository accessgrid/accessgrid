#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:     helper code
# Created:     2003/08/02
# RCS-ID:      $Id: Utilities.py,v 1.9 2007-10-01 16:49:40 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
utility classes and functions.
"""

import time


__revision__ = "$Id: Utilities.py,v 1.9 2007-10-01 16:49:40 turam Exp $"

def NewMd5Hash(subject):
    """
    Return a new md5 hash.

    The hashlib module is new in python 2.5 and deprecates
    the md5 module in python 2.6 but is unavailable in python 2.4.
    NewMd5Hash returns a new md5 hash using whichever of these modules
    is available.
    """
    try:
        import hashlib
        return hashlib.md5(subject)
    except ImportError:
        import md5
        return md5.new(subject)

def GetCNFromX509Subject(subject):
    """
    Return a short form of the CN in an X509Subject object.

    @param subject:  Name to extract CN from
    @type subject: X509Subject
    """
    
    cn = []
    return subject.CN

def IsExpired(x509):
    isExpired = 0
    now = time.time()
    before_time = x509.get_not_before()
    after_time = x509.get_not_after()
    format = '%b %d %H:%M:%S %Y %Z'
    before_tuple = time.strptime(str(before_time),format)
    after_tuple = time.strptime(str(after_time), format)
    before = time.mktime(before_tuple) - time.timezone
    after = time.mktime(after_tuple) - time.timezone
    if now < before or now > after:
        return 1

    return 0
