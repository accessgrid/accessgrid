import re

class ServiceBase:

    def _bind_to_service(self, service_obj):
        self._register_exports(service_obj)
        self._service_object = service_obj

    def get_handle(self):
        return self._service_object.get_handle()

    def bind_to_registry(self, classad, registry_url, frequency):
        return self._service_object.bind_to_registry(classad, registry_url, frequency)

    def bind_to_local_registry(self, class_ad, registry_obj, registry_url):
        return self._service_object.bind_to_local_registry(class_ad, registry_obj, registry_url)
    
    def unbind_from_registry(self, registry_url):
        return self._service_object.unbind_from_registry(registry_url)

    def _register_exports(self, service_obj):

        #
        # Walk our list of attributes looking for
        # methods with docstrings
        #

        # print "Register exports for ", self

        export_regexp = re.compile("^\s+xmlrpc_export_as:\s*(\S+)\s*$", re.MULTILINE)
        cinfo_regexp =  re.compile("^\s+pass_connection_info:\s*(\S+)\s*$", re.MULTILINE)

        for name, value in self.__class__.__dict__.items():
            if callable(value):
                dstr = value.__doc__
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
                        method = getattr(self, name)
                        # print "Export %s as %s %s" % (value, export, method)

                        service_obj.register_function(method, export, pass_cinfo)
        
