import AccessGrid
import AccessGrid.hosting
import os
import os.path
import glob

#
# The following byte compiles all the AccessGrid modules after they've
# been installed into their proper place
#

def modimport(module):
    for module_file in glob.glob(module.__path__[0] + "\\*.py"):
        __import__(module.__name__ + "." + os.path.basename(module_file[:-3]))

modimport(AccessGrid)
modimport(AccessGrid.hosting)
