#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:     helper code
# Created:     2003/08/02
# RCS-ID:      $Id: Utilities.py,v 1.7 2005-10-27 18:58:14 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
utility classes and functions.
"""

__revision__ = "$Id: Utilities.py,v 1.7 2005-10-27 18:58:14 turam Exp $"

def GetCNFromX509Subject(subject):
    """
    Return a short form of the CN in an X509Subject object.

    @param subject:  Name to extract CN from
    @type subject: X509Subject
    """
    
    cn = []
    for what, val in subject.get_name_components():
        if what == "CN":
           cn.append(val)
    return ", ".join(cn)

