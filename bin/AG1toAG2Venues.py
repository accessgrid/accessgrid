#!/usr/bin/python1.5
#-----------------------------------------------------------------------------
# Name:        AG1toAG2Venues.py
# Purpose:     This connects to the db for AG1 gets the venues,
#              then spits out a INI formatted file of the information.
# 
#              Note:  This script only works on the machine where the
#                     ag1 venues db lives (currently ag.mcs.anl.gov)
# Author:      Ivan R. Judson
# Created:     2002/12/12
# RCS-ID:      $Id: AG1toAG2Venues.py,v 1.2 2004-03-01 20:54:32 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import socket
import os
import ConfigParser
import string

import pg

def load_pass_1(db_conn, id_map):
    #
    # We'll convert all the rooms, even if some aren't linked to.
    # Later we'll choose the default entry.

    query = db_conn.query("SELECT  id, name, description FROM room")
    rooms = query.getresult()

    for r in rooms:
        room_id, name, desc = r
        
        create_venue(db_conn, id_map, room_id, name, desc)
        
def load_pass_2(db_conn, id_map):
    """
    This pass iterates over the rooms (values in id_map) and
    fills in the connectivity information.
    """
    
    for id, venue in id_map.items():
	query_str = "select destination from exit where source = %d" % id
	query = db_conn.query(query_str)

        for exit_id in query.getresult():

            exit_id = exit_id[0]
            
            if id_map.has_key(exit_id):
                exit_venue = id_map[exit_id]
		id_map[venue['id']]['exits'].append(str(exit_venue['id']))
                
def create_venue(db_conn, id_map, room_id, name, desc):
    """
    Given the room id, name, and description, create a venue.
    """
    
    venue = {
        'id' : room_id,
        'name' : name,
        'description' : desc,
        'media' : [],
        'exits' : []
        }
    
    id_map[room_id] = venue
    
    query_str = "select address, port, media from channel, location where channel.id = location.item and location.location = %d" % room_id    
    query = db_conn.query(query_str)

    for ch in query.getresult():
        m = (ch[2], ch[0], ch[1])
        venue['media'].append(m)
        
if __name__ == "__main__":
    """
    Load the room information from the database.  This occurs in two
    passes. The first pass loads the individual rooms, creating a
    Venue for each, as well as a mapping from venue id to the venue
    for that id. The second pass creates the connectivity information
    between the venues.
    """
    
    venue_id_map = {}

    db_conn = pg.connect(dbname='ag_venues', host='pgsql.mcs.anl.gov',
                         user='wwwtrans', passwd='bigvoyage')
    load_pass_1(db_conn, venue_id_map)
    load_pass_2(db_conn, venue_id_map)
    
    for id in venue_id_map.keys():
	print "[%d]" % id
	venue = venue_id_map[id]
	print "name = %s" % venue['name']
	print "description = %s" % venue['description']
	print "exits = %s" % string.join(venue['exits'], ', ')
	
	for (media, host, port) in venue['media']:
	    print "%s = %s : %d" % (media, host, port)


            
