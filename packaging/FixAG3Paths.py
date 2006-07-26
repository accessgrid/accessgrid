#!/usr/bin/python

import sys, os

# There are 3 command line options (all mandatory)
# argv[1] is the directory to work in (containing the .py files to work on (assigned to variable targetDir)
# argv[2] is the extra path to be appended to sys.path (assigned to variable eppath)
# argv[3] is a True or False string (boolean renameFile is assigned argv[3]=='True')
#        where True means that a _new_ file name (with a '3') will be assigned (and original version removed)
#          and False means no new file name is created, rather the original file name is kept
#
targetDir = ''
argv = sys.argv
argc = len(argv)
if argc != 4:
    print "Bad args for argv[0]: need target directory and name of directory to add to PYTHONPATH"
    sys.exit(1)
else:
    targetDir = argv[1]
    eppath = argv[2]
    renameFile =  argv[3].startswith('True')

here = os.getcwd()
#line_to_insert = 'sys.path.insert' + '(0, \'' + os.path.join(eppath, 'AccessGrid3') + '\')\n'
line_to_insert = 'import agversion\nagversion.select(3)\n'
#eppath = '/usr/lib/python2.4/site-packages'

def fixAG3paths(dir):
    os.chdir(dir)
    for infilename in os.listdir(os.getcwd()):
        if infilename.endswith('.py') and not infilename.endswith('3.py') and not infilename.endswith('build.py'):
            print "=> ", infilename
            outfilename = infilename[:-3] + '3' + '.py'
            print "=> ", outfilename
            infile = open(infilename, 'r')
            outfile = open(outfilename, 'w')
            done = False
            line_inserted = False
            while not done:
                line = infile.readline()
                # Don't modify a previously fixed file
                if len(line) > 0 and line.startswith(line_to_insert):
                    line_inserted = True
                if len(line) == 0:
                    done = True
                else:
                    if not line_inserted and line.find('AccessGrid') > 4:
                        outfile.write(line_to_insert)
                        line_inserted = True
                    outfile.write(line)

            infile.close()
            outfile.close()

            os.chmod(outfilename, 0755)

            # renameFile => we want a new file name (with a '3' in it), so erase the original file
            if renameFile:
                print "ERASING: ", infilename
                os.remove(infilename)
            else:
                print "REPLACING original file: ", infilename
                os.rename(outfilename, infilename)

    os.chdir(here)

if len(targetDir) > 0:
    fixAG3paths(targetDir)


