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