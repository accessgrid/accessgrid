#!/usr/bin/python2 

import unittest

from AccessGrid import Log
from AccessGrid.Toolkit import Service

import logging
import logging.handlers


def GetMemoryHandlers():
    numFound = 0
    for log in Log.GetLoggers():
        for handler in log.handlers:
            for lowhandler in handler.handlers:
                if isinstance(lowhandler,logging.handlers.MemoryHandler):
                    #print "Found memory handler: ", lowhandler
                    numFound += 1
    return numFound



class LogTestCase(unittest.TestCase):

    def testMemoryHandlers(self):
        num = GetMemoryHandlers()
        print "Number of memory handlers in logs before initialization: ", num

        app = Service.instance()
        app.Initialize("test")

        num = GetMemoryHandlers()
        print "Number of memory handlers in logs after initialization: ", num
        assert num == 0

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(LogTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')
