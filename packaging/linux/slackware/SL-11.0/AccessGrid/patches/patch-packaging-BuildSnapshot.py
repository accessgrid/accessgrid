--- packaging/BuildSnapshot.py.orig	2008-06-21 13:35:30.000000000 +1000
+++ packaging/BuildSnapshot.py	2008-07-21 22:41:49.849057475 +1000
@@ -29,11 +29,11 @@
 
 # - Perform general checks
 #   - setuptools
-try:
-    import setuptools
-except ImportError:
-    print '* * Error: Required Python module "setuptools" not found'
-    sys.exit(1)
+#try:
+#    import setuptools
+#except ImportError:
+#    print '* * Error: Required Python module "setuptools" not found'
+#    sys.exit(1)
 
 #   - zsi
 try:
@@ -241,116 +241,16 @@
 
 os.environ['PYTHONPATH'] = nppath
 
-# Build stuff that needs to be built for modules to work
+# Other modules are built separately
 os.chdir(StartDir)
 
-buildcmd = "BuildOpenSSL.py"
-cmd = "%s %s %s" % (sys.executable, buildcmd, DestDir)
-ret = os.system(cmd)
-if ret:
-    print '%s failed with %d; exiting' % (cmd,ret)
-    sys.exit(1)
-
-if sys.platform == 'win32':
-    td = os.getcwd()
-    os.chdir(os.path.join(BuildDir, "tools"))
-    cmd = "%s %s" % ("MakeVfwScan.bat", DestDir)
-    ret = os.system(cmd)
-    if ret:
-        print '%s failed with %d; exiting' % (cmd,ret)
-        sys.exit(1)
-    cmd = "%s %s" % ("MakeWdmScan.bat", DestDir)
-    ret = os.system(cmd)
-    if ret:
-        print '%s failed with %d; exiting' % (cmd,ret)
-        sys.exit(1)
-    os.chdir(td)
-
-elif sys.platform == 'darwin':
-    # vic
-    td = os.getcwd()
-    os.chdir(os.path.join(BuildDir, "tools"))
-    cmd = "%s %s" % ("./MakeOsxVGrabberScan.py", os.path.join(DestDir, 'bin') )
-    ret = os.system(cmd)
-    if ret:
-        print '%s failed with %d; exiting' % (cmd,ret)
-        sys.exit(1)
-    os.chdir(td)
-
-# Build the UCL common library
-cmd = "%s %s %s %s" % (sys.executable, "BuildCommon.py", SourceDir, DestDir)
-print cmd
-ret = os.system(cmd)
-if ret:
-    print '%s failed with %d; exiting' % (cmd,ret)
-    sys.exit(1)
-
-
-# Build the other python modules
-cmd = "%s %s %s %s %s" % (sys.executable, "BuildPythonModules.py", SourceDir,
-                          BuildDir, DestDir)
-if options.verbose:
-    print "Building python modules with the command:", cmd
-ret = os.system(cmd)
-if ret:
-    print '%s failed with %d; exiting' % (cmd,ret)
-    sys.exit(1)
-
 
 # put the old python path back
 if oldpath is not None:
     os.environ['PYTHONPATH'] = oldpath
 
 
-# Build the QuickBridge executable
-if sys.platform == 'linux2' or sys.platform == 'darwin' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
-    print "Building QuickBridge"
-    os.chdir(os.path.join(BuildDir,'services','network','QuickBridge'))
-    cmd = "gcc -O -o QuickBridge QuickBridge.c"
-    print "cmd = ", cmd
-    ret = os.system(cmd)
-    if ret:
-        print '%s failed with %d; exiting' % (cmd,ret)
-        sys.exit(1)
-
-
-    cmd = "cp QuickBridge %s" % (os.path.join(DestDir,'bin','QuickBridge'))
-    print "cmd = ", cmd
-    ret = os.system(cmd)
-    if ret:
-        print '%s failed with %d; exiting' % (cmd,ret)
-        sys.exit(1)
-elif sys.platform == 'win32':
-    print "Building QuickBridge"
-    os.chdir(os.path.join(BuildDir,'services','network','QuickBridge'))
-
-    # Find the version of visual studio by peering at cl
-    (input, outerr) = os.popen4("cl.exe")
-    usageStr = outerr.readlines()
-    v = map(int, usageStr[0].split()[7].split('.')[:2])
-    
-    v = map(int, usageStr[0].split()[7].split('.')[:2])
-
-    proj = None
-    if v[0] == 12:
-        print "Please do not use visual studio 6.0 to build QuickBridge"
-    elif v[0] == 13:
-        if v[1] == 0:
-            proj = "QuickBridge.sln"
-        elif v[1] == 10:
-            proj = "QuickBridge.2003.sln"
-
-    if proj is not None:
-        os.system("devenv %s /rebuild Release" % proj)
-
-    qbexe = os.path.join(os.getcwd(), "Release", "QuickBridge.exe")
-    destDir = os.path.join(DestDir,'bin','QuickBridge.exe')
-    cmd = "copy %s %s" % (qbexe, destDir)
-    print "cmd = ", cmd
-    os.system(cmd)
-    
-
-
+# Don't build the QuickBridge executable. Its now in a separate "quickbridge" package.
 
 
 # Change to packaging dir to build packages
@@ -393,21 +293,8 @@
     sys.exit(1)
 
 
-# copy media tools to bin directory
-cmd = '%s %s %s %s'%(sys.executable, 'BuildRat.py', SourceDir, os.path.join(DestDir,"bin"))
-print "\n ********* cmd = ",cmd
-ret = os.system(cmd)
-if ret:
-    print '%s failed with %d; exiting' % (cmd,ret)
-    sys.exit(1)
-
+# media tools are built separately
 
-cmd = '%s %s %s %s'%(sys.executable, 'BuildVic.py', SourceDir, os.path.join(DestDir,"bin"))
-print "\n ********* cmd = ",cmd
-ret = os.system(cmd)
-if ret:
-    print '%s failed with %d; exiting' % (cmd,ret)
-    sys.exit(1)
 
 # Fix shared app *.py files before they're packaged
 #
@@ -443,29 +330,6 @@
 
 file_list = os.listdir(SourceDir)
 
-if bdir is not None:
-    pkg_script = "BuildPackage.py"
-    NextDir = os.path.join(StartDir, bdir)
-    if os.path.exists(NextDir):
-        os.chdir(NextDir)
-        cmd = "%s %s --verbose -s %s -b %s -d %s -p %s -m %s -v %s" % (sys.executable,
-                                                                 pkg_script,
-                                                                 SourceDir,
-                                                                 BuildDir,
-                                                                 DestDir,
-                                                                 options.pyver,
-                                                                 metainfo.replace(' ', '_'),
-                                                                 version)
-        if sys.platform == 'linux2' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
-            cmd += ' --dist %s' % (options.dist,)
-        print "cmd = ", cmd
-        ret = os.system(cmd)
-        if ret:
-            print '%s failed with %d; exiting' % (cmd,ret)
-            sys.exit(1)
-    else:
-        print "No directory (%s) found." % NextDir
-
 nfl = os.listdir(SourceDir)
 for f in file_list:
     nfl.remove(f)
