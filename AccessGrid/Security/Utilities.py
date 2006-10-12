#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:     helper code
# Created:     2003/08/02
# RCS-ID:      $Id: Utilities.py,v 1.8 2006-10-12 18:52:55 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
utility classes and functions.
"""

__revision__ = "$Id: Utilities.py,v 1.8 2006-10-12 18:52:55 turam Exp $"

def GetCNFromX509Subject(subject):
    """
    Return a short form of the CN in an X509Subject object.

    @param subject:  Name to extract CN from
    @type subject: X509Subject
    """
    
    cn = []
    return subject.CN
