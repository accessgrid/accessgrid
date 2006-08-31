#-----------------------------------------------------------------------------
# Name:        unittest_XmlEvent.py
# Purpose:     
#
# Created:     2006/08/31
# RCS-ID:    
# Copyright:   (c) 2006
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import unittest

from AccessGrid.XMLGroupMsgClient import XMLGroupMsgClient
from AccessGrid.ClientProfile import ClientProfile

xmlSerializerAndParser = XMLGroupMsgClient(location="localhost:9090", privateId="abc", channel="nochannel")

class XmlEventTestCase(unittest.TestCase):
    # Called before each testCase
    def setUp(self):
        self.serializerAndParser = XMLGroupMsgClient(location="localhost:9090", privateId="abc", channel="nochannel")

    # Called after each testCase
    def tearDown(self):
        pass

    def generalTest(self, origObj, equalityTestFunc=None):
      xml = xmlSerializerAndParser._Serialize(origObj)
      obj = xmlSerializerAndParser._Deserialize(xml)

      if None != equalityTestFunc:
          if not equalityTestFunc(origObj, obj):
              strng = "original: " + str(origObj) +  ", reconstructed: " + str(obj)
              raise Exception("Objects not equal. " + strng)
      else:
          if origObj != obj:
              strng = "original: " + str(origObj) +  ", reconstructed: " + str(obj)
              raise Exception("Objects not equal. " + strng)

      #print xml

    def testString(self):
        self.generalTest("blah")

    def testInteger(self):
        self.generalTest(5)

    def testFloat(self):
        self.generalTest(5.5)

    def testClientProfile(self):
        def cpEqualityTest(cp1, cp2):
            return cp1.profileType == cp2.profileType and \
                   cp1.name == cp2.name and \
                   cp1.email == cp2.email and \
                   cp1.phoneNumber == cp2.phoneNumber and \
                   cp1.publicId == cp2.publicId and \
                   cp1.location == cp2.location and \
                   cp1.privateId == cp2.privateId and \
                   cp1.distinguishedName == cp2.distinguishedName

        self.generalTest(ClientProfile(), cpEqualityTest)

    # This won't work
    #def testListOfStrings(self):
    #    self.generalTest(["a", "b", "c"])

    # This works, but not tested for interoperability with
    #   Axis or .Net.
    def testDictionary(self):
        self.generalTest({"a":1, "b":2, "c":3})

def suite():
    """ Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(XmlEventTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

