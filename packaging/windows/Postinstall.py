import AccessGrid
import AccessGrid.hosting
import OpenSSL
import os
import os.path
import glob
import sys

#
# The following byte compiles all the AccessGrid modules after they've
# been installed into their proper place
#

def modimport(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.py")):
        __import__(module.__name__ + "." + os.path.basename(module_file[:-3]))

sys.stdout.write("Compiling Access Grid Python modules.... ")
modimport(AccessGrid)
modimport(AccessGrid.hosting)
modimport(OpenSSL)
sys.stdout.write("Done\n")
