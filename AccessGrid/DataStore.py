#-----------------------------------------------------------------------------
# Name:        DataStore.py
# Purpose:     This is a data storage server.
#
# Author:      Robert Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: DataStore.py,v 1.3 2003-02-14 20:41:08 olson Exp $
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

import AccessGrid.GUID
from AccessGrid.Utilities import GetHostname
from AccessGrid.Descriptions import DataDescription


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
    
    def __init__(self, venue, pathname):
        """
        Create the datastore.

        Files will be stored in the directory named by pathname.

        """

        self.venue = venue
        
        if not os.path.exists(pathname):
            raise Exception("Datastore path %s does not exist" % (pathname))

        self.pathname = pathname

    def SetTransferEngine(self, engine):
        """
        Set the datastore's default transfer engine.

        """

        self.transfer_engine = engine

    def GetUploadDescriptor(self):
        """
        Return the upload descriptor for this datastore.

        """

        return self.transfer_engine.GetUploadDescriptor()

    def GetDownloadDescriptor(self, filename):
        """
        Return the download descriptor for filename.

        If filename is not present in the datastore, return None.

        """

        path = os.path.join(self.pathname, filename)

        if not os.path.exists(path):
            return None
        
        return self.transfer_engine.GetDownloadDescriptor(filename)
    

    def GetFilePath(self, dn, filename):
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

        if re.search("bad", dn):
            raise NotAuthorized

        path = os.path.join(self.pathname, filename)

        if not os.path.isfile(path):
            raise FileNotFound

        return path

    def CanUploadFile(self, dn, filename):
        """
        Used by the transfer engine to determine if a client is able to
        upload a new file.

        Arguments:
         - dn is the distinguished name of the client
         - filename is the file name client is attempting to upload

        Current test is just to see if the file exists.
        Need to test to see if the client is currently logged into the venue.
        """

        desc = self.venue.GetData(filename)

        if desc is not None:
            return 0

        return 1

    def GetUploadFileHandle(self, dn, filename):
        """
        Return a filehandle appropriate for writing into a
        new upload of filename.

        The client is running with identity "dn".

        This is used by the transfer engine to provide a
        destination for a file upload.

        """

        #
        # First verify that we have a state=pending description in the venue.
        #

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
        fp = file(path, "wb")

        return fp

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

    def AddPendingFile(self, dn, filename):
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
        # print "GET ", self.path
        # print "have datastore ", self.server.datastore
        # print "headers are ", self.headers

        #
        # We require an X-Client-DN header as a token of
        # authentication. It's a bad token, but this is
        # mostly a sample code.
        #

        if self.headers.has_key("X-Client-DN"):
            dn = self.headers["X-Client-DN"]

            try:
                self.ProcessGet(dn)

            except FileNotFound:
                self.send_error(404, "File not found")
            except NotAuthorized:
                self.send_error(403, "Not authorized")
                
        else:
            self.send_error(403, "Not authorized")

    def do_POST(self):
        # print "POST ", self.path
        # print "have datastore ", self.server.datastore
        # print "headers are ", self.headers

        #
        # We require an X-Client-DN header as a token of
        # authentication. It's a bad token, but this is
        # mostly a sample code.
        #

        if not self.headers.has_key("X-Client-DN"):
            self.send_error(403, "Not authorized")
            return None
        
        dn = self.headers["X-Client-DN"]

        #
        # Split path into components, and verify
        # that it started with /. (path_parts[0] is
        # empty if that is the case).
        #

        path_parts = self.path.split('/')
        if path_parts[0] != '':
            self.send_error(404, "File not found")
            return None

        #
        # This is always empty, so nuke it.
        #

        del path_parts[0]

        #
        # Check for /manifest
        #
        if len(path_parts) == 1 and path_parts[0] == "manifest":
            return self.ProcessManifest(dn)

        #
        # Check for /<transfer_key>/<file_num>, designating a file upload.
        #

        if len(path_parts) == 2:
            transfer_key = path_parts[0]
            file_num = path_parts[1]

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
            
            return self.ProcessFileUpload(dn, transfer_key, file_num)
            
        #
        # Default.
        #
        self.send_error(404, "File not found")
        return None

    def ProcessFileUpload(self, dn, transfer_key, file_num):
        """
        Process a possible file upload.

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
        # Open up destination file and initialize digest.
        #

        filename = file_info['name']
        fp = self.server.datastore.GetUploadFileHandle(dn, filename)

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
            while 1:
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
        #
        # Grab the data description for this file from the venue, fix it
        # up with the right info, and update. Or, rather, have the datastore
        # do it.
        #

        self.server.datastore.CompleteUpload(dn, file_info)

    def ProcessManifest(self, dn):
        """
        Read the manifest from the input.

        We can't just let the ConfigParser read as it will read until EOF,
        and the server is leaving the socket open so it can write the
        transfer key back. So we need to obey the Content-Length header, reading
        that many bytes, stuff them into a StringIO, and pass that to the
        ConfigParser to parse.
        """

        #
        # Woo, the int cast is important, as the header comes back
        # as a string and self.rfile.read() complains bitterly if it
        # gets a string as an argument.
        #
        
        len = int(self.headers['Content-Length'])
        buf = self.rfile.read(len)

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
            # print "have manifest"
            # print manifest.sections()
            # manifest.write(sys.stdout)

            #
            # Go through the potential files to be uploaded and ensure
            # that the datastore will be able to store them.
            #

            num_files = manifest.getint("manifest", "num_files")
            for file_num in range(0, num_files):
                name = manifest.get(str(file_num), "name")
                if not self.server.datastore.CanUploadFile(dn, name):
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
        self.end_headers()

        #
        # If all files can be transferred, go ahead and register
        # the manifest with the server, and request the file slots in the
        # datastore (they'll get marked as "pending").
        #
        
        if upload_okay:
            transfer_key = self.server.RegisterManifest(manifest)

            for file in file_list:
                desc = self.server.datastore.AddPendingFile(dn, file)

            self.wfile.write("return_code: 0\n")
            self.wfile.write("transfer_key: %s\n" % (transfer_key))

        else:
            self.wfile.write("return_code: 1\n")
            for err in upload_error_list:
                self.wfile.write("error_reason: %s\n" % (err))

        return None

    def ProcessGet(self, dn):
        """
        Handle an HTTP GET.

        Extract the name of the file from the path; the path should be
        of the format /<filename>. Any other path is incorrect and
        will cause a FileNotFound exception to be raised.

        Call the datastore's OpenFile method to open the file and
        return a python file handle to it. This method can return FileNotFound
        and NotAuthorized exceptions; return an appropriate error code for each.
        """

        path = urllib.unquote(self.path)
        match = re.search("^/([^/?#]+)$", path)

        if not match:
            raise FileNotFound
        
        path = match.group(1)

        # print "Have path '%s'" % ( path)

        fp = None
        try:
            ds_path = self.server.datastore.GetFilePath(dn, path)
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
            print "Start copy to output"
            shutil.copyfileobj(fp, self.wfile)
            print "Done copying"
            fp.close()

class HTTPTransferServer(BaseHTTPServer.HTTPServer):
    """
    An HTTPTransferServer provides upload and download services via HTTP.

    This is mostly an easier-to-understand example than the GASS-based transfer
    server. We fake authentication by passing along the DN of the requesting
    client in the X-Client-DN HTTP header.
    """

    def __init__(self, datastore, address = ('', 0)):
        print "datastore=%s address=%s" % (datastore, address)
        self.datastore = datastore
        BaseHTTPServer.HTTPServer.__init__(self, address, HTTPTransferHandler)

        #
        # upload_manifests is a dictionary mapping from transfer key
        # to the manifest for that transfer.
        #
        self.upload_manifests = {}

    def GetUploadDescriptor(self):
        return urlparse.urlunparse(("http",
                                 "%s:%d" % (GetHostname(), self.socket.getsockname()[1]),
                                 "",    # Path
                                 "", "", ""))
                                 
    def GetDownloadDescriptor(self, path):
        return urlparse.urlunparse(("http",
                                    "%s:%d" % (GetHostname(), self.socket.getsockname()[1]),
                                    urllib.quote(path),
                                    "", "", ""))
                                 

    def RegisterManifest(self, manifest):
        """
        A client has sent a POST to /manifest to initiate an upload.
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
        
    def run(self):
        self.done = 0
        self.server_thread = threading.Thread(target = self.thread_run)
        self.server_thread.start()

    def stop(self):
        self.done = 1

    def thread_run(self):
        """
        thread_run is the server thread's main function.
        """

        while not self.done:
            self.handle_request()

def HTTPDownloadFile(identity, download_url, destination, size, checksum,
                     progressCB = None):
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

    headers = {"X-Client-DN": identity}

    url_info = urlparse.urlparse(download_url)
    host = url_info[1]
    path = url_info[2]

    print "Connect to ", host
    conn = httplib.HTTPConnection(host)

    print "Downloading %s into %s" % (download_url, destination)

    conn.request("GET", path, headers = headers)

    print "request sent"

    resp = conn.getresponse()

    print "Request got status ", resp.status

    #
    # See if the file size is what we expect
    #
    size = int(size)
    hdr_size = resp.getheader("Content-Length")

    if hdr_size is not None:
        try:
            hdr_size = int(hdr_size)
            print "got size ", hdr_size
            
            if hdr_size != size:
                raise DownloadFailed("Size mismatch: server says %d, metadata says %d" %
                                     (hdr_size, size))
        except TypeError:
            print "HMM, Content-Length='%s' is not numeric" % (hdr_size)
    else:
        print "HMM, no content-length header"

    #
    # Set up for download
    #

    digest = md5.new()
    bytes_left = size
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

    download_digest = digest.hexdigest()

    if progressCB is not None:
        progressCB(size, 1)

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

class HTTPUploadEngine:
    """
    An HTTPUploadEngine bundles up the functionality need to implement
    HTTPUploadFiles.
    """
    
    def __init__(self, identity, upload_url, progressCB):
        self.identity = identity
        self.upload_url = upload_url

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
            # print "Connecting to ", host

            print "Upload mainfest to ", host

            conn = httplib.HTTPConnection(host)
            transfer_key = self.uploadManifest(conn, manifest)
            
            print "Manifest upload returns '%s'" % ( transfer_key)
        
            for idx, file, basename in file_info:
                conn = httplib.HTTPConnection(host)
                url_path = string.join(["", transfer_key, str(idx)], "/")
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

        try:
            while 1:
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
        
    def uploadManifest(self, conn, manifest):
        """
        Upload the manifest to the upload server.

        This is done with a POST to the /manifest path.
        The server will return the string "transfer_key: <keystring>"

        """

        headers = {"X-Client-DN": self.identity}
        conn.request("POST", "/manifest", manifest, headers)
        resp = conn.getresponse()

        if resp.status != 200:
            raise UploadFailed((resp.status, resp.reason))

        transfer_key = None
        error_reasons = []

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
    s = HTTPTransferServer(ds, ('', 9011))

    ds.SetTransferEngine(s)

    print s.GetDownloadDescriptor("JunoSetup.exe")
    print s.GetUploadDescriptor()

    s.run()

    try:
        while 1:
            time.sleep(1)

    except:
        os._exit(0)
