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
    
