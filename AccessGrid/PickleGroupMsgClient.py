#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        PickleGroupMsgClient.py
# Purpose:     A group messaging service pickling layer.
# Created:     2005/09/09
# RCS-ID:      $Id: PickleGroupMsgClient.py,v 1.1 2005-09-23 22:09:36 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import pickle
from GroupMsgClient import GroupMsgClient
from GroupMsgClientBase import GroupMsgClientBase

class PickleGroupMsgClient(GroupMsgClientBase):
    def __init__(self, location, privateId, channel):
        GroupMsgClientBase.__init__(self, location, privateId, channel, groupMsgClientClass=GroupMsgClient)

    def Send(self, data):
        sdata = self._Serialize(data)
        self.groupMsgClient.Send(sdata)

    def Receive(self, data):
        pythonObject = self._Deserialize(data)
        if self.receiveCallback != None:
            apply(self.receiveCallback, [pythonObject])

    def _Serialize(self, data):
        pdata = pickle.dumps(data)
        return pdata 

    def _Deserialize(self, data):
        # Unpickle the data
        try:
            event = pickle.loads(data)
        except EOFError:
            log.debug("PickleGroupMsgClient: unpickle got EOF.")
            return None
        return event

