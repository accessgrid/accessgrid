#-----------------------------------------------------------------------------
# Name:        SOAPInterface.py
# Purpose:     Base class for all SOAP interface objects, this has the
#              constructor and authorization callback defined.
#
# Author:      Ivan R. Judson
#
# Created:     2003/23/01
# RCS-ID:      $Id: SOAPInterface.py,v 1.3 2004-03-01 20:02:42 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the base class for all SOAP interface objects. It has two
primary methods, the constructor and a default authorization for all
interfaces.
"""

__revision__ = "$Id: SOAPInterface.py,v 1.3 2004-03-01 20:02:42 turam Exp $"
__docformat__ = "restructuredtext en"

import re

methodPat = re.compile("^<(slot wrapper|bound method|built-in method) .+>$")

from AccessGrid.Security.Action import MethodAction

class SOAPInterface:
    """
    This is the SOAP Interface object. It is meant to be derived from for all
    real SOAP Interfaces. This object provides the glue for how the interfaces
    and implementations get stuck together. It also provides a default
    authorization method that returns 0 (not authorized).
    """

    def __init__(self, impl):
        """
        This constructor for all SOAP Interfaces.
        """
        # The interface keeps a reference to the implementation
        self.impl = impl

        # If the implementation is smart it keeps a reference to all of the
        # interfaces it exposes.
        if hasattr(impl, "AddInterface"):
            impl.AddInterface(self)

    def _authorize(self, *args, **kw):
        """
        This is meant to be a base class for all SOAP interfaces, so it's going
        to default to disallow calls. Derived interfaces can tailor this to
        suit their needs.
        """
        #        print "Authorizing method: %s" % kw["method"]
        return 1

    def _GetMethodActions(self):
        global methodPat
        object = self
        actions = list()
        # Here we preload the methods as actions
        for attrName in dir(object):
            if attrName.startswith("_"):
                # don't register private methods
                pass
            else:
                try:
                    attr = eval("object.%s" % attrName)
                    attrRepr = repr(attr)
                    m = methodPat.match(attrRepr)
                    if m:
                        actions.append(MethodAction(attrName))
                except:
                    print "Blew up trying to register methods."
                    raise

        return actions

    def IsValid(self):
        """
        This method is here to support calls that just want to see if there
        is a valid server endpoint for communication from the client.
        """
        return 1

    def _IsValid(self):
        """
        This method is here to support calls that just want to see if there
        is a valid server endpoint for communication from the client.
        """
        return 1

