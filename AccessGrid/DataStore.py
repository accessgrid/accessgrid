#-----------------------------------------------------------------------------
# Name:        DataStore.py
# Purpose:     This is a data storage server.
#
# Author:      Robert Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: DataStore.py,v 1.8 2003-03-12 08:43:33 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os.path
import threading
import re
import urllib
import urlparse
import httplib
import string
import shutil
import sys
import socket
import md5
import os
import ConfigParser
import cStringIO
import Queue

import AccessGrid.GUID
from AccessGrid.Utilities import GetHostname
from AccessGrid.Descriptions import DataDescription
from AccessGrid import Platform

import logging
log = logging.getLogger("AG.DataStore")

class NotAPlainFile(Exception):
    pass

class DuplicateFile(Exception):
    pass

class FileNotFound(Exception):
    pass

class NotAuthorized(Exception):
    pass

class UploadFailed(Exception):
    pass

class DownloadFailed(Exception):
    pass

class DataStore:
    """
    A DataStore implements a per-venue data storage server.
    
    """
    
    def __init__(self, venue, pathname, prefix):
        """
        Create the datastore.

        Files will be stored in the directory named by <pathname>.
        The URL prefix for this data store is <prefix>.

        """

        self.venue = venue
        
        if not os.path.exists(pathname):
            raise Exception("Datastore path %s does not exist" % (pathname))

        self.pathname = pathname
        self.prefix = prefix

    def SetTransferEngine(self, engine):
        """
        Set the datastore's default transfer engine.

        """

        self.transfer_engine = engine
        engine.RegisterPrefix(self.prefix, self)

    def GetUploadDescriptor(self):
        """
        Return the upload descriptor for this datastore.

        """

        return self.transfer_engine.GetUploadDescriptor(self.prefix)

    def GetDownloadDescriptor(self, filename):
        """
        Return the download descriptor for filename.

        If filename is not present in the datastore, return None.

        """

        path = os.path.join(self.pathname, filename)

        if not os.path.exists(path):
            return None
        
        return self.transfer_engine.GetDownloadDescriptor(self.prefix, filename)
    

    def GetDownloadFilename(self, id_token, url_path):
        """
        Return the full path of the given filename in this datastore.

        Used by the transfer engine to find a requested file.
        This method must perform an authorization check on dn, the
        distinguished name of the client requesting the file. If this fails,
        raise a NotAuthorized exception. If the file does not exist,
        raise a FileNotFound exception.

        """

        # print "OpenFile: dn=%s filename=%s" % (dn, filename)

        #
        # Authorization check for dn goes here
        #

        path = os.path.join(self.pathname, url_path)

        if not os.path.isfile(path):
            raise FileNotFound

        return path

    def CanUploadFile(self, dn, file_info):
        """
        Used by the transfer engine to determine if a client is able to
        upload a new file.

        Arguments:
         - dn is the distinguished name of the client
         - file_info is a file information dict for hte file the client is trying to upload

        Current test is just to see if the file exists.
        Need to test to see if the client is currently logged into the venue.
        """

        filename = file_info['name']
        desc = self.venue.GetData(filename)

        if desc is  None or desc == "":
            return 1

        return 0

    def GetUploadFilename(self, dn, file_info):
        """
        Return the filename for a file to be uploaded.

        file_info is a file information dictionary.

        The client is running with identity "dn".

        This is used by the transfer engine to provide a
        destination for a file upload.

        """

        #
        # First verify that we have a state=pending description in the venue.
        #

        filename = file_info['name']
        desc = self.venue.GetData(filename)
        
        if desc is None:
            print "Venue data for %s not present" % (filename)
            return None

        if desc.GetStatus() != DataDescription.STATUS_PENDING:
            print "Invalid status in GetUploadFileHandle()"
            return None

        #
        # Okay, we should be cool. Open up the file for creation.
        # (Ignoring whether the file is there or not - the metadata
        # assures us we have the right to do so).
        #

        path = os.path.join(self.pathname, filename)

        return path

    def CompleteUpload(self, dn, file_info):
        """
        The upload is done. Get the data description, update with the
        information from the file_info dict (which contains the information
        from the manifest).
        """

        desc = self.venue.GetData(file_info['name'])
        # print "CompleteUpload: got desc ", desc, desc.__dict__
        desc.SetChecksum(file_info['checksum'])
        desc.SetSize(file_info['size'])
        desc.SetStatus(DataDescription.STATUS_PRESENT)
        desc.SetOwner(dn)
        desc.SetURI(self.GetDownloadDescriptor(file_info['name']))
        print "CompleteUpload: updating with ", desc, desc.__dict__
        self.venue.UpdateData(desc)

    def DeleteFile(self, filename):
        """
        Delete filename from the datastore.

        """

        print "DeleteFile: ", filename
        path = os.path.join(self.pathname, filename)
        if not os.path.exists(path):
            raise FileNotFound(filename)

        try:
            os.remove(path)
        except OSError, e:
            print "DeleteFile raised error ", e

    def AddPendingUpload(self, dn, filename):
        """
        Create a data description for filename with a state of "pending" and
        add to the venue.

        """

        desc = DataDescription(filename)
        desc.SetStatus(DataDescription.STATUS_PENDING)
        desc.SetOwner(dn)
        
        self.venue.AddData(desc)

        return desc

import BaseHTTPServer

class HTTPTransferHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):

        #
        # Retrieve an identity token from the TransferServer. 
        # We pass the transfer handler through so that the
        # protocol-specific code in TransferServer can have access
        # to the connection-specific information in the handler
        # instance.
        #

        identityToken = self.server.GetIdentityToken(self)
        print "GET identity token ", identityToken
        
        try:
            self.ProcessGet(identityToken)

        except FileNotFound:
            self.send_error(404, "File not found")

        except NotAuthorized:
            self.send_error(403, "Not authorized")

    def do_POST(self):
        #
        # Retrieve an identity token from the TransferServer. 
        # We pass the transfer handler through so that the
        # protocol-specific code in TransferServer can have access
        # to the connection-specific information in the handler
        # instance.
        #

        identityToken = self.server.GetIdentityToken(self)
        # log.debug("POST identity token %s", identityToken)
        
        #
        # Split path into components, and verify
        # that it started with /. (path_parts[0] is
        # empty if that is the case).
        #

        # log.debug("doPOST path=%s", self.path)

        path_parts = self.path.split('/')
        if path_parts[0] != '':
            self.send_error(404, "File not found")
            return None

        #
        # This is always empty, so nuke it.
        #

        del path_parts[0]

        #
        # Check for /<prefix>/manifest
        #
        if len(path_parts) == 2 and path_parts[1] == "manifest":
            return self.ProcessManifest(path_parts[0], identityToken)

        #
        # Check for /<prefix>/<transfer_key>/<file_num>, designating a file upload.
        #

        if len(path_parts) == 3:
            prefix = path_parts[0]
            transfer_key = path_parts[1]
            file_num = path_parts[2]

            #
            # Ensure file_num is numeric
            #

            if not re.search("^\d+$", file_num):
                self.send_error(404, "File not found")
                return None

            #
            # This might be right. Pass control off
            # to the method that handles the details of
            # file uploads.
            
            return self.ProcessFileUpload(identityToken, prefix, transfer_key, file_num)
            
        #
        # Default.
        #
        self.send_error(404, "File not found")
        return None

    def ProcessFileUpload(self, identityToken, prefix, transfer_key, file_num):
        """
        Process a possible file upload.

        Look up the prefix to get the handler for that prefix.

        Look up the transfer key in the server to get the
        manifest.

        Look in the manifest for the metadata about the file.

        Do some preliminary checks (see if the Content-Length
        matches the size in the manifest, etc).

        Create a local file in the right location for the download.

        Copy the data from the socket into the file location, collecting
        a md5 checksum along the way.

        Verify the checksum, and nuke the file if it's wrong.
        """


        #
        # Find the transfer handler for this prefix.
        #
        transfer_handler = self.server.LookupPrefix(prefix)
        if transfer_handler is None:
            self.send_error(404, "Path not found")
            return None

        #
        # Find the manifest information for this file.
        #

        file_info = self.server.LookupUploadInformation(transfer_key, file_num)
        print "Got this for %s: %s" % (file_num, file_info)

        #
        # Verify the filesize is what we expect
        #

        size = int(file_info['size'])
        content_len = int(self.headers['Content-Length'])
        if size != content_len:
            self.send_error(405, "Size in manifest != size in Content-Length")
            return None

        #
        # Query the handler for the pathname we shoudl use
        # to upload the file.
        #

        upload_file_path = transfer_handler.GetUploadFilename(identityToken, file_info)
        if upload_file_path is None:
            self.send_error(404, "Upload file not found")
            return None

        #
        # See if we have enough disk space for this. Put a 5% fudge factor on the space
        # available so we won't consume all.
        #

        try:
            upload_dir = os.path.dirname(upload_file_path)
            bytesFree = Platform.GetFilesystemFreeSpace(upload_dir)
            # bytesFree = 10
            if bytesFree is None:
                log.debug("Cannot determine free space for %s", upload_Dir)
            else:
                if size > (0.95 * bytesFree):
                    log.info("Upload failing: not enough disk space. Free=%d needed=%d",
                             bytesFree, size)
                    self.send_error(405, "Not enough disk space for upload")
                    return None
                else:
                    log.debug("Allowing upload. Free spae=%d needed=%d",
                             bytesFree, size)
        except:
            log.exception("Platform.GetFilesystemFreeSpace threw exception")
            
        

        #
        # Open up destination file and initialize digest.
        #

        filename = file_info['name']
        fp = None

        try:
            # log.debug("opening upload file %s", upload_file_path)
            fp = open(upload_file_path, "wb")
        except EnvironmentError:
            # log.exception("Cannot open output file")
            self.send_error(405, "Cannot open output file")
            return None

        if fp is None:
            #
            # Wups, something bad happened.
            #

            print "Could not get upload filehandle for ", filename
            self.send_error(400, "Could not get upload filehandle for %s" % (filename))
            return None

        digest = md5.new()

        #
        # Start the transfer. We need to read exactly size bytes.
        #

        try:

            left = int(size)
            bufsize = 4096
            while left > 0:
                if left < 4096:
                    n = left
                else:
                    n = 4096

                buf = self.rfile.read(n)

                left -= len(buf)

                if buf == "":
                    break

                digest.update(buf)
                fp.write(buf)

                if left == 0:
                    break;
            fp.close()
            
        except EnvironmentError, e:
            print "Hm, got an exception on upload"
            self.send_error(400, "Error on upload: %s" % (str(e)))
            fp.close()
            return None


        #
        # Transfer done.
        # Compute the checksum and test against what was
        # advertised in the manifest.
        #

        checksum = digest.hexdigest()
        if checksum == file_info['checksum']:
            #
            # We got the file fine. Declare success.
            #
            # print "Checksms match!"

            self.send_response(200, "File transfer OK")
            self.end_headers()

        else:
            #
            # Something happened in the upload.
            #
            # Delete the file we created (TODO: figure out a clean
            # way to do this; we're not doing it at the moement)
            # and report an error.
            #
            
            self.send_error(405, "Checksum mismatch on upload")
            
        #
        # OKAY, we handled the upload properly.
        # Let the transfer handler know things are cool.
        #
        
        transfer_handler.CompleteUpload(identityToken, file_info)

    def ProcessManifest(self, prefix, identityToken):
        """
        Read the manifest from the input.

        We can't just let the ConfigParser read as it will read until EOF,
        and the server is leaving the socket open so it can write the
        transfer key back. So we need to obey the Content-Length header, reading
        that many bytes, stuff them into a StringIO, and pass that to the
        ConfigParser to parse.
        """

        #
        # First get the transfer handler for this prefix.
        #

        transfer_handler = self.server.LookupPrefix(prefix)
        if transfer_handler is None:
            self.send_error(404, "Path not found")
            return None

        #
        # Woo, the int cast is important, as the header comes back
        # as a string and self.rfile.read() complains bitterly if it
        # gets a string as an argument.
        #
        
        read_len = int(self.headers['Content-Length'])
        buf = self.rfile.read(read_len)

        #
        # Construct the StringIO and read the manifest from it.
        #

        io = cStringIO.StringIO(buf)
    
        manifest = ConfigParser.ConfigParser()

        #
        # Upload status variables.
        #
        upload_okay = 1
        upload_error_list = []

        #
        # List of files to be uploaded; cache them
        # here so we don't have to run throught the manifest multiple times.
        #
        file_list = []

        #
        # We've created a ConfigParser object for the manifest.
        # All actions touching this manifest are in a
        # try block so that if there are *any* problems
        # with the manifest the transfer is aborted as failing.
        #
        try:
            manifest.readfp(io)
            print "have manifest"
            print manifest.sections()
            manifest.write(sys.stdout)

            #
            # Go through the potential files to be uploaded and ensure
            # that the datastore will be able to store them.
            #

            num_files = manifest.getint("manifest", "num_files")

            for file_num in range(0, num_files):

                info = {}
                for opt in manifest.options(str(file_num)):
                    info[opt] = manifest.get(str(file_num), opt)
                
                name = info['name']
                if not transfer_handler.CanUploadFile(identityToken, info):
                    upload_okay = 0
                    upload_error_list.append("Upload error for file " + name)
                file_list.append(name)


        except ValueError, e:
            print "ConfigParser error: ", str(e)
            self.send_error(400, "ConfigParser error: " + str(e))
            return None

        except ConfigParser.Error, e:
            print "ConfigParser error: ", str(e)
            self.send_error(400, "ConfigParser error: " + str(e))
            return None

        #
        # Okay, since we got here okay the basic form of the request
        # was fine, so we can return a 200 for the POST itself.
        #

        self.send_response(200)
        self.send_header("Content-type", "text/plain")

        #
        # If all files can be transferred, go ahead and register
        # the manifest with the server, and request the file slots in the
        # datastore (they'll get marked as "pending").
        #
        
        #
        # Collect the response  into a string so we can
        # issue a Content-length header. The GSIHTTP code
        # appears to be happier with that, and it's good
        # practice anyway.
        #
        output = ""
        
        if upload_okay:
            transfer_key = self.server.RegisterManifest(manifest)

            for file in file_list:
                transfer_handler.AddPendingUpload(identityToken, file)

            output += "return_code: 0\n"
            output += "transfer_key: %s\n" % (transfer_key)

        else:
            output += "return_code: 1\n"
            for err in upload_error_list:
                output += "error_reason: %s\n" % (err)

        self.send_header("Content-length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)
        return None

    def ProcessGet(self, identityToken):
        """
        Handle an HTTP GET.

        Extract the name of the file from the path; the path should be
        of the format /<prefix>/<filename>. Any other path is incorrect and
        will cause a FileNotFound exception to be raised.

        Call the datastore's OpenFile method to open the file and
        return a python file handle to it. This method can return FileNotFound
        and NotAuthorized exceptions; return an appropriate error code for each.
        """

        path = urllib.unquote(self.path)

        components = path.split('/')

        #
        # This is always empty, so nuke it.
        #

        del components[0]
        
        if len(components) != 2:
            raise FileNotFound

        prefix = components[0]
        path = components[1]

        # log.info("Have path '%s', prefix='%s'", path, prefix)

        #
        # First get the transfer handler for this prefix.
        #

        transfer_handler = self.server.LookupPrefix(prefix)
        if transfer_handler is None:
            self.send_error(404, "Path not found")
            return None

        fp = None
        try:
            ds_path = transfer_handler.GetDownloadFilename(identityToken, path)
            if ds_path is None:
                raise FileNotFound(path)
            fp = open(ds_path, "rb")
        except FileNotFound, e:
            raise e
        except NotAuthorized, e:
            raise e
        except IOError:
            raise FileNotFound(path)

        #
        # Successfully opened the file to be transferred.
        # Write it to the output
        #
        if fp is not None:

            #
            # Figure out how big it is.
            #
            stat = os.stat(ds_path)
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Length", stat.st_size)
            self.end_headers()
            # print "Start copy to output"
            shutil.copyfileobj(fp, self.wfile)
            print "Done copying"
            fp.close()

class TransferServer:
    """
    A TransferServer provides file upload and download services.

    It is intended to be subclassed to produce a protocol-specific
    transfer engine. This class handles the connection to the data store itself,
    and the manipulation of manifests.

    The transfer server provides services based on URL prefixes. That is,
    a client (um, a client in the same process as this object that is using
    its services to provide file upload and download capabilities) of the
    transfer server will register its interest in upload and downloads for some
    URL prefix. Access to files under that prefix is gated through the
    registered object.

    A local client registers a callback handler with the TransferServer. This handler
    will be invoked in the following situations:

    When a HTTP GET request occurs to initiate a file download, the handler's
    GetDownloadFilename(id_token, url_path) is invoked, and expects to be returned a
    pathname to the file on the local filesystem. The url_path does not include the
    client's transfer prefix. id_token is an identifier token representing the
    identity of the downloading client.

    When a HTTP POST request occurs with a transfer manifest, the manifest is
    parsed. For each file, the handler's CanUpload(id_token, file_info) 
    callback is invoked.  The callback is to determine whether it can accept the upload
    of the file and return 1 if the server will accept the file, 0 otherwise. id_token is an
    identifier token representing the identity of the uploading client.

    file_info is a dictionary with the following keys:
    
    	name		Desired name of the file
        size		Size of the file in bytes
        checksum	MD5 checksum of the file

    If the manifest processing indicates that the file upload can continue,
    the transfer handler's AddPendingUpload(id_token, filename) method is invoked.

    When a HTTP POST request occurs with an actual file upload, the handler's
    GetUploadFilename(id_token, file_info) method is invoked. The handler validates
    the request and returns the pathname to which the file should be uploaded. id_token is an
    identifier token representing the identity of the uploading client.

    When the file upload is completed, the handler's CompleteUpload(id_token, file_info)
    method is invoked.  

    """

    def __init__(self):

        #
        # upload_manifests is a dictionary mapping from transfer key
        # to the manifest for that transfer.
        #
        self.upload_manifests = {}

        #
        # The prefix_registry maps from a transfer prefix to
        # the handler for that prefix.
        #
        
        self.prefix_registry = {}

    def RegisterPrefix(self, prefix, handler):
        self.prefix_registry[prefix] = handler

    def LookupPrefix(self, prefix):
        if self.prefix_registry.has_key(prefix):
            return self.prefix_registry[prefix]
        else:
            return None
        
    def GetUploadDescriptor(self, prefix):
        """
        Return the upload descriptor for this transfer server.

        Must be implemented by the protocol-specific subclass.
        """
        
        raise NotImplementedError
                                 
    def GetDownloadDescriptor(self, prefix, path):
        """
        Return the download descriptor for this transfer server.

        Must be implemented by the protocol-specific subclass.
        """
        
        raise NotImplementedError

    def RegisterManifest(self, manifest):
        """
        A client has sent a POST to /<prefix>/manifest to initiate an upload.
        Manifest is the manifest that was transferred.

        Allocate a transfer key for this upload, save the manifest under
        that key, and return the key to the caller.

        """

        transfer_key = str(AccessGrid.GUID.GUID())

        #
        # GUIDs better be unique.
        #
        assert not self.upload_manifests.has_key(transfer_key)

        self.upload_manifests[transfer_key] = manifest
        return transfer_key

    def LookupUploadInformation(self, transfer_key, file_num):
        """
        Look up the information for transfer_key and file_num in the manifest.

        Raise a FileNotFound exception if it isn't there.

        Returns the list of attribute information for that file.

        """

        if not self.upload_manifests.has_key(transfer_key):
            raise FileNotFound

        manifest = self.upload_manifests[transfer_key]

        num_files = manifest.getint("manifest", "num_files")
        if int(file_num) < 0 or int(file_num) >= num_files:
            print "invalid file_num '%s'" % (file_num)
            print "Have manifest: "
            manifest.write(sys.stdout)
            raise FileNotFound

        file_num = str(file_num)

        if not manifest.has_section(file_num):
            print "section not found for ", file_num
            raise FileNotFound

        info = {}
        for opt in  manifest.options(file_num):
            info[opt] = manifest.get(file_num, opt)
        return info

class IdentityToken:
    def __init__(self, dn):
        self.dn = dn

    def __repr__(self):
        cname = self.__class__.__name__
        return "%s(dn=%s)" % (cname, self.dn)

class HTTPIdentityToken(IdentityToken):
    pass

class GSIHTTPIdentityToken(IdentityToken):
    pass

class HTTPTransferServer(BaseHTTPServer.HTTPServer, TransferServer):
    """
    A HTTPTransferServer is a HTTP-based implementation of a TransferServer.

    Note that most of the work is done in HTTPTransferHandler.
    """

    def __init__(self, address = ('', 0)):
        TransferServer.__init__(self)
        BaseHTTPServer.HTTPServer.__init__(self, address, HTTPTransferHandler)

    def GetIdentityToken(self, transferHandler):
        """
        Create an identity token for this HTTP-based transfer.

        The token will contain the X-Client-DN header if there is one.
        """

        try:
            dn = transferHandler.headers.getheader("X-Client-DN")
        except KeyError:
             dn = None

        return HTTPIdentityToken(dn)
        

    def GetUploadDescriptor(self, prefix):
        return urlparse.urlunparse(("http",
                                 "%s:%d" % (GetHostname(), self.socket.getsockname()[1]),
                                 prefix,    # Path
                                 "", "", ""))
                                 
    def GetDownloadDescriptor(self, prefix, path):
        return urlparse.urlunparse(("http",
                                    "%s:%d" % (GetHostname(), self.socket.getsockname()[1]),
                                    "%s/%s" % (prefix, urllib.quote(path)),
                                    "", "", ""))
                                 
    def run(self):
        self.done = 0
        self.server_thread = threading.Thread(target = self.thread_run,
                                              name = 'TransferServer')
        self.server_thread.start()

    def stop(self):
        self.done = 1

    def thread_run(self):
        """
        thread_run is the server thread's main function.
        """

        while not self.done:
            self.handle_request()

from pyGlobus import io
from AccessGrid.hosting.pyGlobus import Utilities

class GSIHTTPTransferServer(io.GSITCPSocketServer, TransferServer):
    """
    A GSIHTTPTransferServer is a Globus-enabled HTTP-based implementation of a TransferServer.
n
    Note that most of the work is done in HTTPTransferHandler.

    This implementation uses a pool of worker threads to handle the requests.
    We could just use SocketServer.ThreadingMixIn, but I worry about 
    an unbounded number of incoming request overloading the server.

    self.requestQueue is a Queue object. Each worker thread runs __WorkerRun(),
    which blocks on a get on teh request queue.

    Incoming requests are just placed on the queue.
    """

    def __init__(self, address = ('', 0), numThreads = 5):
        TransferServer.__init__(self)

        self.done = 0
        
        self.numThreads = numThreads
        self.requestQueue = Queue.Queue()
        self._CreateWorkers()

        #
        # For now, allow all connections.
        #

        def auth_cb(server, g_handle, remote_user, context):
            # print "Got remote ", remote_user
            return 1
        # tcpAttr = Utilities.CreateTCPAttrAlwaysAuth()
        tcpAttr = Utilities.CreateTCPAttrCallbackAuth(auth_cb)
        io.GSITCPSocketServer.__init__(self, address, HTTPTransferHandler,
                                    None, None, tcpAttr = tcpAttr)

    def _CreateWorkers(self):
        self.workerThread = {}
        for workerNum in range(self.numThreads):
            self.workerThread[workerNum] = threading.Thread(target = self.__WorkerRun,
                                                            name = 'TransferWorker',
                                                            args = (workerNum,))
            self.workerThread[workerNum].start()

    def __WorkerRun(self, workerNum):
        # log.debug("Worker %d starting", workerNum)

        while not self.done:
            cmd = self.requestQueue.get(1)
            # log.debug("Worker %d gets cmd %s", workerNum, cmd)
            cmdType = cmd[0]
            if cmdType == "quit":
                break
            elif cmdType == "request":
                request = cmd[1]
                client_address = cmd[2]

                try:
                    self.finish_request(request, client_address)
                    self.close_request(request)
                except:
                    info.exception("Worker %d: Request handling threw exception", workerNum)
        # log.debug("Worker %d exiting", workerNum)
            

    def process_request(self, request, client_address):
        # log.debug("process_request: request=%s client_address=%s", request, client_address)
        self.requestQueue.put(("request", request, client_address))

    def GetIdentityToken(self, transferHandler):
        """
        Create an identity token for this GSIHTTP-based transfer.

        It contains the DN from the connection's security context.
        """

        context = transferHandler.connection.get_security_context()
        initiator, acceptor, valid_time, mechanism_oid, flags, local_flag, open_flag = context.inquire()
        dn = initiator.display()

        return GSIHTTPIdentityToken(dn)
        
    def _GetListenPort(self):
        return self.port

    def GetUploadDescriptor(self, prefix):
        return urlparse.urlunparse(("https",
                                 "%s:%d" % (GetHostname(), self._GetListenPort()),
                                 prefix,
                                 "", "", ""))
                                 
    def GetDownloadDescriptor(self, prefix, path):
        return urlparse.urlunparse(("https",
                                    "%s:%d" % (GetHostname(), self._GetListenPort()),
                                    "%s/%s" % (prefix, urllib.quote(path)),
                                    "", "", ""))
                                 
    def run(self):
        self.done = 0
        self.server_thread = threading.Thread(target = self.thread_run,
                                              name = 'TransferServer')
        self.server_thread.start()

    def stop(self):
        self.done = 1
        for workerNum in range(self.numThreads):
            self.requestQueue.put("quit",)

    def thread_run(self):
        """
        thread_run is the server thread's main function.
        """

        while not self.done:
            self.handle_request()

def HTTPDownloadFile(identity, download_url, destination, size, checksum,
                     progressCB = None):
    return HTTPFamilyDownloadFile(download_url, destination, size, checksum,
                                  identity, progressCB)

def GSIHTTPDownloadFile(download_url, destination, size, checksum,
                        progressCB = None):
    """
    Download a file with GSI HTTP.

    Define a local connection class so we can poke about at the
    tcp attributes here.
    """
    
    def GSIConnectionClass(host):
        tcpAttr = Utilities.CreateTCPAttrAlwaysAuth()
        return io.GSIHTTPConnection(host, tcpAttr = tcpAttr)

    return HTTPFamilyDownloadFile(download_url, destination, size, checksum,
                                  None, progressCB, GSIConnectionClass)
                                  
def HTTPFamilyDownloadFile(download_url, destination, size, checksum,
                           identity = None,
                           progressCB = None,
                           connectionClass = httplib.HTTPConnection):
    """
    Download the given url, as user identified by identity,
    and place the new file in destination. 

    We assume the caller has determined that overwriting destination
    is valid, so we do not check for its existence.

    progressCB is a callable that will be invoked with two arguments: the number
    of bytes transferred so far, and a flag that is passed as 1 if the transfer
    is completed. If the call to progressCB returns true, the user has cancelled
    the transfer.

    """

    dest_fp = open(destination, "wb")

    headers = {}
    if identity is not None:
        headers["X-Client-DN"] = identity

    url_info = urlparse.urlparse(download_url)
    host = url_info[1]
    path = url_info[2]

    print "Connect to ", host
    conn = connectionClass(host)

    print "Downloading %s into %s" % (download_url, destination)

    #
    # We want strict enabled here, otherwise the empty
    # result we get when querying a gsihttp server with an http
    # client results in a valid response, when it should have failed.
    #

    try:
        conn.strict = 1
        conn.request("GET", path, headers = headers)

        print "request sent to ", conn

        resp = conn.getresponse()

        print "response is ", resp
        print "Request got status ", resp.status
    except httplib.BadStatusLine:
        raise DownloadFailed("bad status from http (server type mismatch?)")

    if int(resp.status) != 200:
        raise DownloadFailed(resp.status, resp.reason)

    try:
        hdr = resp.getheader("Content-Length")
        print "Got hdr ", hdr
        print resp.msg.headers
        hdr_size = int(hdr)
    except (TypeError, KeyError):
        raise DownloadFailed("server must provide a valid content length")

    #
    # See if the file size is what we expect, only if
    # the user has passed in a size.
    #
    if size is not None:
        size = int(size)

        print "got size ", hdr_size

        if hdr_size != size:
            raise DownloadFailed("Size mismatch: server says %d, metadata says %d" %
                                 (hdr_size, size))

    #
    # Set up for download
    #

    if checksum is not None:
        digest = md5.new()
    else:
        digest = None
    bytes_left = hdr_size
    buf_size = 4096

    #
    # and GO
    #

    while bytes_left > 0:
        if bytes_left > buf_size:
            bytes_to_read = buf_size
        else:
            bytes_to_read = bytes_left

        # print "Reading %d bytes" % (bytes_to_read)
        buf = resp.read(bytes_to_read)

        if buf == "":
            print "FILE TOO SHORT in download"
            dest_fp.close()
            raise DownloadFailed("End of file before %d bytes read" % (size))

        if digest is not None:
            digest.update(buf)
        #
        # Send a callback if we have a valid callback reference.
        # Handle a cancellation of the transfer.
        #
        if progressCB is not None:
            cancel = progressCB(size - bytes_left, 0)
            if cancel:
                print "DL got cancel!"
                dest_fp.close()
                raise DownloadFailed("Cancelled by user")
        
        dest_fp.write(buf)

        bytes_left -= len(buf)

    #
    # Done reading. Check the checksum and flag an
    # exception if it doesn't match.
    #
    # for now, leave the file in place; need to
    # figure out the right semantics for this case.

    dest_fp.close()


    if progressCB is not None:
        progressCB(size, 1)

    if checksum is not None:
        download_digest = digest.hexdigest()
        if download_digest != checksum:
            raise DownloadFailed("Checksum mismatch on download: download was %s, metadata was %s"
                                 % (download_digest, checksum))
        else:
            print "DOwnload success! ", download_digest

def HTTPUploadFiles(identity, upload_url, file_list, progressCB):
    """
    Upload the given list of files to the server using HTTP.

    Identity is the DN of the client submitting the files.

    progressCB is a callback that will be invoked this way:

       progressCB(filename, bytes_sent, total_bytes, file_done, transfer_done)

    filename is the file to which the progress update applies
    bytes_sent and total_bytes denote the file's progress
    file_done is set when the given file upload is complete
    transfer_done is set when the entire transfer is complete

    If progressCB returns true, the transfer is to be cancelled.

    """

    uploader = HTTPUploadEngine(identity, upload_url, progressCB)
    uploader.UploadFiles(file_list)

def GSIHTTPUploadFiles(upload_url, file_list, progressCB):
    """
    Upload the given list of files to the server using HTTP.

    progressCB is a callback that will be invoked this way:

       progressCB(filename, bytes_sent, total_bytes, file_done, transfer_done)

    filename is the file to which the progress update applies
    bytes_sent and total_bytes denote the file's progress
    file_done is set when the given file upload is complete
    transfer_done is set when the entire transfer is complete

    If progressCB returns true, the transfer is to be cancelled.

    """

    def GSIConnectionClass(host):
        tcpAttr = Utilities.CreateTCPAttrAlwaysAuth()
        return io.GSIHTTPConnection(host, tcpAttr = tcpAttr)

    uploader = HTTPUploadEngine(None, upload_url, progressCB,
                                GSIConnectionClass)
    uploader.UploadFiles(file_list)

class HTTPUploadEngine:
    """
    An HTTPUploadEngine bundles up the functionality need to implement
    HTTPUploadFiles.
    """
    
    def __init__(self, identity, upload_url, progressCB,
                 connectionClass = httplib.HTTPConnection):
        self.identity = identity
        self.upload_url = upload_url

        self.connectionClass = connectionClass

        if progressCB is not None:
            if not callable(progressCB):
                raise UploadFailed("Progress callback not a callable object")
        self.progressCB = progressCB

    def UploadFiles(self, file_list):
        """
        Upload the list of files to the datastore.

        We only support files, not directories, so do a pass over
        them to ensure that they are all files.
        """

        print "Upload: check files"

        for file in file_list:
            if not os.path.exists(file):
                raise FileNotFound(file)
            elif not os.path.isfile(file):
                raise NotAPlainFile(file)

        print "Upload: create manifest"
        (manifest, file_info) = self.constructManifest(file_list)

        print "Upload: Created manifest"

        try:
            parsed = urlparse.urlparse(self.upload_url)
            host = parsed[1]
            base_path = parsed[2]

            # log.debug("upload mainfest: host='%s' base_path='%s'", host, base_path)

            #
            # We want strict enabled here, otherwise the empty
            # result we get when querying a gsihttp server with an http
            # client results in a valid response, when it should have failed.
            #
            conn = self.connectionClass(host)
            conn.strict = 1
            
            transfer_key = self.uploadManifest(conn, base_path, manifest)
            
            # log.debug("Manifest upload returns '%s'", transfer_key)
        
            for idx, file, basename in file_info:
                conn = self.connectionClass(host)
                conn.strict = 1
                url_path = string.join([base_path, transfer_key, str(idx)], "/")
                self.uploadFile(conn, file, url_path)

            if self.progressCB is not None:
                self.progressCB('', 0, 0, 0, 1)

        except UploadFailed, e:
             print "Upload failed: ", e
             if self.progressCB is not None:
                 self.progressCB('', 0, 0, 0, 1)

             raise e

    def uploadFile(self, conn, file, url_path):
        """
        Upload file to the HTTPConnection conn, placing it at url_path.

        We open the file for reading, and read from it in chunks, sending
        the data to the HTTP connection.
        """

        #
        # Determine the length of the file.
        # The paranoid part of me worries about a race condition
        # between doing the stat and opening the file, and wishes
        # for the unix fstat() call. Probably not a real-life problem tho.
        #

        st = os.stat(file)
        size = st.st_size

        #
        # Open file (do it now before we waste the server's time
        # on a connection that might fail if the file doesn't open).
        #
        # Important to remember the "b" in the spec, otherwise we will
        # have problems on Windows.
        #

        fp = open(file, "rb")

        #
        # Fire up the connection and send headers
        #

        print "Send headers"

        conn.connect()
        conn.putrequest("POST", url_path)
        conn.putheader("X-Client-DN", self.identity)
        conn.putheader("Content-type", "application/octet-stream")
        conn.putheader("Content-Length", size)
        conn.endheaders()

        #
        # Now we can stream the file across.
        #

        if self.progressCB is not None:
            self.progressCB(file, 0, size, 0, 0)

        n_sent = 0

        print "sending file"

        try:
            left = 0
            while size - n_sent > 0:
                buf = fp.read(4096)
                if buf == "":
                    break
                conn.send(buf)
                n_sent += len(buf)
                if self.progressCB is not None:
                    self.progressCB(file, n_sent, size, 0, 0)

        except socket.error, e:
            if self.progressCB is not None:
                self.progressCB(file, n_sent, size, 1, 1)
            print "Hm, got a socket error."
            raise UploadFailed(e[1])

        if self.progressCB is not None:
            self.progressCB(file, n_sent, size, 1, 0)
        #
        # All done!
        #

        resp = conn.getresponse()

        print "Upload got status ", resp.status

        conn.close()
        
    def uploadManifest(self, conn, base_path, manifest):
        """
        Upload the manifest to the upload server.

        This is done with a POST to the /manifest path.
        The server will return the string "transfer_key: <keystring>"

        """

        # conn.debuglevel = 10
        headers = {"X-Client-DN": self.identity}

        upload_url = string.join([base_path, "manifest"], "/")
        
        conn.request("POST", upload_url, manifest, headers)
        resp = conn.getresponse()

        print "post returns ", resp

        if resp.status != 200:
            raise UploadFailed((resp.status, resp.reason))

        transfer_key = None
        error_reasons = []

        print "Reading response, headers are ", resp.msg.headers
        result = resp.read()
        
        for tline in result.split("\n"):
            print "got tline <%s>" % (tline)
            if tline == "":
                continue
            m = re.search("^(\S+):\s+(.*)", tline)

            if m is None:
                raise UploadFailed("Invalid line in manifest return: %s" % (tline))

            key = m.group(1)
            value = m.group(2)

            if key == "transfer_key":
                transfer_key = value
            elif key == "return_code":
                return_code = int(value)
            elif key == "error_reason":
                error_reasons.append(value)

        if return_code == 0:
            return transfer_key
        else:
            print "Upload failed: "
            for r in error_reasons:
                print "   ", r
            raise UploadFailed((return_code, error_reasons))
        
    
    def constructManifest(self, file_list):
        """
        Construct a transfer manifest from the given file list.
        """

        manifest = ConfigParser.ConfigParser()

        manifest.add_section("manifest")

        manifest.set("manifest", "num_files", len(file_list))

        #
        # First iterate through the files computing the shortname.
        # Ensure that we don't have any duplicates.
        # Also check to ensure that each is a normal file, not
        # a directory or anything goofy.
        #

        file_map = {}
        file_info = []
        idx = 0
        for file in file_list:

            if not os.path.exists(file):
                raise FileNotFound(file)
            elif not os.path.isfile(file):
                raise NotAPlainFile(file)

            base = os.path.basename(file)

            if file_map.has_key(base):
                raise DuplicateFile((file, file_map[base]))
            else:
                file_map[base] = file

            file_info.append((idx, file, base))
            idx += 1

        del file_map

        #
        # Now compute checksums and complete the manifest
        #

        for idx, file, base in file_info:

            print "Checksum ", file

            s = os.stat(file)

            fp = open(file, "rb")

            digest = md5.new()
            while 1:
                buf = fp.read(32768)
                if not buf:
                    break
                digest.update(buf)
            fp.close()

            section = str(idx)
            manifest.add_section(section)
            manifest.set(section, "name", base)
            manifest.set(section, "size", s.st_size)
            manifest.set(section, "checksum", digest.hexdigest())

        #
        # Retrieve the manifest as a string
        #
        io = cStringIO.StringIO()
        manifest.write(io)
        mstr = io.getvalue()
        io.close()

        return (mstr, file_info)

if __name__ == "__main__":

    logger = logging.getLogger("AG")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    import time
    import os

    class TestVenue:
        def __init__(self):
            self.data = {}
            
        def GetData(self, filename):
            
            if self.data.has_key(filename):
                d = self.data[filename]
            else:
                d = None
            print "GetData %s returning %s" % (filename, d)
            return d

        def UpdateData(self, desc):
            self.data[desc.GetName()] = desc
            print "UpdateData: ", desc

        def AddData(self, desc):
            self.data[desc.GetName()] = desc
            print "AddData: ", desc
            

    v = TestVenue()
    ds = DataStore(v, "/temp")
    s = GSIHTTPTransferServer(('', 9011))

    class Handler:
        def GetDownloadFilename(self, id_token, url_path):
            print "Get download: id='%s' path='%s'" % (id_token, url_path)
            return r"c:\temp\junoSetup.exe"

        def GetUploadFilename(self, id_token, file_info):
            print "Get upload filename for %s %s" % (id_token, file_info)
            return os.path.join("c:\\", "temp", "uploads", file_info['name'])

        def CanUploadFile(self, id_token, file_info):
            print "CanUpload: id=%s file_info=%s" % (id_token, file_info)
            return 1

        def AddPendingUpload(self, id_token, filename):
            print "AddPendingUpload: %s %s" % (id_token, filename)

        def CompleteUpload(self, id_token, file_info):
            print "CompleteUpload %s %s" % (id_token, file_info)

    ds.SetTransferEngine(s)

    prefix = "test"
    s.RegisterPrefix(prefix, Handler())

    print s.GetDownloadDescriptor(prefix, "JunoSetup.exe")
    print s.GetUploadDescriptor(prefix)

    s.run()

    try:
        while 1:
            time.sleep(.1)

    except:
        os._exit(0)
