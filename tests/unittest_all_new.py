#-----------------------------------------------------------------------------
# Name:        unittest_all.py
# Purpose:     Automatic testing with machine readable output
# Created:     2004/04/014
# RCS-ID:      $Id: unittest_all_new.py,v 1.5 2004-04-16 15:12:22 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import sys, time
import xml.dom.minidom
from unittest import TestResult, TestSuite, findTestCases
from optparse import OptionParser

html_xform = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<xsl:stylesheet version=\"1.0\" xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\">
<xsl:output method=\"html\"/>
 <xsl:template match=\"TestResults\">
 <html>
  <head>
   <title>AGTk Automatic Test Results</title>
  </head>
  <body bgcolor=\"#ffffff\" text=\"#000000\">
   <H2>AGTk Automatic Test Results</H2>
   <H3>Elapsed Time <xsl:value-of select=\"@Elapsed_Time\"/></H3>
     <table border=\"1\" cellpadding=\"2\">
      <tbody>
        <xsl:apply-templates select=\"Test\"/>
      </tbody>
     </table>
  </body>
 </html>
 </xsl:template>
	
 <xsl:template match=\"Test[@Result='passed']\">
  <tr>
   <td>
    <xsl:value-of select=\"@Name\"/><br/>
   </td>
   <td bgcolor=\"#00ff00\">
    <xsl:value-of select=\"@Result\"/><br/>
   </td>
  </tr>
 </xsl:template>

 <xsl:template match=\"Test[@Result='failed']\">
  <tr>
   <td>
    <xsl:value-of select=\"@Name\"/><br/>	
   </td>
   <td bgcolor=\"#ff0000\">
    <xsl:value-of select=\"@Result\"/><br/>
   </td>
   <td>
    <xsl:value-of select=\"@Detail\"/>
   </td>
  </tr>
 </xsl:template>
</xsl:stylesheet>
"""

text_xform="""<?xml version='1.0' encoding='UTF-8'?>
<xsl:stylesheet version=\"1.0\" xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\">
<xsl:output method=\"text\"/>
 <xsl:template match=\"TestResults\">
   AGTk Automatic Test Results
   Elapsed Time: <xsl:value-of select=\"@Elapsed_Time\"/>
   <xsl:text>&#10;</xsl:text>
   <xsl:text>&#10;</xsl:text>

   <xsl:apply-templates select=\"Test\"/>

 </xsl:template>
	
<xsl:template match=\"Test[@Result='passed']\">
<xsl:value-of select=\"@Name\"/><xsl:text>...</xsl:text>
<xsl:value-of select=\"@Result\"/><xsl:text>&#10;</xsl:text>
</xsl:template>

<xsl:template match=\"Test[@Result='failed']\">
<xsl:value-of select=\"@Name\"/><xsl:text>...</xsl:text>
<xsl:value-of select=\"@Result\"/><xsl:text>&#10;</xsl:text>
     Details:
     <xsl:value-of select=\"@Detail\"/><xsl:text>&#10;&#10;</xsl:text>

</xsl:template>
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
                      action="store_const", const="html", default=None,
                      help="Output HTML results.")
    parser.add_option("--text", dest="format", metavar="FORMAT", 
                      action="store_const", const="text", default=None,
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
    if options.format is not None:
        try:
            from Ft.Lib import Uri
            from Ft.Xml.InputSource import DefaultFactory
            from Ft.Xml.Xslt.Processor import Processor
        except:
            print "Couldn't import modules to generate HTML."
            
        processor = Processor()

        if options.format == "html":
            xform = DefaultFactory.fromString(html_xform, "uri")
        elif options.format == "text":
            xform = DefaultFactory.fromString(text_xform, "uri")

        processor.appendStylesheet(xform)
        
        try:
            ro = processor.run(DefaultFactory.fromString(output, "uri"))
        except Exception, e:
            print "Failed to generate HTML. (%s)" % e
            ro = None
                
    if options.outputFile is not None and ro is not None:
        f = file(options.outputFile, 'w')
        f.write(ro)
        f.close()
    else:
        if ro is not None:
            print ro
        else:
            print output
