#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        XMLGroupMsgClient.py
# Purpose:     A group messaging service xml layer.
# Created:     2005/09/09
# RCS-ID:      $Id: XMLGroupMsgClient.py,v 1.5 2006-01-23 17:29:29 turam Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from GroupMsgClient import GroupMsgClient
import ZSI
from ZSI.parse import ParsedSoap
from StringIO import StringIO
import AccessGrid.hosting.ZSI # registers AccessGrid types
from GroupMsgClientBase import GroupMsgClientBase


class XMLGroupMsgClient(GroupMsgClientBase):
    def __init__(self, location, privateId, channel, groupMsgClientClassList=[GroupMsgClient]):
        GroupMsgClientBase.__init__(self, location, privateId, channel, groupMsgClientClassList=groupMsgClientClassList)

    def Send(self, data):
        xml = self._Serialize(data)
        self.groupMsgClient.Send(xml)

    def Receive(self, data):
        pythonObject = self._Deserialize(data)
        if self.receiveCallback != None:
            apply(self.receiveCallback, [pythonObject])

    def _Serialize(self, data):
        # Document/literal
        sw = ZSI.writer.SoapWriter(nsdict={}, envelope=True)
        typeCode = ZSI.TC.AnyElement(aname="any", minOccurs=0, maxOccurs=1, nillable=False, processContents="lax")
        sw.serialize(data, typeCode)
        #print "SERIALIZED:", str(sw)
        return str(sw)

    def _Deserialize(self, xml):
        # Doc/lit
        ps = ParsedSoap(xml, readerClass=None, keepdom=False)
        return ZSI.TC.AnyElement(aname="any", minOccurs=0, maxOccurs=1, nillable=False, processContents="lax").parse(ps.body_root, ps)

