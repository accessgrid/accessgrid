#!/usr/bin/python2.2
#
# Python certificate statistics tool
#
#

import sys
import os
import os.path
import calendar

# Get the name of the running command
executable = os.path.basename( sys.argv[0] )

# Make sure a path was passed on the command line
if ( len( sys.argv ) < 2 ):
    print "Usage " + executable + " <path to signed certificates>"
    print "\tExample: " + executable + " .globus/simpleCA/newcerts"
    sys.exit( 1 )

# Set the signed certificate directory to the command line argument
cert_dir = sys.argv[1]

# Make sure the signed certificate directory passed in exists
if ( not os.path.exists( cert_dir ) ):
    print cert_dir + " is not a valid path."
    sys.exit( 1 )

# List the filenames of the signed certificates
signed_certs = os.listdir(cert_dir)

# Constants used for converting numeric months to stringed ones.
months = ["", "Jan", "Feb", "Mar", "Apr",
          "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Setup our data dictionary
data={}

# Start parsing throught the cert files
for cert in signed_certs:
    # Stat the file to get the ctime
    (mode,ino,dev,nlink,uid,gid,size,atime,mtime,ctime) = os.stat( os.path.join( cert_dir, cert ) )

    # Convert the ctime into some useable numbers
    (year,month,day,hour,minute,second,weekday,dayofyear,dst) = calendar.localtime(ctime)

    # Drop the .pem suffix as we don't need it
    cert_number_hex = cert.replace( ".pem", "" )

    # Set the file date
    date = months[month] + " %d" % (year)

    # Convert the hex filename into decimal
    cert_number_dec = int( cert_number_hex, 16 )

    # If we haven't hit this date yet, initialize the dict, otherwise
    # increment the month total, and set the grand total to the current
    # value
    if ( not data.has_key(date) ):
        data[date] = {"Month Total":1, "Grand Total":cert_number_dec}
    else:
        data[date]["Month Total"] += 1
        data[date]["Grand Total"] = cert_number_dec

dest = file( "cert-data.csv", "w" )

# Write out the comma separated data
for date in data.keys( ):
    dest.write( date + ",%d,%d" % (data[date]["Month Total"],
                                   data[date]["Grand Total"]) + "\n")

dest.close( )
