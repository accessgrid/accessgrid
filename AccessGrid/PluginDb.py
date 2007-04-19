
import os
import sys
import shutil

sys.path.insert(0, '/usr/lib/python2.4/site-packages/AccessGrid3')

from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.Descriptions import PluginDescription
from AccessGrid.GUID import GUID
from AccessGrid import Log

log = Log.GetLogger(Log.PluginDb)

#
# Copied from AppDB
#
# Config file
# [<key>]
# name = <name>
# command = <cmd>
# 
#

class PluginDb:

    defaultSeparator = ':'

    def __init__(self, path=None, filename="PluginDatabase"):

        self.PluginDb = dict()

        if path is None:
            self.path = UserConfig.instance().GetConfigDir()
        else:
            self.path = path

        self.fileName = os.path.join(self.path, filename)

        if not os.path.exists(self.fileName):
            try:
                file(self.fileName, 'w').close()
            except:
                log.exception('Couldn\'t create app db file %s', self.fileName)

        self.Load(self.fileName)

    def Load(self, fileName=None):
        if fileName == None:
            fileName = self.fileName

        try:

            self.PluginDb = LoadConfig(fileName,
                                       separator=self.defaultSeparator)

        except:
            print sys.exc_info()
            print 'Couldn\'t open Plugin Database: %s' % fileName

        #print 'Loaded %s' % fileName

    def Save(self, fileName=None):
        if fileName == None:
            fileName = self.fileName

        try:
            SaveConfig(fileName, self.PluginDb, self.defaultSeparator)

        except Exception, e:
            print 'Couldn\'t write Plugin Database: %s: ' % fileName, e

    def RegisterPlugin(self, name, description, command, module, icon, fileList, srcPath, dstPath):

        success = 0
        
        noSpaceName = name.replace(' ', '_')
        dstPath = os.path.join(dstPath, noSpaceName)

        print 'rp: intalling into %s' % dstPath
        
        if self._add_plugin(name, description, command, module, icon):
            
            if not os.path.exists(dstPath):
                try:
                    os.mkdir(dstPath)
                except:
                    print 'Couldn\'t make app directory (%s).' % dstPath

            for appFile in fileList:
                try:
                    srcf = os.path.join(srcPath, appFile)
                    dstf = os.path.join(dstPath, appFile)
                    shutil.copy(srcf, dstf)
                    success = 1
                        
                except Exception, e:
                    print 'Couldn\'t copy file into place (%s->%s).' % (srcf, dstf)
                    print '  ', e
                    success = 0
                    break
            
        return success
    
    def UnregisterPlugin(self, name):
        noSpaceName = '_'.join(name.split(' '))
        dstPath = os.path.join(UserConfig.instance().GetPluginDir(), 
                               noSpaceName)

        if os.path.exists(dstPath):
            try:
                shutil.rmtree(dstPath)
                print "Unregistration of application %s complete" % (name)
            except:
                print "App directory error -- can't remove (%s)." % dstPath
        else:
            print "Application %s not found; skipping" % (name)
            return 0

        return self._remove_plugin(name)

    def _add_plugin(self, name, description, command, module, icon):

        namekey = self._get_priv_name(name)
        if namekey == None:
            namekey = str(GUID())

        privName = self.defaultSeparator.join(['priv_names', namekey])
        nameStr = self.defaultSeparator.join(['name', namekey])
        desckey = self.defaultSeparator.join(['priv_desc', namekey])
        cmdkey = self.defaultSeparator.join(['priv_cmds', namekey])
        modulekey = self.defaultSeparator.join(['priv_modules', namekey])
        iconkey = self.defaultSeparator.join(['priv_icons', namekey])
        

        self.PluginDb[privName] = name
        self.PluginDb[desckey] = description
        self.PluginDb[cmdkey] = command
        self.PluginDb[modulekey] = module
        self.PluginDb[iconkey] = icon

        self.Save()

        return True

    def _remove_plugin(self, name):
        namekey = self._get_priv_name(name)
        if namekey == None:
            namekey = str(GUID())

        privName = self.defaultSeparator.join(['priv_names', namekey])
        nameStr = self.defaultSeparator.join(['name', namekey])
        desckey = self.defaultSeparator.join(['priv_desc', namekey])
        cmdkey = self.defaultSeparator.join(['priv_cmds', namekey])
        modulekey = self.defaultSeparator.join(['priv_modules', namekey])
        iconkey = self.defaultSeparator.join(['priv_icons', namekey])

        #
        # The ,None prevents an exception being thrown that we don't
        # care about, ie KeyError
        #
        self.PluginDb.pop(privName, None)
        self.PluginDb.pop(desckey, None)
        self.PluginDb.pop(cmdkey, None)
        self.PluginDb.pop(modulekey, None)
        self.PluginDb.pop(iconkey, None)

        self.Save()

        return True

    def _get_priv_name(self, name):

        pname = None
        for key in self.PluginDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == 'priv_names':
                if self.PluginDb[key] == name:
                    pname = option

        return pname
        
    def ListPlugins(self):

        plugins = list()

        for key in self.PluginDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == 'priv_names':
                plugins.append(self.PluginDb[key])

        return plugins

    def ListPluginsAsPluginDescriptions(self):

        plugins = list()

        for key in self.PluginDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == 'priv_names':
                name = self.PluginDb[key]
                desc = self.GetDescription(name)
                cmd = self.GetCommandLine(name)
                mod = self.GetModule(name)
                icon = self.GetIcon(name)
                plugins.append(PluginDescription(name = name, description = desc, command = cmd, module = mod, icon = icon))

        return plugins

    def GetDescription(self, name):

        namekey = self._get_priv_name(name)
        if not namekey:
            return None

        desc = None
        for key in self.PluginDb.keys():
            (section, option) = key.split(self.defaultSeparator)

            if section == 'priv_desc':
                if option == namekey:
                    desc = self.PluginDb[key]
                    break
            
        return desc

    def GetCommandLine(self, name, vars=None):

        namekey = self._get_priv_name(name)
        if not namekey:
            return None

        cmdStr = None
        for key in self.PluginDb.keys():
            (section, option) = key.split(self.defaultSeparator)

            if section == 'priv_cmds':
                if option == namekey:
                    cmdStr = self.PluginDb[key]
                    break

        if cmdStr:
            if vars:
                cmdStr = cmdStr % vars

        return cmdStr
    
    def GetModule(self, name):

        namekey = self._get_priv_name(name)
        if not namekey:
            return None

        mod = None
        for key in self.PluginDb.keys():
            (section, option) = key.split(self.defaultSeparator)

            if section == 'priv_modules':
                if option == namekey:
                    mod = self.PluginDb[key]
                    break
            
        return mod

    def GetIcon(self, name):

        namekey = self._get_priv_name(name)
        if not namekey:
            return None

        icon = None
        for key in self.PluginDb.keys():
            (section, option) = key.split(self.defaultSeparator)

            if section == 'priv_icons':
                if option == namekey:
                    icon = self.PluginDb[key]
                    break
            
        return icon

        
    
