#
# Unit tests for the rss reader
#


from AccessGrid.RssReader import RssReader

expected_out ="""title: AccessGrid Dev
modified: 1 Jan 2007 09:00:00 UT
Multicast Network Overview13 Aug 2007 15:00:00 UThttps://vv3.mcs.anl.gov:8000/Venues/000000ff6f312bfe008c00dd0022000749c
Access Grid Test Meeting16 Aug 2007 15:00:00 UThttps://vv3.mcs.anl.gov:8000/Venues/000000ff6f312bfe008c00dd0022000749c
Access Grid Test Meeting23 Aug 2007 15:00:00 UThttps://vv3.mcs.anl.gov:8000/Venues/000000ff6f312bfe008c00dd0022000749c
Access Grid Test Meeting30 Aug 2007 15:00:00 UThttps://vv3.mcs.anl.gov:8000/Venues/000000ff6f312bfe008c00dd0022000749c
Access Grid Townhall Meeting4 Sep 2007 15:00:00 UThttps://vv3.mcs.anl.gov:8000/Venues/000000ff6f312bfe008c00dd0022000749c
Access Grid Test Meeting7 Sep 2007 15:00:00 UThttps://vv3.mcs.anl.gov:8000/Venues/000000ff6f312bfe008c00dd0022000749c
Access Grid Townhall Meeting7 Sep 2007 23:00:00 UThttps://vv3.mcs.anl.gov:8000/Venues/000000ff6f312bfe008c00dd0022000749c
"""

rssUrl = 'schedule.rss'
reader = RssReader([],0)
reader._ProcessUrl(rssUrl)
feeds = reader.GetFeeds()
assert feeds[0] == rssUrl
entries = reader.entries[rssUrl]
d = entries[0]
out = ""
out +=  'title: ' + d['feed']['title'] + "\n"
out +=  'modified: ' + d['feed']['modified'] + "\n"
for e in d.entries:
    out +=  e.title + e['modified'] + e.enclosures[0].url + "\n"
assert out == expected_out
