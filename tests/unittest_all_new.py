#-----------------------------------------------------------------------------
# Name:        unittest_all.py
# Purpose:     Automatic testing with machine readable output
# Created:     2004/04/014
# RCS-ID:      $Id: unittest_all_new.py,v 1.4 2004-04-15 17:58:49 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import sys, time
import xml.dom.minidom
from unittest import TestResult, TestSuite, findTestCases
from optparse import OptionParser

html_xform = """<?xml version='1.0' encoding='UTF-8'?>
<xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'>
<xsl:output method='html'/>
 <xsl:template match='BeaconReport'>
 <html>
  <head>
   <title>Multicast Beacon Report</title>
  </head>
  <body bgcolor='#A0A0A0' text='#000000'>
   <H2>Multicast Beacon Report for <xsl:value-of select='@time'/></H2>
     <table border='1' cellpadding='2'>
      <tbody>
       <xsl:apply-templates select='Beacon'/>
      </tbody>
     </table>
  </body>
 </html>
 </xsl:template>
	
 <xsl:template match='Beacon'>
  <tr>
   <td>
    SSRC: <xsl:value-of select='@ssrc'/><br/>	
    Host: <xsl:value-of select='@name'/><br/>
    IP: <xsl:value-of select='@ip'/>
   </td>
   <xsl:apply-templates select='Data'/>
  </tr>
 </xsl:template>
	
 <xsl:template match='Data'>
  <td>
   SSRC: <xsl:value-of select='@send_ssrc'/><br/>
   <xsl:apply-templates select='Loss'/>
  </td>
 </xsl:template>
 
 <xsl:template match='Loss'>
  Total Loss: <xsl:value-of select='@total'/><br/>
  Fractional Loss: <xsl:value-of select='@fractional'/>
 </xsl:template>
 
</xsl:stylesheet>
"""

text_xform="""<?xml version='1.0' encoding='UTF-8'?>
<xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'>

</xsl:stylesheet>
"""

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
        return outxml, result

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-o", "--outputFile", dest="outputFile", metavar="FILE",
                      default=None,
                      help="specify the output file to store results in.")
    parser.add_option("--html", dest="format", metavar="FORMAT", 
                      action="store_const", const="html", default="text",
                      help="Output HTML results.")
    parser.add_option("--text", dest="format", metavar="FORMAT", 
                      action="store_const", const="text", default="text",
                      help="Output TEXT results.")
    
    options, args = parser.parse_args()
    
    # List modules to test
    modules_to_test = [
        'unittest_AGParameter',
        'unittest_ClientProfile',
        'unittest_Descriptions',
        'unittest_GUID',
        'unittest_MulticastAddressAllocator',
        'unittest_NetworkLocation',
        'unittest_Platform',
        'unittest_version'
#        'unittest_AGServiceManager',
#        'unittest_AGNodeService',
#        'unittest_VenueServer',
        ]

    suite = TestSuite()

    for module in map(__import__, modules_to_test):
       suite.addTest(findTestCases(module))

    output, result = XMLTestRunner().run(suite)

    ro = output
    if options.format == 'html':
        try:
            from Ft.Lib import Uri
            from Ft.Xml.InputSource import DefaultFactory
            from Ft.Xml.Xslt.Processor import Processor
        except:
            print "Couldn't import modules to generate HTML."
            
        processor = Processor()
        xform = DefaultFactory.fromString(html_xform, "")
        processor.appendStylesheet(xform)
        
        try:
            ro = processor.run(output)
        except:
            print "Failed to generate HTML."
            ro = None
                
    if options.outputFile is not None and ro is not None:
        f = file(options.outputFile, 'w')
        f.write(ro)
        f.close()
    else:
        print output
