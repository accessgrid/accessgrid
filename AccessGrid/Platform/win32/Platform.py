import os
import sys

from AccessGrid import Log
from AccessGrid.Version import GetVersion

log = Log.GetLogger(Log.Platform)
Log.SetDefaultLevel(Log.Platform, Log.INFO)

# Windows Defaults
try:
    import _winreg
    import win32api
    from win32com.shell import shell, shellcon
except:
    print "Python windows extensions are missing, but required!"
    pass

# This gets updated with a call to get the version
AGTkRegBaseKey = "SOFTWARE\Access Grid Toolkit\%s" % GetVersion()

def GetSystemConfigDir():
    """
    Determine the system configuration directory
    """
    global AGTK_LOCATION
    try:
        configDir = os.environ[AGTK_LOCATION]
    except:
        base = shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_APPDATA, 0, 0)
        configDir = os.path.join(base, "AccessGrid")

    return configDir

def GetUserConfigDir():
    """
    Determine the user configuration directory
    """
    global AGTK_USER
    try:
        configDir = os.environ[AGTK_USER]
    except:
        base = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        configDir = os.path.join(base, "AccessGrid")
    return configDir

def GetUserAppPath():
    """
    Return the path to the users shared applications directory.
    """
    ucd = GetUserConfigDir()
    appPath = os.path.join(ucd, "SharedApplications")

    return appPath

def GetConfigFilePath( configFile ):
    """
    Locate given file in configuration directories:
    first check user dir, then system dir;
    return None if not found
    """

    userConfigPath = GetUserConfigDir()
    pathToFile = os.path.join(userConfigPath,configFile)
    if os.path.exists( pathToFile ):
        return pathToFile

    systemConfigPath = GetSystemConfigDir()
    pathToFile = os.path.join(systemConfigPath,configFile)
    if os.path.exists( pathToFile ):
        return pathToFile

    return None

def GetInstallDir():
    """
    Determine the install directory
    """
    global AGTkRegBaseKey, AGTK_INSTALL
    try:
        installDir = os.environ[AGTK_INSTALL]
    except:
        try:
            AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
            installDir, valuetype = _winreg.QueryValueEx(AG20,"InstallPath")
            installDir = os.path.join(installDir, "bin")
        except:
            installDir = ""

    return installDir

def GetSharedDocDir():
    """
    Determine the shared doc directory
    """
    global AGTkRegBaseKey, AGTK_INSTALL
    
    try:
        sharedDocDir = os.environ[AGTK_INSTALL]
    except:
        try:
            AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, AGTkRegBaseKey)
            sharedDocDir, valuetype = _winreg.QueryValueEx(AG20,"InstallPath")
            sharedDocDir = os.path.join(sharedDocDir, "doc")
        except:
            sharedDocDir = ""
        
    return sharedDocDir

def GetTempDir():
    """
    Return a directory in which temporary files may be written.
    """
    return win32api.GetTempPath()

def GetSystemTempDir():
    """
    Return a directory in which temporary files may be written.
    The system temp dir is guaranteed to not be tied to any particular user.
    """
    winPath = win32api.GetWindowsDirectory()
    return os.path.join(winPath, "TEMP")

def GetUsername():
    try:
        user = win32api.GetUserName()
        user.replace(" ", "")
        return user
    except:
        raise

def GetFilesystemFreeSpace(path):
    """
    Determine the amount of free space available in the filesystem
    containing <path>.

    Returns a value in bytes.
    """
    #
    # Otherwise use win32api.GetDiskFreeSpace.
    #
    # From the source to win32api:
    #
    # The return value is a tuple of 4 integers, containing
    # the number of sectors per cluster, the number of bytes per sector,
    # the total number of free clusters on the disk and the total number of
    # clusters on the disk.
    #

    try:
        x = win32api.GetDiskFreeSpace(path)

        freeBytes = x[0] * x[1] * x[2]
    except:
        freeBytes = None

    return freeBytes

def FindRegistryEnvironmentVariable(varname):
    """
    Find the definition of varname in the registry.
    
    Returns the tuple (global_value, user_value).
    
    We can use this to determine if the user has set an environment
    variable at the commandline if it's causing problems.
    
    """
    env_key = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    global_reg = None
    user_reg = None
    
    #
    # Read the system registry
    #
    k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, env_key)
              
    try:
        (val, valuetype) = _winreg.QueryValueEx(k, varname)
        global_reg = val
    except:
        pass
    k.Close()
    
    # Read the user registry
    k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Environment")
    
    try:
        (val, valuetype) = _winreg.QueryValueEx(k, varname)
        user_reg = val
    except:
        pass
    k.Close()
    
    
    return (global_reg, user_reg)

def SendSettingChange():
    """
    This updates all windows with registry changes to the HKCU\Environment key.
    """
    import win32gui, win32con
    
    ret = win32gui.SendMessageTimeout(win32con.HWND_BROADCAST,
                                      win32con.WM_SETTINGCHANGE, 0,
                                      "Environment", win32con.SMTO_NORMAL,
                                      1000)
    return ret

def RegisterMimeType(mimeType, extension, fileType, description, cmds):
    """
    mimeType - mimetype designator
    extension - file extension
    (doesn't have to be 3 letters, does have to start with a .)
    fileType - file type, doesn't matter, just unique
    description - free form description of the type

    list of:
    verb - name of command
    command - the actual command line
    commandDesc - a description (menu format) for the command

    ----

    This function gets the mime type registered with windows via the registry.
    The following documentation is from wxWindows, src/msw/mimetype.cpp:

        1. "HKCR\MIME\Database\Content Type" contains subkeys for all
        known MIME types, each key has a string value "Extension"
        which gives (dot preceded) extension for the files of this
        MIME type.

        2. "HKCR\.ext" contains

            a) unnamed value containing the "filetype"
        
            b) value "Content Type" containing the MIME type


        3. "HKCR\filetype" contains

            a) unnamed value containing the description

            b) subkey "DefaultIcon" with single unnamed value giving
            the icon index in an icon file

            c) shell\open\command and shell\open\print subkeys
            containing the commands to open/print the file (the
            positional parameters are introduced by %1, %2, ... in
            these strings, we change them to %s ourselves)

    """

    # Do 1. from above
    try:
        regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT,
        "MIME\Database\Content Type\%s" % mimeType)
        _winreg.SetValueEx(regKey, "Extension", 0, _winreg.REG_SZ, extension)
        _winreg.CloseKey(regKey)
    except EnvironmentError:
        log.debug("Couldn't open registry for mime registration!")

    # Do 2. from above
    try:
        regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT, extension)

        _winreg.SetValueEx(regKey, "", 0, _winreg.REG_SZ, fileType)
        _winreg.SetValueEx(regKey, "Content Type", 0, _winreg.REG_SZ, mimeType)

        _winreg.CloseKey(regKey)
    except EnvironmentError:
        log.debug("Couldn't open registry for mime registration!")

    # Do 3. from above
    try:
        regKey = _winreg.CreateKey(_winreg.HKEY_CLASSES_ROOT, fileType)

        _winreg.SetValueEx(regKey, "", 0, _winreg.REG_SZ, description)

        icoKey = _winreg.CreateKey(regKey, "DefaultIcon")
        _winreg.SetValueEx(icoKey, "", 0, _winreg.REG_SZ, "")
        _winreg.CloseKey(icoKey)

        shellKey = _winreg.CreateKey(regKey, "shell")

        for trio in cmds:
            (verb, command, commandDesc) = trio
            verbKey = _winreg.CreateKey(shellKey, verb)
            _winreg.SetValueEx(verbKey, "", 0, _winreg.REG_SZ, commandDesc)
            cmdKey = _winreg.CreateKey(verbKey, "command")
            # Make sure this is quoted
            lwords = command.split(' ')
            lwords[0] = "\"%s\"" % lwords[0]

            newcommand = " ".join(lwords)
            _winreg.SetValueEx(cmdKey, "", 0, _winreg.REG_SZ, newcommand)
            _winreg.CloseKey(cmdKey)
            _winreg.CloseKey(verbKey)

        _winreg.CloseKey(shellKey)

        _winreg.CloseKey(regKey)
    except EnvironmentError, e:
        log.debug("Couldn't open registry for mime registration!")

def GetMimeCommands(mimeType = None, ext = None):
    """
    This gets the mime commands from one of the three types of specifiers
    windows knows about. Depending on which is passed in the following
    trail of information is retrieved:

        1. "HKCR\MIME\Database\Content Type" contains subkeys for all
        known MIME types, each key has a string value "Extension"
        which gives (dot preceded) extension for the files of this
        MIME type.

        2. "HKCR\.ext" contains
            a) unnamed value containing the "filetype"
            b) value "Content Type" containing the MIME type

        3. "HKCR\filetype" contains
            a) unnamed value containing the description
            b) subkey "DefaultIcon" with single unnamed value giving
            the icon index in an icon file
            c) shell\open\command and shell\open\print subkeys
            containing the commands to open/print the file (the
            positional parameters are introduced by %1, %2, ... in
            these strings, we change them to %s ourselves)
    """
    cdict = dict()
    filetype = None
    extension = ext

    log.debug("MimeType: %s", mimeType)

    if mimeType != None:
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
            "MIME\Database\Content Type\%s" % mimeType)
            extension, type = _winreg.QueryValueEx(key, "Extension")
            _winreg.CloseKey(key)
        except WindowsError:
            log.warn("Couldn't open registry for mime types: %s",
            mimeType)
            return cdict

    log.debug("Extension: %s", extension)

    if extension != None:
        if extension[0] != ".":
            extension = ".%s" % extension
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "%s" % extension)
            filetype, type = _winreg.QueryValueEx(key, "")
            _winreg.CloseKey(key)
        except WindowsError:
            log.warn("Couldn't open registry for file extension: %s.",
            extension)
            return cdict

    log.debug("FileType: %s", filetype)
    
    if filetype != None:
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
            "%s\shell" % filetype)
            nCommands = _winreg.QueryInfoKey(key)[0]

            log.debug("Found %d commands for filetype %s.", nCommands,
                      filetype)

            for i in range(0,nCommands):
                commandName = _winreg.EnumKey(key, i)
                command = None
                # Always use caps for names to make life easier
                try:
                    ckey = _winreg.OpenKey(key, "%s\command" % commandName)
                    command, type = _winreg.QueryValueEx(ckey,"")
                    _winreg.CloseKey(ckey)
                except:
                    log.warn("Couldn't get command for name: <%s>",
                    commandName)
                commandName = commandName.capitalize()
                cdict[commandName] = command

            _winreg.CloseKey(key)

        except EnvironmentError:
            warnStr = "Couldn't retrieve list of commands: (mimeType: %s) \
                       (fileType: %s)"
            log.warn(warnStr, mimeType, filetype)
            return cdict

    return cdict

def GetMimeType(extension = None):
    mimeType = None
    if extension != None:
        if extension[0] != ".":
            extension = ".%s" % extension
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "%s" % extension)
            mimeType, type = _winreg.QueryValueEx(key, "Content Type")
            _winreg.CloseKey(key)
        except WindowsError:
            log.warn("Couldn't open registry for file extension: %s.",
            extension)
            return mimeType

    return mimeType

def InitUserEnv():

    # Register application installer mime type
    #
    #  shared app package mime type: application/x-ag-shared-app-pkg
    #  shared app package extension: .shared_app_pkg

    installCmd = win32api.GetShortPathName(os.path.join(GetInstallDir(),
                                                        "agpm.py"))
    sharedAppPkgType = "application/x-ag-shared-app-pkg"
    sharedAppPkgExt = ".shared_app_pkg"
    sharedAppPkgDesc = "A shared application package for use with the Access \
    Grid Toolkit 2.0."
    
    open = ('Open', "%s %s -p %%1" % (sys.executable, installCmd),
            "Install this shared application.")
    sharedAppPkgCmds = list()
    sharedAppPkgCmds.append(open)

    RegisterMimeType(sharedAppPkgType, sharedAppPkgExt,
                          "x-ag-shared-app-pkg", sharedAppPkgDesc,
                          sharedAppPkgCmds)

    log.debug("registered agpm for shared app packages.")
    
    # Install applications found in the shared app repository
    # Only install those that are not found in the user db.

    sharedPkgPath = os.path.join(GetSystemConfigDir(), "sharedapps")

    log.debug("Looking in %s for shared apps.", sharedPkgPath)
    
    if os.path.exists(sharedPkgPath):
        for pkg in os.listdir(sharedPkgPath):
            t = pkg.split('.')
            if len(t) == 2:
                (name, ext) = t
                if ext == "shared_app_pkg":
                    pkgPath = win32api.GetShortPathName(os.path.join(sharedPkgPath, pkg))
                    # This will wait for the completion cuz of the P_WAIT
                    pid = os.spawnv(os.P_WAIT, sys.executable, (sys.executable,
                                                                installCmd,
                                                                "-p", pkgPath))
                else:
                    log.debug("Not registering file: %s", t)
            else:
                log.debug("Filename wrong, not registering: %s", t)
        else:
            log.debug("No shared package directory.")
            
    # Invoke windows magic to get settings to be recognized by the
    # system. After this incantation all new things know about the
    # settings.
    SendSettingChange()
    
    return 1
    
