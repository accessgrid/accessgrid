# Linux Defaults
AGTkBasePath = "/etc/AccessGrid"

def GetSystemConfigDir():
    """
    Determine the system configuration directory
    """
    try:
        configDir = os.environ[AGTK_LOCATION]
    except:
        configDir = AGTkBasePath

    return configDir

def GetUserConfigDir():
    """
    Determine the user configuration directory
    """
    try:
        configDir = os.environ[AGTK_USER]
    except:
        configDir = os.path.join(os.environ["HOME"],".AccessGrid")

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

    WARNING: This should be set during installation, not hardwired here.
    """
    try:
        installDir = os.environ[AGTK_INSTALL]
    except:
        installDir = "/usr/bin"

    return installDir

def GetSharedDocDir():
    """
    Determine the shared doc directory

    WARNING: This should be set during installation, not hardwired here.
    """
    try:
        sharedDocDir = os.environ[AGTK_INSTALL]
    except:
        sharedDocDir = "/usr/share/doc/AccessGrid/Documentation"

    return sharedDocDir

def GetTempDir():
    """
    Return a directory in which temporary files may be written.

    WARNING: This should be set during installation, not hardwired here.
    """
    return "/tmp"


def GetSystemTempDir():
    """
    Return a directory in which temporary files may be written.
    The system temp dir is guaranteed to not be tied to any particular user.

    WARNING: This should be set during installation, not hardwired here.
    """

    return "/tmp"

def GetUsername():
    """ This isn't used on linux? """
    
    if isWindows():
        try:
            user = win32api.GetUserName()
            user.replace(" ", "")
            return user
        except:
            pass

    return getpass.getuser()


def GetFilesystemFreeSpace(path):
    """
    Determine the amount of free space available in the filesystem
    containing <path>.

    Returns a value in bytes.
    """

    #
    # On Unix-like systems (including Linux) we can use os.statvfs.
    #
    # f_bsize is the "preferred filesystem block size"
    # f_frsize is the "fundamental filesystem block size"
    # f_bavail is the number of blocks free
    #
    if hasattr(os, "statvfs"):
        x = os.statvfs(path)

        #
        # On some older linux systems, f_frsize is 0. Use f_bsize instead then.
        # cf http://www.uwsg.iu.edu/hypermail/linux/kernel/9907.3/0019.html
        #
        if x.f_frsize == 0:
            blockSize = x.f_bsize
        else:
            blockSize = x.f_frsize

        freeBytes = blockSize * x.f_bavail
    else:
        freeBytes = None

    return freeBytes

def InitUserEnv():
    """
    This is the place for user initialization code to go.
    """
    pass

def GetMimeType(extension = None):
    """
    """
    fauxFn = ".".join(["Faux", extension])
    mimetypes.init()

    # This is always a tuple so this is Ok
    mimeType = mimetypes.guess_type(fauxFn)[0]

    return mimeType

def GetMimeCommands(mimeType = None, ext = None):
    """
    """
    cdict = dict()
    view = 'view'

    if mimeType == None:
        mimeType = GetMimeType(extension = ext)

    # We only care about mapping view to Open
    caps = mailcap.getcaps()

    # This always returns a tuple, so this should be safe
    if mimeType != None:
        match = mailcap.findmatch(caps, mimeType, view)[1]
    else:
        return cdict

    if match != None:
        cdict['Open'] = match[view]

    return cdict

#
# Unix Daemonize, this is not appropriate for Win32
#

def Daemonize():
    try:
        pid = os.fork()
    except:
        print "Could not fork"
        sys.exit(1)

        if pid:
            # Let parent die !
            sys.exit(0)
        else:
            try:
                # Create new session
                os.setsid()
            except:
                print "Could not create new session"
                sys.exit(1)

def SetRtpDefaults( profile ):
    """
    Set registry values used by vic and rat for identification
    """
    #
    # Write the rtp defaults file
    #
    rtpDefaultsText="*rtpName: %s\n*rtpEmail: %s\n*rtpLoc: %s\n*rtpPhone: \
                     %s\n*rtpNote: %s\n"
    rtpDefaultsFile=open( os.path.join(os.environ["HOME"], ".RTPdefaults"),"w")
    rtpDefaultsFile.write( rtpDefaultsText % ( profile.name,
    profile.email,
    profile.location,
    profile.phoneNumber,
    profile.publicId ) )
    rtpDefaultsFile.close()
