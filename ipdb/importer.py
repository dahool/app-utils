import csv
from sqlobject import *
from sqlobject.sqlbuilder import *
import datetime

def transform_datetime(value):
    if value:
        return datetime.datetime.strptime(value,'%Y-%m-%dT%H:%M:%S')
    return None
    
def bool_to_int(value):
    if value != None and value != '':
        if value.lower == 'true':
            return 1
    return 0
    
def none_to_int(value):
    if value == None or value == '':
        return 0
    return int(value)

class Server(SQLObject):
    uid = StringCol()
    gaekey = IntCol()
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
    serverid = StringCol()
    nickname = StringCol()
    ip = StringCol()
    clientid = IntCol()
    connected = BoolCol()
    level = IntCol()
    baninfo = TimestampCol()
    updated = TimestampCol()
    created = TimestampCol()
    note = TimestampCol()
    gaekey = IntCol()
    
class Alias(SQLObject):
    playerid = IntCol()
    nickname = StringCol()
    count = IntCol()
    updated = TimestampCol()
    created = TimestampCol()
    ngrams = StringCol()
    
class AliasIP(SQLObject):
    playerid = IntCol()
    ip = IntCol()
    count = IntCol()
    updated = TimestampCol()
    created = TimestampCol()

def processHeader(row):
    head = {}
    for i in range(0,len(row)):
        head[row[i]]=i
    return head

def import_server():
    reader = csv.reader(open('server.csv', 'rb'))
    header = {}
    c = 0
    print "Procesando servers"
    for row in reader:
        if header:
            c+=1
            
            data = {'updated':transform_datetime(row[header['updated']]),
                        'name':row[header['name']],
                        'created':transform_datetime(row[header['created']]),
                        'admin':row[header['admin']],
                        'address':row[header['ip']],
                        'permission':none_to_int(row[header['permission']]),
                        'onlineplayers':none_to_int(row[header['players']]),
                        'pluginversion':row[header['pluginversion']],
                        'isdirty':False,
                        'gaekey':none_to_int(row[header['key']]),
                        'maxlevel':none_to_int(row[header['maxlevel']]),
                        'uid':row[header['uid']]}
                        
            insert = Insert('server', values = data)
            query = connection.sqlrepr(insert)
            connection.query(query)

        else:
            header = processHeader(row)
    
    trans.commit()
    
    print "%d servers importados" % c
    
def import_player():
    reader = csv.reader(open('player.csv', 'rb'))
    serverCache = {}
    header = {}
    c=0
    for row in reader:
        if header:
            # find the associated server
            if serverCache.has_key(row[header['server']]):
                server = serverCache[row[header['server']]]
            else:
                server = Server.selectBy(gaekey=row[header['server']])[0]
            if server:
                c+=1
                serverCache[row[header['server']]] = server
                
                if row[header['note']] != '':
                    note != transform_datetime(row[header['updated']])
                else:
                    note = None
                    
                data = {'serverid':server.id,
                        'guid':row[header['guid']],
                        'nickname':row[header['nickname']],
                        'ip':row[header['ip']],
                        'clientid':none_to_int(row[header['clientId']]),
                        'connected':False,
                        'level':none_to_int(row[header['level']]),
                        'baninfo':transform_datetime(row[header['baninfoupdated']]),
                        'created':transform_datetime(row[header['created']]),
                        'updated':transform_datetime(row[header['updated']]),
                        'note':note,
                        'gaekey':row[header['key']]}
                        
                insert = Insert('player', values = data)
                query = connection.sqlrepr(insert)
                connection.query(query)
                
                # commit every 500 players
                if c % 500 == 0:
                    print "Processing %d" % c
                    trans.commit()

            else:
                print "Server %s not found" % row[header['server']]
        else:
            header = processHeader(row)
            
    trans.commit()
    
    print "%d players importados" % c        

playerCache = {}
        
def import_alias():
    reader = csv.reader(open('alias.csv', 'rb'))
    header = {}
    c=0
    for row in reader:
        if header:
            # find the associated server
            if playerCache.has_key(row[header['player']]):
                player = playerCache[row[header['player']]]
            else:
                player = Player.selectBy(gaekey=row[header['player']])[0]
            if player:
                c+=1
                playerCache[row[header['player']]] = player
                
                data = {'playerid':player.id,
                        'nickname':row[header['nickname']],
                        'count':none_to_int(row[header['count']]),
                        'created':transform_datetime(row[header['created']]),
                        'updated':transform_datetime(row[header['updated']]),
                        'ngrams':row[header['ngrams']]}
                        
                insert = Insert('alias', values = data)
                query = connection.sqlrepr(insert)
                connection.query(query)
                
                # commit every 500 players
                if c % 500 == 0:
                    print "Processing %d" % c
                    trans.commit()

            else:
                print "Player %s not found" % row[header['player']]
        else:
            header = processHeader(row)
            
    trans.commit()
    
    print "%d aliases importados" % c   
           
def import_aliasip():
    reader = csv.reader(open('aliasip.csv', 'rb'))
    header = {}
    c=0
    for row in reader:
        if header:
            # find the associated server
            if playerCache.has_key(row[header['player']]):
                player = playerCache[row[header['player']]]
            else:
                player = Player.selectBy(gaekey=row[header['player']])[0]
            if player:
                c+=1
                playerCache[row[header['player']]] = player
                
                data = {'playerid':player.id,
                        'ip':none_to_int(row[header['ip']]),
                        'count':none_to_int(row[header['count']]),
                        'created':transform_datetime(row[header['created']]),
                        'updated':transform_datetime(row[header['updated']])}
                        
                insert = Insert('aliasip', values = data)
                query = connection.sqlrepr(insert)
                connection.query(query)
                
                # commit every 500 players
                if c % 500 == 0:
                    print "Processing %d" % c
                    trans.commit()

            else:
                print "Player %s not found" % row[header['player']]
        else:
            header = processHeader(row)
            
    trans.commit()
    
    print "%d ip aliases importados" % c  
    
connection = connectionForURI('mysql://test:test@166.40.231.124/test?debug=1')
connection.autoCommit = False
trans = connection.transaction()
sqlhub.processConnection = trans

import_server()
import_player()
import_alias()
import_aliasip()
