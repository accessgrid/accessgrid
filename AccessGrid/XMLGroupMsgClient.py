#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        XMLGroupMsgClient.py
# Purpose:     A group messaging service xml layer.
# Created:     2005/09/09
# RCS-ID:      $Id: XMLGroupMsgClient.py,v 1.2 2005-09-23 22:22:20 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from GroupMsgClient import GroupMsgClient
import ZSI
from ZSI.parse import ParsedSoap
from ZSI import TC
from StringIO import StringIO
import AccessGrid.hosting.ZSI # registers AccessGrid types
from GroupMsgClientBase import GroupMsgClientBase

try:
    # Use 4suite to speedup xml parsing 
    from Ft.Xml.Domlette import NonvalidatingReaderBase
    class DomletteReader(NonvalidatingReaderBase):
        '''Used with ZSI.parse.ParsedSoap
        '''
        fromString = NonvalidatingReaderBase.parseString
        fromStream = NonvalidatingReaderBase.parseStream
    defaultReaderClass = NonvalidatingReaderBase
except:
    defaultReaderClass = None
 

class XMLGroupMsgClient(GroupMsgClientBase):
    def __init__(self, location, privateId, channel):
        GroupMsgClientBase.__init__(self, location, privateId, channel, groupMsgClientClass=GroupMsgClient)

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
        ps = ParsedSoap(xml, readerClass=defaultReaderClass, keepdom=False)
        return TC.AnyElement(aname="any", minOccurs=0, maxOccurs=1, nillable=False, processContents="lax").parse(ps.body_root, ps)

