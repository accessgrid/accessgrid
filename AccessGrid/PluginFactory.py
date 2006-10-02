import os
import sys

from AccessGrid.Plugin import Plugin
from AccessGrid.Descriptions import PluginDescription
from AccessGrid import Log

from AccessGrid.Platform import Config

log = Log.GetLogger("PluginFactory")

def BuildPlugin(pluginDesc):
    if not pluginDesc:
        log.exception("Null plugin description.")
        return None

    if not isinstance(pluginDesc, PluginDescription):
        log.exception("Invalid type, expected PluginDescription.")
        return None

    namenospace = pluginDesc.name.replace(' ', '_')

    sysdir = os.path.join(Config.AGTkConfig.instance().GetPluginDir(),
                          namenospace)
    userdir = os.path.join(Config.UserConfig.instance().GetPluginDir(),
                           namenospace)
    olddir = os.getcwd()
        
    if os.access(userdir, os.R_OK):
        pluginDir = userdir
    elif os.access(sysdir, os.R_OK):
        pluginDir = sysdir
    else:
        log.exception('Plugin %s is not installed' % pluginDesc.name)
        return None
        
    if pluginDesc.module and len(pluginDesc.module):
        os.chdir(pluginDir)
        
        # Shouldn't have to do this ... but I do
        if '.' not in sys.path:
            sys.path.append('.')
            
        try:
            mod = __import__(pluginDesc.module)
        except Exception, e:
            print 'Failed to import module for plugin %s: ' % pluginDesc.name
            print '  ', e
            print '  ', os.getcwd()
            print '  ', sys.path
            os.chdir(olddir)
            return None
        
        os.chdir(olddir)
        
        if hasattr(mod, pluginDesc.module):
            if type(mod.__dict__[pluginDesc.module]) != type(Plugin):
                log.exception("Class %s is not super of AccessGrid.Plugin!" % pluginDesc.module)
                return None
            
            try:
                plugin = mod.__dict__[pluginDesc.module](pluginDir, pluginDesc.name, pluginDesc.description, pluginDesc.command, pluginDesc.icon)
                if not isinstance(plugin, Plugin):
                    #
                    # Not possible considering already checked just above.
                    #
                    log.exception('Plugin %s is not a derived class of Plugin' % pluginDesc.name)
                    return None
                
                return plugin
            except Exception, e:
                log.exception('Failed to instantiate plugin %s: %s' % (pluginDesc.name, e))
                return None
                
        else:
            log.exception('Plugin %s does not have matching class named %s' % (pluginDesc.name, pluginDesc.module))
            print dir(mod)
            return None

    elif pluginDesc.command and len(pluginDesc.command):
        return Plugin(pluginDir, pluginDesc.name, pluginDesc.description, pluginDesc.command, pluginDesc.icon)
    else:
        #
        # A plugin requires either a command or a module.
        #
        log.exception("Invalid plugin: A plugin requires either a command or a module to be set.")
        return None
        
