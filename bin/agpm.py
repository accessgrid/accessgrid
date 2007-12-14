#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        RegisterApp.py
# Purpose:     This registers an application with the users venue client.
# Created:     2002/12/12
# RCS-ID:      $Id: agpm.py,v 1.38 2007-12-14 23:07:55 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This program is used to register applications with the user or system AGTk
installation.
"""
__revision__ = "$Id: agpm.py,v 1.38 2007-12-14 23:07:55 turam Exp $"

import os
import re
from types import StringType
import sys
import zipfile
import tempfile
import shutil
from optparse import OptionParser, Option

from AccessGrid import Log

from AccessGrid.AppDb import AppDb
from AccessGrid.PluginDb import PluginDb
from AccessGrid.Utilities import LoadConfig
from AccessGrid.Platform.Config import SystemConfig, AGTkConfig, UserConfig
from AccessGrid import Toolkit, Utilities

log = Log.GetLogger(Log.Agpm)

tempfile.tmpdir = SystemConfig.instance().GetTempDir()
gUseGui=False

class InvalidApplicationDescription(Exception):
    pass

def ShowResult(result, title="Package Manager"):
    if True == gUseGui:
        from AccessGrid.UIUtilities import MessageDialog
        import wx
        try: wxapp = wx.PySimpleApp()
        except: pass
        dialog = MessageDialog(None, str(result), title, style = wx.OK | wx.ICON_INFORMATION)
    else:
        print str(result)

def InitAppAndProcessArgs(app):
    doc = """
    By default this program registers/installs a shared application
    or node service with the users environment. Using the -u argument applications 
    can be unregistered/uninstalled.  To unregister node services, use 
    the '--unregister-service' argument.
    """
    tkConf = AGTkConfig.instance()

    app.AddCmdLineOption(Option("-u", "--unregister", action="store_true",
                      dest="unregister", default=0,
          help="Unregister the application, instead of registering it. \
                Specify application with '-n'"))
    app.AddCmdLineOption(Option("--unregister-service", action="store_true",
                      dest="unregisterservice", default=0,
          help="Unregister the service, instead of registering it. \
                Specify service with '-n'. (Requires administrative access)"))
    app.AddCmdLineOption(Option("--unregister-plugin", action="store_true",
                      dest="unregisterplugin", default=0,
          help="Unregister the plugin, instead of registering it. \
                Specify plugin with '-n'."))
    app.AddCmdLineOption(Option("-n", "--name", dest="appname",
          help="specify a name other than the default on from the .app file."))
    app.AddCmdLineOption(Option("-v", "--verbose", action="store_true", dest="verbose",
                      default=0, help="Be verbose during app processing."))
    app.AddCmdLineOption(Option("-f", "--file", dest="appfile",
          help="The name of a .app file to install."))

    # Remove conflicting options and readd without the shorter option.
    app.parser.remove_option("-d") # remove debug option
    app.parser.remove_option("-l") # remove logfile option
    # Unnecessary options
    app.parser.remove_option("--cert")
    app.parser.remove_option("--key")
    app.parser.remove_option("--cadir")
    app.parser.remove_option("--secure")

    # Readd debug option without the shorter -d.
    app.parser.add_option("--debug", action="store_true",
                           dest="debug", default=0,
                           help="Set the debug level of this program.")

    # Readd logfile option without the shorter -l.
    app.parser.add_option("--logfile", dest="logfilename",
                           metavar="LOGFILE", default=None,
                           help="Specify a log file to output logging to.")

    app.AddCmdLineOption(Option("-d", "--dir", dest="appdir",
                      help="The name of a directory containing a .app file."))
    app.AddCmdLineOption(Option("-z", "--zip", dest="appzip",
                      help="The name of a .zip file containing a .app or .svc file.\
                            (Requires administrative access to install services)"))
    app.AddCmdLineOption(Option("-p", "--package", dest="apppkg",
                    help="The name of an agpkg file containing a .app or .svc \
                    file. (Requires administrative access to install services)"))
    app.AddCmdLineOption(Option("-l", "--list-apps", action="store_true",
                      dest="listapps", help="List installed shared apps."))
    app.AddCmdLineOption(Option("--list-services", action="store_true",
                      dest="listservices", help="List installed node services."))
    app.AddCmdLineOption(Option("--list-plugins", action="store_true",
                      dest="listplugins", help="List installed plugins."))
    
    app.AddCmdLineOption(Option("-s", "--system", action="store_true",
                      dest="sys_install", default=0,
                      help="Install the package for all users. \
                      (This requires administrative access)"))
    app.AddCmdLineOption(Option("--post-install", action="store_true",
                      dest="post_install", default=0,
                      help="Do a post-installation run, which will install \
                      all apps distributed with the toolkit in the system \
                      if possible. (This requires administrative access)"))
    app.AddCmdLineOption(Option("--wait-for-input", action="store_true",
                      dest="wait_for_input", default=0,
                      help="After completing wait for the user to confirm by\
                      pressing a key."))
    app.AddCmdLineOption(Option("--gui", action="store_true",
                      dest="useGui", help="Show if the installation was successful with a GUI dialog."))
                      
    args = app.Initialize("agpm")
    if True == app.GetOption("useGui"):
        global gUseGui
        gUseGui = True

    # Validate arguments
    if not (
            # these args imply an action
            app.options.appzip 
            or app.options.apppkg 
            or app.options.appfile 
            or app.options.appdir 
            
            # these are explicit actions
            or app.options.post_install
            or app.options.listservices
            or app.options.listapps
            or app.options.listplugins
            or app.options.unregister
            or app.options.unregisterservice
            or app.options.unregisterplugin
            ):
        app.parser.print_help()
        ShowResult("Error: no action specified")
        sys.exit(1)
    
    if app.options.sys_install or app.options.post_install:
        appdb = AppDb(path=tkConf.GetConfigDir())
        plugindb = PluginDb(path=tkConf.GetConfigDir())
        appdest = tkConf.GetSharedAppDir()
        plugindest = tkConf.GetPluginDir()
    else:
        appdb = AppDb()
        plugindb = PluginDb()
        appdest = UserConfig.instance().GetSharedAppDir()
        plugindest = UserConfig.instance().GetPluginDir()

    return app.options, appdb, plugindb, appdest, plugindest

"""
def ExtractZip_(zippath, dstpath):
    if not os.path.exists(path):
        os.mkdir(path)

    zf = zipfile.ZipFile( zippath, "r" )
    filenameList = zf.namelist()
    for filename in filenameList:
        try:
            # create subdirs if needed
            pathparts = string.split(filename, '/')

            if len(pathparts) > 1:
                temp_dir = str(path)
                for i in range(len(pathparts) - 1):
                    log.info("this is temp dir: %s"%(temp_dir))
                    log.info("this is pathparts: %s"%(pathparts))
                    temp_dir = os.path.join(temp_dir, pathparts[i])

                if not os.access(temp_dir, os.F_OK):
                    try:
                        os.makedirs(temp_dir)
                    except:
                        log.exception("Failed to make temp dir %s"%(temp_dir))
            destfilename = os.path.join(path,filename)

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

            #print "setting permissions on file", destfilename

            # Mark the file executable (indiscriminately)
            os.chmod(destfilename,0755)

            #s = os.stat(destfilename)
            #print "%s mode %d" % (destfilename, s[0])
        except:
            log.exception("Error extracting file %s"%(filename))
    zf.close()
"""


def UnpackPkg(filename):
    """
    This function takes the name of a zip file and unpacks it returning the
    directory it unpacked the zip into.
    """
    print "UnpackPkg:", filename
    zipArchive = zipfile.ZipFile(filename)
    # We have to unpack things some where we can use them
    if hasattr(tempfile, "mkdtemp"):
        workingDir = tempfile.mkdtemp()
    else:
        workingDir = tempfile.mktemp()
        os.mkdir(workingDir)
    appFile = None

    for f in zipArchive.namelist():
        parts = f.split('.')
        if len(parts) == 2 and parts[1] == 'app':
            appFile = f

    Utilities.ExtractZip(filename, workingDir)

    if appFile == None:
        raise Exception, "Invalid Shared Application Package."

    return (appFile, workingDir)

def UnpackPlugin(filename):
    """
    This function takes the name of a zip file and unpacks it returning the
    directory it unpacked the zip into.
    """
    zipArchive = zipfile.ZipFile(filename)
    # We have to unpack things some where we can use them
    if hasattr(tempfile, "mkdtemp"):
        workingDir = tempfile.mkdtemp()
    else:
        workingDir = tempfile.mktemp()
        os.mkdir(workingDir)
    pluginFile = None
    for filename in zipArchive.namelist():
        parts = filename.split('.')
        if len(parts) == 2 and parts[1] == 'plugin':
            pluginFile = filename
        bytes = zipArchive.read(filename)
        outpath = os.path.join(workingDir, filename)
        out = file(outpath, "wb")
        out.write(bytes)
        out.close()
        zinfo = zipArchive.getinfo(filename)
        if zinfo.external_attr == 2179792896:
            os.chmod(outpath, 0755)

    if pluginFile == None:
        raise Exception, "Invalid Plugin Application Package."


    return (pluginFile, workingDir)

def ProcessAppFile(appFile):
    """
    Process the Application File returning the appinfo and the command
    dictionary.
    """
    commands = dict()
    
    # Read in .app file
    appInfo = LoadConfig(appFile)

    # Build command list
    for key in appInfo.keys():
        spList = key.split('.')
        if len(spList) > 1:
            (section, option) = spList
            if section == "commands":
                verb = option
                cmd = appInfo[key]
                # If the named argument python is used, replace it
                if cmd.find("%(python)s") != -1:
                    if sys.platform == 'darwin':
                        cmd = cmd.replace("%(python)s", '/usr/bin/pythonw')
                    else:
                        cmd = cmd.replace("%(python)s", sys.executable)
                commands[verb] = cmd
    return appInfo, commands

def ProcessPluginFile(pluginFile):
    """
    Process the Plugin File returning the plugininfo and the command
    dictionary.
    """
    command = None

    # Read in .plugin file
    pluginInfo = LoadConfig(pluginFile)

    return pluginInfo, command

def PrepPackageFromCmdLine(options):
    cleanup = 0
    workingDir = None
    appFile = None
    appInfo = None
    commands = None
    
    # specified specific .app file
    if options.appfile:
        if os.path.isabs(options.appfile):
            workingDir = os.path.dirname(options.appfile)
            appFile = os.path.basename(options.appfile)
        else:
            workingDir = os.getcwd()
            appFile = options.appfile

    # specified a directory
    if options.appdir:
        workingDir = os.path.abspath(options.appdir)
        files = os.listdir(workingDir)
        for filename in files:
            spList = filename.split('.')
            if len(spList) == 2:
                (name, ext) = spList
                if ext == "app":
                    appFile = filename

    # specified a .zip or .agpkg3 file
    if options.appzip:
        return PrepPackage(options.appzip)

    if options.apppkg:
        return PrepPackage(options.apppkg)

    if appFile is not None and workingDir is not None:
        appFile = os.path.join(workingDir, appFile)
        appInfo, commands = ProcessAppFile(appFile)
        
    return appInfo, commands, workingDir, cleanup

def PrepPluginFromCmdLine(options):
    cleanup = 0
    workingDir = None
    pluginFile = None
    pluginInfo = None
    command = None

    # specified a .zip or .agpkg file
    if options.appzip:
        return PrepPlugin(options.appzip)

    if options.apppkg:
        return PrepPlugin(options.apppkg)

    if pluginFile is not None and workingDir is not None:
        pluginFile = os.path.join(workingDir, appFile)
        pluginInfo, command = ProcessAppFile(appFile)

    return pluginInfo, command, workingDir, cleanup

def PrepPackage(package):
    cleanup = 0
    workingDir = None
    appInfo = None
    commands = None
    appFile = None

    try:
        appFile, workingDir = UnpackPkg(package)
        appFile = os.path.join(workingDir, appFile)
        cleanup = 1
    except Exception:
        log.exception("PrepPackage")
        if workingDir is not None:
            shutil.rmtree(workingDir)
        raise
            
    if appFile is None:
        raise Exception, "No valid package specified, exiting."
    else:
        appInfo, commands = ProcessAppFile(appFile)
        
    return appInfo, commands, workingDir, cleanup

def PrepPlugin(package):
    cleanup = 0
    workingDir = None
    pluginInfo = None
    command = None
    pluginFile = None

    try:
        pluginFile, workingDir = UnpackPlugin(package)
        pluginFile = os.path.join(workingDir, pluginFile)
        cleanup = 1
    except Exception:
        log.exception("PrepPlugin")
        if workingDir is not None:
            shutil.rmtree(workingDir)
        raise

    if pluginFile is None:
        raise Exception, "No valid package specified, exiting."
    else:
        pluginInfo, command = ProcessPluginFile(pluginFile)

    return pluginInfo, command, workingDir, cleanup

def UnregisterAppPackage(appdb, appInfo, name):
        if appInfo != None and name == None:
            name = appInfo["application.name"]
        if name != None:
            appdb.UnregisterApplication(name=name)
        else:
            raise Exception, "No application name discovered, exiting without doing unregister."

def RegisterAppPackage(appdb, dest, appInfo, commands, workingDir=None,
                    cleanup=0):

    # some error checking upfront
    if not appInfo['application.extension']:
        raise InvalidApplicationDescription('no extension given')
                   
    origDir = os.getcwd()

    # Otherwise we go through and do the registration stuff...
    if workingDir != None and workingDir != '':
        # Change to the appropriate directory
        # This won't work for zipfiles
        os.chdir(workingDir)
        
    # Register the App
    files = appInfo["application.files"]
    if type(appInfo["application.files"]) is StringType:
        files = re.split(r',\s*|\s+', files)

    # Applications are "startable" (i.e. from the VenueClient) by default.
    if "application.startable" not in appInfo.keys():
        appInfo["application.startable"] = "1"

    result = appdb.RegisterApplication(appInfo["application.name"],
                              appInfo["application.mimetype"],
                              appInfo["application.extension"],
                              commands, files,
                              workingDir,
                              dstPath=dest,
                              startable=appInfo["application.startable"])
    if 0==result:
        "Unable to register application %s" % appInfo["application.name"]
        sys.exit(1)

    # Clean up, remove the temporary directory and files from
    # unpacking the zip file
    if cleanup:
        os.chdir(origDir)
        if workingDir is not None:
            shutil.rmtree(workingDir)

    ShowResult("Successfully installed application %s." % appInfo["application.name"], "Application Installed")
            
            
def RegisterServicePackage(servicePackage):
    tkConf = AGTkConfig.instance()
    servicePackageFile = os.path.split(servicePackage)[1]
    servicePackagePath = os.path.join(tkConf.GetNodeServicesDir(),servicePackageFile)
    
    try:
        shutil.copy(servicePackage,servicePackagePath)
        # Set the permissions correctly
        os.chmod(servicePackagePath,0644)
    except Exception, e:
        log.exception("RegisterServicePackage")
        ShowResult(str(e))
        return
    
    ShowResult( "Installation of service %s complete." % (servicePackageFile,), "Service Installed")


def UnregisterPluginPackage(pluginDb, pluginInfo, name):
        if pluginInfo != None and name == None:
            name = appInfo["application.name"]
        if name != None:
            pluginDb.UnregisterPlugin(name=name)
        else:
            raise Exception, "No such plugin, exiting without doing unregister."

def RegisterPluginPackage(plugindb, dest, pluginInfo, commands, workingDir=None,
                    cleanup=0):
    origDir = os.getcwd()

    # Otherwise we go through and do the registration stuff...
    if workingDir != None and workingDir != '':
        # Change to the appropriate directory
        # This won't work for zipfiles
        os.chdir(workingDir)

    # Register the Plugin
    files = pluginInfo["plugin.files"]
    if type(pluginInfo["plugin.files"]) is StringType:
        files = re.split(r',\s*|\s+', files)

    description = None
    if pluginInfo.has_key("plugin.description"):
        description = pluginInfo["plugin.description"]

    command = None
    if pluginInfo.has_key("plugin.command"):
        command = pluginInfo["plugin.command"]

    module = None
    if pluginInfo.has_key("plugin.module"):
        module = pluginInfo["plugin.module"]

    icon = None
    if pluginInfo.has_key("plugin.icon"):
        icon = pluginInfo["plugin.icon"]

    result = plugindb.RegisterPlugin(pluginInfo["plugin.name"],
                                     description,
                                     command,
                                     module,
                                     icon,
                                     files,
                                     workingDir,
                                     dstPath=dest)
    if 0==result:
        ShowResult("Unable to register plugin %s" % pluginInfo["plugin.name"])
        sys.exit(1)

    # Clean up, remove the temporary directory and files from
    # unpacking the zip file
    if cleanup:
        os.chdir(origDir)
        if workingDir is not None:
            shutil.rmtree(workingDir)

    ShowResult("Successfully installed plugin %s." % pluginInfo["plugin.name"], "Plugin Installed")

def UnregisterServicePackage(servicePackageFile):
    tkConf = AGTkConfig.instance()
    servicePackagePath = os.path.join(tkConf.GetNodeServicesDir(),servicePackageFile)
    
    try:
        os.remove(servicePackagePath)
        ShowResult( "Unregistration of service package %s complete." % (servicePackageFile,) )
    except Exception, e:
        log.exception("UnregisterServicePackage")
        ShowResult( e )

def main():
    """
    This is the main, this function processes command line arguments,
    then digs the files out of the directory, or archive and installs them.
    It registers the application with the users AG environment.
    """
    workingDir = os.getcwd()
    commands = dict()
    files = list()
    cleanup = 0

    tkConf = AGTkConfig.instance()
    
    # We're going to assume there's a .app file in the current directory,
    # but only after we check for a command line argument that specifies one.
    # We also have the ability to pass in a zip file that contains a .app
    # file and the other parts of the shared application.

    app = Toolkit.CmdlineApplication.instance()
    options, appdb, plugindb, appdest, plugindest = InitAppAndProcessArgs(app)

    #
    # Handle list-only options
    #
    if options.listapps:
        apps = appdb.ListApplications()
        import pprint
        pprint.pprint(apps)
        sys.exit(0)
        
    if options.listservices:
        files = os.listdir(tkConf.GetNodeServicesDir())
        for f in files:
            print f
        sys.exit(0)

    if options.listplugins:
        plugins = plugindb.ListPlugins()
        import pprint
        pprint.pprint(plugins)
        sys.exit(0)
    
        
    # 
    # Handle command-line errors
    #   
    if options.appfile and not os.path.exists(options.appfile):
        ShowResult("Error: app file does not exist: %s" % options.appfile )
        sys.exit(1)
    if options.appdir and not os.path.exists(options.appdir):
        ShowResult("Error: dir does not exist: %s" % options.appdir )
        sys.exit(1)
    if options.apppkg and not os.path.exists(options.apppkg):
        ShowResult("Error: package file does not exist: %s" % options.apppkg )
        sys.exit(1)
    if options.appzip and not os.path.exists(options.appzip):
        ShowResult("Error: zip file does not exist: %s" % options.appzip)
        sys.exit(1)
        
    #
    # Determine whether it's a service or app package
    #
    isServicePackage = 0
    isPluginPackage = 0
    if options.appzip or options.apppkg:
        
        try:
            filename=options.appzip or options.apppkg
            zipArchive = zipfile.ZipFile(filename)
            for filename in zipArchive.namelist():
                if filename.endswith('.svc'):
                    isServicePackage = 1
                    break
                elif filename.endswith('.plugin'):
                    isPluginPackage = 1
                    break
        except zipfile.BadZipfile,e:
            log.exception("Error in zipfile %s", filename)
            ShowResult( "Error in zipfile %s: %s" % (filename,e.args[0]))
            sys.exit(1)
            
    
    if options.unregisterservice:
        isServicePackage = 1

    if options.unregisterplugin:
        isPluginPackage = 1
        
    #
    # Register/Unregister packages
    #    
    if isServicePackage:
    
        #
        # Handle a service package
        #
        if options.sys_install:
            print "(note: the -s flag is ignored for Service Packages since they are always installed in a system-wide location.)"

        filename=options.appzip or options.apppkg or options.appname
        if options.unregisterservice:
            if not options.appname:
                ShowResult( "No service package specified to unregister")
                sys.exit(1)
            if options.verbose:
                print "Unregistering service package: ", filename
            UnregisterServicePackage(filename)
        else:
            if options.verbose:
                print "Registering service package: ", filename
            RegisterServicePackage(filename)
    elif isPluginPackage:
        # At this point we have an pluginFile and workingDir
        pluginList = []

        pluginInfo = PrepPluginFromCmdLine(options)
        pluginList.append(pluginInfo)

        for plugin in pluginList:
            pluginInfo, command, workingDir, cleanup = plugin

            if options.verbose:
                print "Name: %s" % pluginInfo["plugin.name"]
                if pluginInfo.has_key("plugin.description"):
                    print "Description: %s" % pluginInfo["plugin.description"]
                if pluginInfo.has_key("plugin.command"):
                    print "Command: %s" % pluginInfo["plugin.command"]
                if pluginInfo.has_key("plugin.module"):
                    print "Module: %s" % pluginInfo["plugin.module"]
                if pluginInfo.has_key("plugin.icon"):
                    print "Icon: %s" % pluginInfo["plugin.icon"]
                print "Working Dir: %s" % workingDir

            # If we unregister, we do that then exit
            if options.unregisterplugin:
                if not options.appname:
                    ShowResult( "No plugin specified for unregister")
                    sys.exit(1)
                UnregisterPluginPackage(plugindb, pluginInfo, options.appname)
            else:
                RegisterPluginPackage(plugindb, plugindest, pluginInfo,
                                      command, workingDir, cleanup)        
    else:
    
        #
        # Handle an application package
        #

        pkgList = []

        #
        # Post-install setup run
        #
        if options.post_install:
            pkgCache = tkConf.GetSharedAppDir()
            for pkg in os.listdir(pkgCache):
                fnl = pkg.split('.')
                if len(fnl) == 2:
                    (name, ext) = fnl
                    if ext == "agpkg" or ext == "agpkg3":
                        pkgInfo = PrepPackage(os.path.join(pkgCache, pkg))
                        pkgList.append(pkgInfo)

        else:

            # At this point we have an appFile and workingDir
            try:
                pkgInfo = PrepPackageFromCmdLine(options)
                pkgList.append(pkgInfo)
            except Exception, e:
                log.exception("Error in package file")
                ShowResult("Error in package file: %s" % e)

        excList = []

        for pkg in pkgList:
            try:
                appInfo, commands, workingDir, cleanup = pkg

                if options.verbose:
                    print "Name: %s" % appInfo["application.name"]
                    print "Mime Type: %s" % appInfo["application.mimetype"]
                    print "Extension: %s" % appInfo["application.extension"]
                    print "From: %s" % workingDir

                # If we unregister, we do that then exit
                if options.unregister:
                    if not options.appname:
                        ShowResult( "No application specified for unregister")
                        sys.exit(1)
                    UnregisterAppPackage(appdb, appInfo, options.appname)
                else:
                    RegisterAppPackage(appdb, appdest, appInfo, commands,
                                    workingDir, cleanup)
            except InvalidApplicationDescription,e:
                msg = '%s %s: Invalid application description: %s\n' % (pkg, appInfo["application.name"],str(e))
                log.exception(msg)
                excList.append(msg)
            except Exception,e:
                msg = '%s: %s: %s\n' % (appInfo["application.name"], str(e.__class__), str(e))
                log.exception(msg)
                excList.append(msg)

        if excList:
            msg = "The following errors occurred during application installation:\n\n"
            for e in excList:
                msg += e
            ShowResult(msg)
    
    if options.wait_for_input:
        try:
            raw_input('AGPM: hit return to exit.')
        except EOFError:
            pass
        
if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except:
        # A catch all exception -- ideally all exceptions will be caught before this.
        import traceback
        traceback.print_exc()
        if "--gui" in sys.argv:
            import wx
            from AccessGrid.UIUtilities import ErrorDialog
            ex_class, ex_instance, trace_obj = sys.exc_info()
            text = traceback.format_exception(ex_class, ex_instance, trace_obj)
            message = "".join(text)
            try: wxapp = wx.PySimpleApp()
            except: pass
            dialog = ErrorDialog(None, "Error running the Package Manager.", "Package Manager Error", extraBugCommentText=message)

