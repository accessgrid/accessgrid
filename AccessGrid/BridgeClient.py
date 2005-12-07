#-----------------------------------------------------------------------------
# Name:        BridgeClient.py
# Purpose:     Generic base client interface to a bridge server.
# Created:     2005/12/06
# RCS-ID:      $Id: BridgeClient.py,v 1.1 2005-12-07 01:47:34 eolson Exp $
# Copyright:   (c) 2005-2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class BridgeClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def JoinBridge(self, multicastNetworkLocation):
        raise Exception("Unimplemented.  Specific BridgeClients should implementthis base BridgeClient function.")

