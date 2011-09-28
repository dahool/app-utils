import csv
from sqlobject import *
from sqlobject.sqlbuilder import *
import datetime
import re

class Server(SQLObject):
    uid = StringCol()
    gaekey = StringCol()
    name = StringCol()
    admin = StringCol()
    address = StringCol()
    created = TimestampCol()
    updated = TimestampCol()
    onlineplayers = IntCol()
    pluginversion = StringCol()
    maxlevel = IntCol()
    isdirty = BoolCol()
    permission = IntCol()
        
class Player(SQLObject):
    guid = StringCol()
    serverid = IntCol()
    nickname = StringCol()
    ip = StringCol()
    clientid = IntCol()
    connected = BoolCol()
    level = IntCol()
    baninfo = TimestampCol()
    updated = TimestampCol()
    created = TimestampCol()
    note = TimestampCol()
    gaekey = StringCol()

def write_data(filename):
    out = csv.writer(open(filename, 'wb'), delimiter=',')
    servers = Server.select(Server.q.gaekey!=None)
    out.writerow(['oldKey','newKey'])
    for server in servers:
        out.writerow([server.gaekey,server.id])
    players = Player.select(Player.q.gaekey!=None)
    for player in players:
        out.writerow([player.gaekey,player.id])
    
connection = connectionForURI('mysql://test:test@166.40.231.124/test')
sqlhub.processConnection = connection

write_data('relation.csv')
