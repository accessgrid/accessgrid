#-----------------------------------------------------------------------------
# Name:        ClientProfileTest.py
# Purpose:     Tests the Client Profile Class.
#
# Author:      Ivan R. Judson
#
# Created:     2003/28/01
# RCS-ID:      $Id: ClientProfileTest.py,v 1.1 2003-01-28 17:21:12 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.ClientProfile import ClientProfile

empty = ClientProfile()
empty.Save("empty-test-out")

user = ClientProfile("userProfileExample")
user.Save("user-test-out")

node = ClientProfile("nodeProfileExample")
node.Save("node-test-out")
