import re

class ServiceBase:

    def _bind_to_service(self, service_obj):
        self._register_exports(service_obj)
        self._service_object = service_obj

    def get_handle(self):
        return self._service_object.get_handle()

    def _register_exports(self, service_obj):

        #
        # Walk our list of attributes looking for
        # methods with docstrings.
        #
        # Also look for method attributes containing that
        # information.
        #

        # print "Register exports for ", self

        export_regexp = re.compile("^\s+soap_export_as:\s*(\S+)\s*$", re.MULTILINE)
        cinfo_regexp =  re.compile("^\s+pass_connection_info:\s*(\S+)\s*$", re.MULTILINE)

        exported_methods = {}
        
        for name, value in self.__class__.__dict__.items():
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