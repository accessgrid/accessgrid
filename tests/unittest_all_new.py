#-----------------------------------------------------------------------------
# Name:        unittest_all.py
# Purpose:     Automatic testing with machine readable output
# Created:     2004/04/014
# RCS-ID:      $Id: unittest_all_new.py,v 1.1 2004-04-14 22:11:10 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import sys, time
import xml.dom.minidom
from unittest import TestResult, TestSuite, findTestCases

class _XMLTestResult(TestResult):
    """
    A test result class that outputs XML, to a stream.
    """
    separator1 = '=' * 70
    separator2 = '-' * 70

    def __init__(self, stream, descriptions):
        TestResult.__init__(self)
        self.stream = stream
        self.descriptions = descriptions
        self.success = list()
        self.domI = xml.dom.minidom.getDOMImplementation()
        
    def getDescription(self, test):
        if self.descriptions:
            return test.shortDescription() or str(test)
        else:
            return str(test)

    def startTest(self, test):
        TestResult.startTest(self, test)

    def addSuccess(self, test):
        TestResult.addSuccess(self, test)
        self.success.append((test, "ok"))

    def addError(self, test, err):
        TestResult.addError(self, test, err)

    def addFailure(self, test, err):
        TestResult.addFailure(self, test, err)

    def printErrors(self):
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)

    def getResults(self, elapsedTime):
        resDoc = self.domI.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                          "TestResults", None)
        resDoc.documentElement.setAttribute("Elapsed_Time", "%s" % elapsedTime)

        # go through successes appending a child for each
        results = self.success + self.errors + self.failures
        for s in results:
            sx = resDoc.createElement("Test")
            sx.setAttribute("Name", "%s" % s[0])
            if s[1] == "ok":
                sx.setAttribute("Result", "passed")
            else:
                sx.setAttribute("Result", "failed")
                sx.setAttribute("Detail", "%s" % s[1])
            resDoc.documentElement.appendChild(sx)
            
        return resDoc.toxml()

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.write(self.separator1 + "\n")
            self.stream.write("%s: %s\n" % (flavour,
                                            self.getDescription(test)))
            self.stream.write(self.separator2 + "\n")
            self.stream.write("%s\n" % err)

class XMLTestRunner:
    """
    A test runner class that returns the result in XML form.
    """
    def __init__(self, stream=sys.stderr, descriptions=1):
        self.stream = stream
        self.descriptions = descriptions

    def _makeResult(self):
        return _XMLTestResult(self.stream, self.descriptions)

    def run(self, test):
        result = self._makeResult()
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = float(stopTime - startTime)
        outxml = result.getResults(timeTaken)
#         result.printErrors()
#         self.stream.write(result.separator2 + "\n")
#         run = result.testsRun
#         self.stream.write("Ran %d test%s in %.3fs\n" %
#                             (run, run != 1 and "s" or "", timeTaken))
#         self.stream.write("\n")
#         if not result.wasSuccessful():
#             self.stream.write("FAILED (")
#             failed, errored = map(len, (result.failures, result.errors))
#             if failed:
#                 self.stream.write("failures=%d" % failed)
#             if errored:
#                 if failed: self.stream.write(", ")
#                 self.stream.write("errors=%d" % errored)
#             self.stream.write(")\n")
#         else:
#             self.stream.write("OK\n")
        return outxml, result

if __name__ == '__main__':
    suite = TestSuite()
    # List modules to test
    modules_to_test = [
#        'unittest_AGNodeService',
        'unittest_AGParameter',
#        'unittest_AGServiceManager',
        'unittest_ClientProfile',
        'unittest_Descriptions',
        'unittest_GUID',
        'unittest_MulticastAddressAllocator',
        'unittest_NetworkLocation',
        'unittest_Platform',
#        'unittest_VenueServer',
        'unittest_version'
        ]

    for module in map(__import__, modules_to_test):
       suite.addTest(findTestCases(module))

    runner = XMLTestRunner()
    output, result = runner.run(suite)
    print output
