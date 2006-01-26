#-----------------------------------------------------------------------------
# Name:        runag.py
# Purpose:     This script sets up the python env and executes the given command/args
# Created:     2006/01/26
# RCS-ID:      $Id: runag.py,v 1.1 2006-01-26 23:12:28 turam Exp $
# Copyright:   (c) 2006
# License:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import os

# define install path of ag module
installpath=r'c:\python23\lib\site-packages\accessgrid3'

# prepend ag install path to pythonpath env variable
if os.environ.has_key('PYTHONPATH'):
    os.environ['PYTHONPATH'] = '%s;%s' % (installpath,os.environ['PYTHONPATH'],)
else:
    os.environ['PYTHONPATH'] = installpath
if sys.argv[1:]:
    os.spawnv(os.P_WAIT,sys.executable,[sys.executable] + sys.argv[1:])
