#-----------------------------------------------------------------------------
# Name:        runtime.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: runtime.py,v 1.3 2003-02-10 14:48:06 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
Runtime services.

"""

class BadArgumentType(Exception):
    pass


def trace_entry(name):
    print "%s: Entry " % ( name)

def trace_exit(name, value):
    print "%s: Exit with %s" % (name, value)

def typecheck_okay(arg, type):
    try:
        if type == "int":
            foo = int(arg)
        elif type == "float" or type == "real":
            foo = float(arg)
        return 1
    except ValueError:
        return 0
    
def typecheck_arg(arg, type, argname, service):
    if not typecheck_okay(arg, type):
        print "Invalid type in argument %s of call to %s" % (argname, service)
        raise BadArgumentType()

def typecheck_return(arg, type, service):
    if not typecheck_okay(arg, type):
        print "Invalid type in return from call to %s" % (service)