#!/usr/bin/python

#-----------------------------------------------------------------------------
# Name:        MailcapSetup.py
# Purpose:     This script will take a new shared applications mime setting
#              and other relevant information and updates the specified
#              mailcap file. If no mailcap file is specified, it updates the
#              system wide mailcap file.
#
# Author:      Ti Leggett
# Copyright:   (c) 2002-2003
# License:     See COPYING.txt
# RCS-ID:      $Id: MailcapSetup.py,v 1.1 2003-05-16 21:00:53 leggett Exp $
#-----------------------------------------------------------------------------

import os
import os.path
import sys
import AccessGrid.Platform
import getopt

try:
    import win32api
except:
    pass

class Mailcap:
    def __init__(self):
        self.system = False
        self.mailcap = os.path.join(AccessGrid.Platform.GetUserConfigDir( ), "mailcap")
        self.mimetype = ""
        self.executable = ""
        self.description = ""
        self.nametemplate = ""
        self.file = ""
        self.uninstall = False
        self.update = False
        self.mimetypes = dict( )
        

    def is_root(self):
        if sys.platform == AccessGrid.Platform.WIN:
            return False
        else:
            if os.getuid( ) == 0:
                return True
            else:
                return False


    def usage(self):
        print "%s:" % (sys.argv[0])
        print "    -h|--help:                      print this message"
        print "    -s|--system:                    edit the system mailcap file"
        print "    -m|--mime-type <mime>:          specify mime-type"
        print "    -e|--executable <file>:         specify executable file"
        print "    -d|--description <description>: specify the description"
        print "    -n|--nametemplate <name>:       specify the name template"
        print "    --mailcap <file>:               edit the specified mailcap"
        print "    --uninstall:                    uninstall the specified mime type"
        print "       Must be used with either --mime-type" 
        print "    --update:                       update the specfied mime type"
        print "       Must be used with either --mime-type"


    def process_args(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hsmed", ["help", "system", "mailcap=", "mime-type=", "executable=", "description=", "nametemplate=", "uninstall", "update"])
        except getopt.GetoptError:
            self.usage( )
            sys.exit(2)

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                self.usage( )
                sys.exit(0)
            elif opt in ('-s', '--system'):
                if self.is_root( ):
                    self.system = True
                    self.mailcap = os.path.join(AccessGrid.Platform.GetSystemConfigDir( ), "mailcap")
                elif sys.platform == AccessGrid.Platform.WIN:
                    print "You must have adminstrative rights to edit the system mailcap file"
                    sys.exit(2)
                else:
                    print "You must be root to edit the system mailcap file"
                    sys.exit(2)
            elif opt in ('-m', '--mime-type'):
                self.mimetype = arg
            elif opt in ('-e', '--executable'):
                self.executable = arg
            elif opt in ('-d', '--description'):
                self.description = arg
            elif opt in ('-n', '--nametemplate'):
                self.nametemplate = arg
            elif opt == '--mailcap':
                self.mailcap = arg
            elif opt == '--uninstall':
                self.uninstall = True
            elif opt == '--update':
                self.update = True

        if not self.mimetype:
            print "You must provide a mimetype."
            print ""
            self.usage( )
            sys.exit(2)

        if self.update and self.uninstall:
            self.usage( )
            sys.exit(2)

        if self.update and not ( self.executable or self.description or self.nametemplate ):
            print "You must specify at least one of executable, description, or nametemplate to update"
            print ""
            self.usage( )
            sys.exit(2)

    def mailcap_exists(self):
        if os.path.isfile(self.mailcap):
            return True
        else:
            return False


    def load_mimetypes(self):
        if not self.mailcap_exists( ):
            return True
        mailcapfd = open(self.mailcap)
        mimeline = mailcapfd.readline( ).strip( )
        while mimeline:
            mimelist = mimeline.split( '; ' )
            self.mimetypes[mimelist[0]] = mimelist[1:]
            mimeline = mailcapfd.readline( ).strip( )
        mailcapfd.close( )
        return True


    def mimetype_exists(self):
        if self.mimetype in self.mimetypes.keys( ):
            return True
        else:
            return False


    def get_mimetype(self):
        if not self.mimetype_exists( ):
            return False
        if not self.executable:
            self.executable = self.mimetypes[self.mimetype][0]
        if not self.description:
            self.description = self.mimetypes[self.mimetype][1]
        if not self.nametemplate:
            self.nametemplate = self.mimetypes[self.mimetype][2]
        return True


    def add_mimetype(self):
        if not self.executable:
            print "You must specify an executable"
            return False
        if not self.description:
            print "You mist specify a description"
            return False
        if not self.nametemplate:
            print "You mist specify a name template"
            return False
        if not self.description.startswith("description="):
            self.description = "description=" + self.description
        if not self.nametemplate.startswith("nametemplate="):
            self.nametemplate = "nametemplate=" + self.nametemplate
        self.mimetypes[self.mimetype] = [self.executable, self.description, self.nametemplate]
        return True


    def del_mimetype(self):
        if self.mimetype_exists( ):
            self.mimetypes.__delitem__(self.mimetype)


    def write_mailcap(self):
        if self.mailcap_exists( ):
            if os.path.isfile(self.mailcap + ".bak"):
                os.unlink(self.mailcap + ".bak")
            os.rename(self.mailcap,self.mailcap + ".bak")

        mailcapfd = open(self.mailcap, "w")
        if not mailcapfd:
            print "Could not %s for writing." %(self.mailcap)
            return False
        for mimetype in self.mimetypes.keys( ):
            mailcapfd.write( mimetype + "; " +
                             self.mimetypes[mimetype][0] + "; " +
                             self.mimetypes[mimetype][1] + "; " +
                             self.mimetypes[mimetype][2] + "\n" )
        mailcapfd.close( )
        return True


    def run(self):
        self.load_mimetypes( )
        if self.uninstall:
            self.del_mimetype( )
            if not self.write_mailcap( ):
                sys.exit(2)
        elif self.update:
            self.get_mimetype( )
            self.del_mimetype( )
            if not self.add_mimetype( ):
                sys.exit(2)
            if not self.write_mailcap( ):
                sys.exit(2)
        else:
            if self.mimetype_exists( ):
                print "The mimetype %s already exists." % (self.mimetype)
                sys.exit(2)
            if not self.add_mimetype( ):
                sys.exit(2)
            if not self.write_mailcap( ):
                sys.exit(2)
            
        
if __name__ == "__main__":
    mailcap = Mailcap( )
    mailcap.process_args( )
    mailcap.run( )
    sys.exit(0)
