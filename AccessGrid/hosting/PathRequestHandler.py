import BaseHTTPServer

class SOAPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def version_string(self):
        return '<a href="http://www.actzero.com/solution.html">' + \
            'SOAP.py ' + __version__ + '</a> (Python ' + \
            sys.version.split()[0] + ')'

    def date_time_string(self):
        self.__last_date_time_string = \
            BaseHTTPServer.BaseHTTPRequestHandler.\
            date_time_string(self)

        return self.__last_date_time_string

    def do_POST(self):
        try:
            if self.server.config.dumpHeadersIn:
                s = 'Incoming HTTP headers'
                debugHeader(s)
                print self.raw_requestline.strip()
                print "\n".join(map (lambda x: x.strip(),
                    self.headers.headers))
                debugFooter(s)

            data = self.rfile.read(int(self.headers["content-length"]))

            if self.server.config.dumpSOAPIn:
                s = 'Incoming SOAP'
                debugHeader(s)
                print "PATH is ", self.path
                print data,
                if data[-1] != '\n':
                    print
                debugFooter(s)

            (r, header, body, attrs) = \
                parseSOAPRPC(data, header = 1, body = 1, attrs = 1)

            method = r._name
            args   = r._aslist
            kw     = r._asdict

            ns = r._ns
            resp = ""
            # For fault messages
            if ns:
                nsmethod = "%s:%s" % (ns, method)
            else:
                nsmethod = method

            try:
                # First look for registered functions
                if self.server.funcmap.has_key(ns) and \
                    self.server.funcmap[ns].has_key(method):
                    f = self.server.funcmap[ns][method]
                elif self.server.pathmap.has_key(ns):
                    #
                    # Server has a pathmap for this namespace.
                    # Dispatch through the pathmap.
                    #

                    f = self.server.pathmap[ns].lookup_path(method, self.path)

                else: # Now look at registered objects
                    # Check for nested attributes. This works even if
                    # there are none, because the split will return
                    # [method]
                    f = self.server.objmap[ns]
                    l = method.split(".")
                    for i in l:
                        f = getattr(f, i)
            except:
                resp = buildSOAP(faultType("%s:Client" % NS.ENV_T,
                        "No method %s found" % nsmethod,
                        "%s %s" % tuple(sys.exc_info()[0:2])),
                    encoding = self.server.encoding,
                    config = self.server.config)
                status = 500
            else:
                try:
                    if header:
                        x = HeaderHandler(header, attrs)

                    # If it's wrapped, some special action may be needed

                    if isinstance(f, MethodSig):
                        c = None
                        if f.context:  # Build context object
                            c = SOAPContext(header, body, attrs, data,
                                self.connection, self.headers,
                                self.headers["soapaction"],
                                self.server.delegated_cred)

                        if f.keywords:
                            # This is lame, but have to de-unicode
                            # keywords

                            strkw = {}

                            for (k, v) in kw.items():
                                strkw[str(k)] = v
                            if c:
                                strkw["_SOAPContext"] = c
                            fr = apply(f, (), strkw)
                        elif c:
                            fr = apply(f, args, {'_SOAPContext':c})
                        else:
                            fr = apply(f, args, {})
                    else:
                        fr = apply(f, args, {})

                    if type(fr) == type(self) and \
                        isinstance(fr, voidType):
                        resp = buildSOAP(kw = {'%sResponse' % method: fr},
                            encoding = self.server.encoding,
                            config = self.server.config)
                    else:
                        resp = buildSOAP(kw =
                            {'%sResponse' % method: {'Result': fr}},
                            encoding = self.server.encoding,
                            config = self.server.config)
                except Exception, e:
                    import traceback
                    info = sys.exc_info()

                    if self.server.config.dumpFaultInfo:
                        s = 'Method %s exception' % nsmethod
                        debugHeader(s)
                        traceback.print_exception(info[0], info[1],
                            info[2])
                        debugFooter(s)

                    if isinstance(e, faultType):
                        f = e
                    else:
                        f = faultType("%s:Server" % NS.ENV_T,
                           "Method %s failed." % nsmethod)

                    if self.server.config.returnFaultInfo:
                        f._setDetail("".join(traceback.format_exception(
                                info[0], info[1], info[2])))
                    elif not hasattr(f, 'detail'):
                        f._setDetail("%s %s" % (info[0], info[1]))

                    resp = buildSOAP(f, encoding = self.server.encoding,
                       config = self.server.config)
                    status = 500
                else:
                    status = 200
        except faultType, e:
            import traceback
            info = sys.exc_info()

            if self.server.config.dumpFaultInfo:
                s = 'Received fault exception'
                debugHeader(s)
                traceback.print_exception(info[0], info[1],
                    info[2])
                debugFooter(s)

            if self.server.config.returnFaultInfo:
                e._setDetail("".join(traceback.format_exception(
                        info[0], info[1], info[2])))
            elif not hasattr(e, 'detail'):
                e._setDetail("%s %s" % (info[0], info[1]))

            resp = buildSOAP(e, encoding = self.server.encoding,
                config = self.server.config)
            status = 500
        except:
            # internal error, report as HTTP server error
            if self.server.config.dumpFaultInfo:
                import traceback
                s = 'Internal exception'
                debugHeader(s)
                traceback.print_exc ()
                debugFooter(s)
            self.send_response(500)
            self.end_headers()

            if self.server.config.dumpHeadersOut and \
                self.request_version != 'HTTP/0.9':
                s = 'Outgoing HTTP headers'
                debugHeader(s)
                if self.responses.has_key(status):
                    s = ' ' + self.responses[status][0]
                else:
                    s = ''
                print "%s %d%s" % (self.protocol_version, 500, s)
                print "Server:", self.version_string()
                print "Date:", self.__last_date_time_string
                debugFooter(s)
        else:
            # got a valid SOAP response
            self.send_response(status)

            t = 'text/xml';
            if self.server.encoding != None:
                t += '; charset="%s"' % self.server.encoding
            self.send_header("Content-type", t)
            self.send_header("Content-length", str(len(resp)))
            self.end_headers()

            if self.server.config.dumpHeadersOut and \
                self.request_version != 'HTTP/0.9':
                s = 'Outgoing HTTP headers'
                debugHeader(s)
                if self.responses.has_key(status):
                    s = ' ' + self.responses[status][0]
                else:
                    s = ''
                print "%s %d%s" % (self.protocol_version, status, s)
                print "Server:", self.version_string()
                print "Date:", self.__last_date_time_string
                print "Content-type:", t
                print "Content-length:", len(resp)
                debugFooter(s)

            if self.server.config.dumpSOAPOut:
                s = 'Outgoing SOAP'
                debugHeader(s)
                print resp,
                if resp[-1] != '\n':
                    print
                debugFooter(s)

            self.wfile.write(resp)
            self.wfile.flush()

            # We should be able to shut down both a regular and an SSL
            # connection, but under Python 2.1, calling shutdown on an
            # SSL connections drops the output, so this work-around.
            # This should be investigated more someday.

            if self.server.config.SSLserver and \
                isinstance(self.connection, SSL.Connection):
                self.connection.set_shutdown(SSL.SSL_SENT_SHUTDOWN |
                    SSL.SSL_RECEIVED_SHUTDOWN)
            else:
                self.connection.shutdown(1)

    def log_message(self, format, *args):
        if self.server.log:
            SOAPServer.BaseHTTPServer.BaseHTTPRequestHandler.\
                log_message (self, format, *args)

