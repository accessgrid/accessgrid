import os 
import sys
import tarfile
import zipfile
import string


def ExtractZip(zippath, dstpath='.'):
    """
    Extract files from zipfile
    """
    zf = None
    try:
        if not os.path.exists(dstpath):
            os.mkdir(dstpath)

        zf = zipfile.ZipFile( zippath, "r" )
        filenameList = zf.namelist()
        for filename in filenameList:
            # create subdirs if needed
            pathparts = string.split(filename, '/')

            if len(pathparts) > 1:
                temp_dir = str(dstpath)
                for i in range(len(pathparts) - 1):
                    temp_dir = os.path.join(temp_dir, pathparts[i])

                if not os.access(temp_dir, os.F_OK):
                    try:
                        os.makedirs(temp_dir)
                    except:
                        print "Failed to make temp dir %s"%(temp_dir)
            destfilename = os.path.join(dstpath,filename)

            # Extract the file
            # Treat directory names different than files.
            if os.path.isdir(destfilename):
                pass  # skip if dir already exists
            elif destfilename.endswith("/"):
                os.makedirs(destfilename) # create dir if needed
            else: # It's a file so extract it
                filecontent = zf.read( filename )
                f = open( destfilename, "wb" )
                f.write( filecontent )
                f.close()

            os.chmod(destfilename,0755)

    except:
        if zf:
            zf.close()
        raise


def ExtractTar(tarfilename,mode):
	tf = tarfile.open(tarfilename,mode)
	members = tf.getnames()
	for m in members:
		tf.extract(m)



buildrootset = 0
if not os.environ.has_key('AGBUILDROOT'):
    if not os.path.exists('build'):
        print 'Creating build directory in current directory'
        os.mkdir('build')
    else:
        print 'Using build directory in current directory'
    buildroot = os.path.abspath(os.path.join(os.getcwd(),'build'))
else:
    buildroot = os.environ['AGBUILDROOT']
    if not os.path.exists(buildroot):
        os.makedirs(buildroot)
    buildrootset = 1

def GetDependencies(path):
    outlist = os.listdir(path)
    outlist = filter( lambda x: x.split('.')[-1] in ['gz','bz2','zip','msi','exe'], outlist)
    outlist = [os.path.abspath(os.path.join(path,f.strip())) for f in outlist]
    return outlist
    
# Determine dependencies from checked out files
plat = sys.platform
if plat == 'darwin':
    plat = 'macosx'
deplist = GetDependencies(os.path.join('third-party',plat))
deplist += GetDependencies(os.path.join('third-party','common'))
	

# Change to build directory
os.chdir(buildroot)

# Expand dependency packages into build directory
print 'Expanding dependency packages into build root', buildroot
for dep in deplist:
    print ' - ', dep
    if dep.endswith('.tar.gz'):
        pass
        #os.system('tar xzf %s' % dep)
        ExtractTar(dep,'r:gz')
    elif dep.endswith('.tar.bz2'):
        pass
        #os.system('tar xjf %s' % dep)
        ExtractTar(dep,'r:bz2')
    elif dep.endswith('.zip'):
        pass
        #os.system('unzip -o -q %s' % dep)
        ExtractZip(dep)
    elif dep.endswith('.exe') or dep.endswith('.msi'):
        # windows-specific
        os.system('copy %s %s' % (dep,'.'))
    else:
        print '* * Error: Unexpected file type: %s ; skipping' % dep


print 'Dependency packages have been expanded.'
if not buildrootset:
    print 'You must set the AGBUILDROOT environment variable.'
    print 'This can be done with the command:'
    if sys.platform in ['win32']:
        print 'set AGBUILDROOT='+buildroot
    else:
        print 'export AGBUILDROOT='+buildroot

