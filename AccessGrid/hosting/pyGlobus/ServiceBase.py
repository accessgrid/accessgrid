#-----------------------------------------------------------------------------
# Name:        ServiceBase.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ServiceBase.py,v 1.7 2003-04-28 18:05:43 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import re

class ServiceBase:

    def _bind_to_service(self, service_obj):
        """
        Binds this object to an underlying web service.
        """
        self._register_exports(service_obj)
        self._service_object = service_obj

    def _UnbindFromService(self):
        """
        Removes the binding of this object to the underlying web service.
        """
        self._UnregisterExports(self._service_object)
        self._service_object = None
        
    def GetHandle(self):
        """
        Return the url to the web service for this web service object.
        """
        return self._service_object.get_handle()

    def _register_exports(self, service_obj):
        """
        This method searches for methods that are supposed to be exported
        via the underlying web service object. It then registers them for
        exporting.
        """
        #
        # Walk our list of attributes looking for
        # methods with docstrings.
        #
        # Also look for method attributes containing that
        # information.
        #

        # print "Register exports for ", self

        export_regexp = re.compile("^\s+soap_export_as:\s*(\S+)\s*$",
                                   re.MULTILINE)
        cinfo_regexp =  re.compile("^\s+pass_connection_info:\s*(\S+)\s*$",
                                   re.MULTILINE)

        exported_methods = {}
        
        # collect items from superclasses
        superitems = []
        for super in self.__class__.__bases__:
           superitems = superitems + super.__dict__.items()
        
        for name, value in superitems + self.__class__.__dict__.items():
            if callable(value):
                method = getattr(self, name)
                dstr = value.__doc__

                #
                # Parse the docstring to find exports or pass_cinfo
                # information
                #
                if dstr is not None:
                    pass_cinfo = 0
                    cmatches = cinfo_regexp.findall(dstr)
                    for cmatch in cmatches:
                        try:
                            imatch = int(cmatch)
                            pass_cinfo = imatch
                        except ValueError:
                            if cmatch.lower() == "true"  or cmatch.lower() == 't':
                                pass_cinfo = 1
                            else:
                                pass_cinfo = 0
                    matches = export_regexp.findall(dstr)
                    for export in matches:
                        # print "Export %s as %s %s" % (value, export, method)
                        exported_methods[name] = (method, export, pass_cinfo)

                #
                # Inspect the method attributes.
                #

                if hasattr(method, 'soap_export_as'):
                    export_name = method.soap_export_as
                    pass_cinfo = 0
                    if hasattr(method, 'pass_connection_info'):
                        pass_cinfo = method.pass_connection_info
                    exported_methods[name] = (method, export_name, pass_cinfo)

            for method, export_name, pass_cinfo in exported_methods.values():
                service_obj.register_function(method, export_name, pass_cinfo)

        # We keep the names for later unregistering them :-)
        self.exportedMethodNames = map( lambda thing:
                                        thing[0].__name__,
                                        exported_methods.values() )
        
    def _UnregisterExports(self, service_obj):
        """
        This method unregisters the web service methods from the server,
        this makes them unavailable to outside callers and allows python
        garbage collection to properly cleanup.
        """

        for method in self.exportedMethodNames:
            self._service_object.UnregisterFunction(method)

    #
    # Mappings to other function naming style.
    #

    get_handle = GetHandle
