#-----------------------------------------------------------------------------
# Name:        Version.py
# Purpose:     Toolkit version.
#
# Author:      Eric Olson
#
# Created:     2003/05/06
# RCS-ID:      $Id: Version.py,v 1.7 2004-05-25 22:29:04 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Version.py,v 1.7 2004-05-25 22:29:04 turam Exp $"
__docformat__ = "restructuredtext en"

# Call GetVersion() to get AGTK version information.
MAJOR_VERSION = 2
MINOR_VERSION = 2
POINT_VERSION = 0

BUILD_NUMBER = 4

class Version:
    """
    Version details: MAJOR.MINOR.POINT
    Works with the following operators : >, >=, ==, <>, <=, <
    """
    def __init__(self):
        self.major = 0
        self.minor = 0
        self.point = 0
    
    def __str__(self):
        if self.point == 0:
            return str(self.major) + "." + str(self.minor)
        else:
            return str(self.major) + "." + str(self.minor) + "." + str(self.point)
    
    def AsTuple3(self):
        return (int(self.major), int(self.minor), int(self.point))
    
    def __lt__(self, other):
        if (int(self.major) < int(other.major)):
            return 1
        elif (int(self.major) == int(other.major)):
            if (int(self.minor) < int(other.minor)):
                return 1
            elif (int(self.minor) == int(other.minor)):
                if (int(self.point) < int(other.point)):
                    return 1
        return 0
    
    def __le__(self, other):
        if (int(self.major) <= int(other.major)):
            if (int(self.minor) <= int(other.minor)):
                if (int(self.point) <= int(other.point)):
                    return 1
        return 0
    
    def __eq__(self, other):
        if (int(self.major) == int(other.major)):
            if (int(self.minor) == int(other.minor)):
                if (int(self.point) == int(other.point)):
                    return 1
        return 0
    
    def __ne__(self, other):
        if (int(self.major) == int(other.major)):
            if (int(self.minor) == int(other.minor)):
                if (int(self.point) == int(other.point)):
                    return 0
        return 1
    
    def __gt__(self, other):
        if (int(self.major) > int(other.major)):
            return 1
        elif (int(self.major) == int(other.major)):
            if (int(self.minor) > int(other.minor)):
                return 1
            elif (int(self.minor) == int(other.minor)):
                if (int(self.point) > int(other.point)):
                    return 1
        return 0
    
    def __ge__(self, other):
        if (int(self.major) >= int(other.major)):
            if (int(self.minor) >= int(other.minor)):
                if (int(self.point) >= int(other.point)):
                    return 1
        return 0

def CreateVersionFromTuple3( (major, minor, point) ):
    ver = Version()
    ver.major = int(major)
    ver.minor = int(minor)
    ver.point = int(point)
    return ver

def CreateVersionFromString(strng):
    ver_list = strng.split(".")
    if len(ver_list) > 3 or len(ver_list) < 2:
        raise "InvalidVersionString"
    ver = Version()
    ver.major = int(ver_list[0])
    ver.minor = int(ver_list[1])
    if len(ver_list) == 3:
        ver.point = int(ver_list[2])
    return ver

def GetVersion():
    """ Use this to get the current version of AGTK. """
    global MAJOR_VERSION, MINOR_VERSION, POINT_VERSION
    ver = CreateVersionFromTuple3((MAJOR_VERSION,
                                   MINOR_VERSION, POINT_VERSION))
    
    return ver

def GetBuildNumber():
    """ Use this to get the build number """
    global BUILD_NUMBER
    return BUILD_NUMBER

#
# yes, this is a hack, but it works :-)
#

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--build':
        print GetBuildNumber()
    else:
        print GetVersion()



