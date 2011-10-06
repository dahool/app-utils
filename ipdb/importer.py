import csv
from sqlobject import *
from sqlobject.sqlbuilder import *
import datetime
import re

BANINFO_TEXT_PAT_FULL = re.compile('^(Baneado el)\s(?P<fecha>\d{2}/\d{2}/\d{4})\s(por)\s(?P<motivo>.*)\s(hasta el)\s(?P<hasta>\d{2}/\d{2}/\d{4}\s\d{2}:\d{2})$')
BANINFO_TEXT_PAT = re.compile('^(Baneado el)\s(?P<fecha>\d{2}/\d{2}/\d{4})\s(por)\s(?P<motivo>.*)$')
BANINFO_TEXT_PERM = re.compile('^(Permanent banned since)\s(?P<fecha>\d{2}/\d{2}/\d{4})\.\s(Reason:)\s(?P<motivo>.*)$')
BANINFO_TEXT_TEMP = re.compile('^(Temp banned since)\s(?P<fecha>\d{2}/\d{2}/\d{4})\s(for)\s(?P<duration>[\d\.{1}]+)\s(?P<periodo>\w*)\.\s(Reason:)\s(?P<motivo>.*)$')
BANINFO_PAT = re.compile('^#(?P<tipo>\d)::(?P<fecha>\d{10})::(?P<admin>.*)::(?P<motivo>.*)::(?P<duration>[\d|\-1]*)$')
BANINFO_N_PAT = re.compile('^#(?P<tipo>\w+)::(?P<fecha>\d{10})::(?P<duration>[\d|\-1]+)::(?P<motivo>.*)$')

def transform_datetime(value):
    if value:
        return datetime.datetime.strptime(value,'%Y-%m-%dT%H:%M:%S')
    return None
    
def bool_to_int(value):
    if value != None and value != '':
        if value.lower() == 'true':
            return 1
    return 0
    
def none_to_long(value):
    if value == None or value == '':
        return 0
    return long(value)
    
def none_to_int(value):
    if value == None or value == '':
        return 0
    return int(value)

def normalize(value):
    s = value.replace("&amp;", "&")
    s = s.replace("amp;", "&")
    s = s.replace("&gt;", ">")
    s = s.replace("gt;", ">")
    s = s.replace("&lt;", "<")
    s = s.replace("lt;", "<")
    s = s.replace("&<", "<")
    s = s.replace("&>", ">")
    s = s.replace("\>", ">")
    s = s.replace("\<", "<")
    return s
    
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

class Penalty(SQLObject):
    playerid = IntCol()
    adminid = IntCol()
    type = IntCol()
    reason = StringCol()
    duration = IntCol()
    synced = BoolCol()
    active = BoolCol()
    updated = TimestampCol()
    created = TimestampCol()
        
class Alias(SQLObject):
    playerid = IntCol()
    nickname = StringCol()
    count = IntCol()
    updated = TimestampCol()
    created = TimestampCol()
    normalized = StringCol()
    
    class sqlmeta:
        lazyUpdate = True
            
class AliasIP(SQLObject):
    playerid = IntCol()
    ip = StringCol()
    count = IntCol()
    updated = TimestampCol()
    created = TimestampCol()

def processHeader(row):
    head = {}
    for i in range(0,len(row)):
        head[row[i]]=i
    return head

def import_server(filename):
    reader = csv.reader(open(filename, 'rb'))
    header = {}
    c = 0
    print "Procesando servers"
    
    #trans.begin()
    
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
                        'gaekey':row[header['key']],
                        'maxlevel':none_to_int(row[header['maxlevel']]),
                        'uid':row[header['uid']]}
                        
            insert = Insert('server', values = data)
            query = connection.sqlrepr(insert)
            connection.query(query)

        else:
            header = processHeader(row)
    
    #trans.commit(close=True)
    
    print "%d servers importados" % c
    
def import_player(filename):
    reader = csv.reader(open(filename, 'rb'))
    serverCache = {}
    header = {}
    c=0
    
    print "Procesando players"
    
    #trans.begin()
    
    for row in reader:
        if header:
            # find the associated server
            server = None
            if serverCache.has_key(row[header['server']]):
                server = serverCache[row[header['server']]]
            else:
                servers = list(Server.selectBy(gaekey=row[header['server']]))
                if len(servers)>0: server = servers[0]
            if server:
                c+=1
                serverCache[row[header['server']]] = server
                
                #if row[header['note']] != '':
                #    note != transform_datetime(row[header['updated']])
                #else:
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
                    #trans.commit()

            else:
                print "Server %s not found" % row[header['server']]
        else:
            header = processHeader(row)
            
    #trans.commit(close=True)
    
    print "%d players importados" % c        

enminutostrans = {'year': 525948.766, 'day': 1440, 'week': 10080, 'minute': 1, 'hour': 60, 'month': 43829.0639}

def enminutos(p):
    if p.endswith('s'):
        p = p[:-1]
    return enminutostrans[p]
    
def procesarBanInfo(baninfo):
    m = BANINFO_TEXT_PAT_FULL.match(baninfo)
    if m:
        created = datetime.datetime.strptime(m.group('fecha'),"%d/%m/%Y")
        hasta = datetime.datetime.strptime(m.group('hasta'),"%d/%m/%Y %H:%M")
        duration = (created - hasta).seconds * 60
        reason = m.group('motivo')
        return True, reason, duration, created
        
    m = BANINFO_TEXT_PAT.match(baninfo)
    if m:
        created = datetime.datetime.strptime(m.group('fecha'),"%d/%m/%Y")
        duration = 0
        reason = m.group('motivo')
        return True, reason, duration, created
        
    m = BANINFO_TEXT_PERM.match(baninfo)
    if m:
        created = datetime.datetime.strptime(m.group('fecha'),"%d/%m/%Y")
        duration = 0
        reason = m.group('motivo')
        return True, reason, duration, created
        
    m = BANINFO_TEXT_TEMP.match(baninfo)
    if m:
        created = datetime.datetime.strptime(m.group('fecha'),"%d/%m/%Y")
        tiempo = float(m.group('duration'))
        periodo = m.group('periodo')
        duration = int(tiempo * enminutos(periodo))
        reason = m.group('motivo')
        return True, reason, duration, created

    m = BANINFO_N_PAT.match(baninfo)
    if m:
        created = datetime.datetime.fromtimestamp(int(m.group('fecha')))
        reason = m.group('motivo')
        try:
            duration = int(m.group('duration'))
        except:
            duration = 0
        return True, reason, duration, created
        
    m = BANINFO_PAT.match(baninfo)
    if m:
        created = datetime.datetime.fromtimestamp(int(m.group('fecha')))
        reason = m.group('motivo')
        try:
            admin = m.group('admin')
        except:
            admin = None
        try:
            duration = int(m.group('duration'))
        except:
            duration = 0
        if admin:
            reason = "%s (%s)" % (reason, admin)
        return True, reason, duration, created

    raise Exception("No se puede verificar patron %s" % baninfo)
    
playerCache = {}
    
def create_baninfo(filename):
    '''process the player file again to fill the penalty table'''
    
    reader = csv.reader(open(filename, 'rb'))
    header = {}
    c=0
    print "Procesando penalties"
    
    for row in reader:
        if header:
            baninfo = row[header['baninfo']]
            if baninfo == '': continue
            player = None
            players = list(Player.selectBy(gaekey=row[header['key']]))
            if len(players) > 0:
                player = players[0]
            if player:
                playerCache[row[header['key']]] = player
                try:
                    status, reason, duration, created = procesarBanInfo(baninfo)
                    if status:
                        data = {'playerid':player.id,
                            'type': 0,
                            'reason': reason,
                            'duration': duration,
                            'created': created,
                            'updated': created,
                            'synced': True,
                            'active': True
                            }
                    
                        insert = Insert('penalty', values = data)
                        query = connection.sqlrepr(insert)
                        connection.query(query)
                        c+=1
                        # commit every 500 players
                        if c % 100 == 0:
                            print "Processing %d" % c
                            #trans.commit()
                except Exception, e:
                    print "%s playerid %s" % (str(e),player.id)
                    
            else:
                print "Player %s not found" % row[header['key']]
        else:
            header = processHeader(row)
            
    #trans.commit()
    
    print "%d penalties generados" % c   
            
def import_alias(filename):
    reader = csv.reader(open(filename, 'rb'))
    header = {}
    c=0
    
    print "Procesando aliases"
    
    for row in reader:
        if header:
            # find the associated server
            player = None
            key = extractPlayerParent(row[header['key']])
            if playerCache.has_key(key):
                player = playerCache[key]
            else:
                players = list(Player.selectBy(gaekey=key))
                if len(players) > 0:
                    player = players[0]
            if player:
                c+=1
                playerCache[key] = player
                name = normalize(row[header['nickname']])
                aliases = list(Alias.selectBy(playerid=player.id, nickname=name))
                if len(aliases) > 0:
                    alias = aliases[0]
                    if alias.updated < transform_datetime(row[header['updated']]):
                        alias.updated = transform_datetime(row[header['updated']])
                    alias.count = alias.count + none_to_int(row[header['count']])
                    alias.syncUpdate()
                    print "Found duplicated %s" % name
                else:
                    data = {'playerid':player.id,
                        'nickname': name,
                        'count':none_to_int(row[header['count']]),
                        'created':transform_datetime(row[header['created']]),
                        'updated':transform_datetime(row[header['updated']]),
                        'normalized': ''}
                    insert = Insert('alias', values = data)
                    query = connection.sqlrepr(insert)
                    connection.query(query)
                
                # commit every 500 players
                if c % 100 == 0:
                    print "Processing %d" % c
                    #trans.commit()

            else:
                print "Player %s not found" % key
        else:
            header = processHeader(row)
            
    #trans.commit()
    
    print "%d aliases importados" % c   

def extractPlayerParent(key):
    values = key.split(":")
    return ":".join(values[2:])
        
def import_aliasip(filename):
    reader = csv.reader(open(filename, 'rb'))
    header = {}
    c=0
    
    print "Procesando ip aliases"
    
    for row in reader:
        if header:
            # find the associated server
            player = None
            key = extractPlayerParent(row[header['key']])
            if playerCache.has_key(key):
                player = playerCache[key]
            else:
                players = list(Player.selectBy(gaekey=key))
                if len(players) > 0:
                    player = players[0]
            if player:
                c+=1
                playerCache[key] = player
                
                data = {'playerid':player.id,
                        'ip':none_to_long(row[header['ip']]),
                        'count':none_to_int(row[header['count']]),
                        'created':transform_datetime(row[header['created']]),
                        'updated':transform_datetime(row[header['updated']])}
                        
                insert = Insert('aliasip', values = data)
                query = connection.sqlrepr(insert)
                connection.query(query)
                
                # commit every 500 players
                if c % 100 == 0:
                    print "Processing %d" % c
                    #trans.commit()

            else:
                print "Player %s not found" % key
        else:
            header = processHeader(row)
            
    #trans.commit()
    
    print "%d ip aliases importados" % c  
    
connection = connectionForURI('mysql://test:test@166.40.231.124/test')
#connection.autoCommit = False
#trans = connection.transaction()
#sqlhub.processConnection = trans
sqlhub.processConnection = connection

import_server('server.csv')
import_player('player.csv')
create_baninfo('player.csv')
import_alias('alias.csv')
import_aliasip('aliasip.csv')
