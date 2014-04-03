#!/usr/bin/env python
import socket
import select
import sys
import re 
import random
import time
import string

commands = str(sys.argv)
HOST, PORT = socket.gethostbyname(socket.gethostname()), 36731
print HOST
MAXPLAYER = 30
BUFFERSIZE = 438
MAXBUFFER = 80
playersize = 0 
minplayers = 5 
lobbywait = 20
chatroom = []
troopsize = 1000
playertimeout = 30   #seconds until timeout
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(10)
inputs = [ sock, sys.stdin ]
if len(commands) > 1:
    argindex = 0
    for prompt in commands:
        if prompt == "-f":
             troopsize = int(commands[argindex + 1])
        elif prompt == "-l":
             lobbywait = int(commands[argindex + 1])
        elif prompt == "-m":
             minplayers = int(commands[argindex + 1])
        elif prompt == "-t":
             playertimeout = int(commands[argindex + 1])
        argindex += 1
class player:
    def __init__(self):
        self.strike = 0
        self.playernum = -1
        self.sd = sock 
        self.wbuffer = "" 
        self.name = None 
        self.time = None
        self.resync = 0
        self.isturn = 0
        self.madeoffer = 0
        self.troops = troopsize 
        self.sentoffer = 0
        self.recoffer = 0
        self.didattack = 0
        self.opponents = 0
        self.nooffer = 1 
        self.ingame = 0
        self.dead = 0
        self.fought = 0
    def remove(self):
        inputs.remove(self.sd)
        global playersize
        playersize -= 1
        self.sd.close()
        self.playernum = -1
        self.sd = sock
        self.strike = 0
        self.wbuffer = "" 
        self.name = None
        self.time = None
        self.resync = 0
        self.isturn = 0
        self.troops = troopsize
        self.sentoffer = 0
        self.recoffer = 0 
        self.didattack = 0
        self.opponents = 0
        self.nooffer = 1 
        self.ingame = 0
        self.dead = 0
        self.fought = 0
    def checktime(self):
        if time.time() - self.time > playertimeout:
            self.strike += 1
            self.sd.send("(strike("+str(self.strike)+")(Timeout))")
            self.time = time.time()
            return 1
        return 0
    def calctroops(self):
        result = []
        if self.opponents != 0:
            division = self.troops/self.opponents
            leftover = self.troops - division
            for x in range (0, self.opponents):
                result.append(division)
            for dudes in result:
                if leftover == 0:
                    break
                dudes += 1
                leftover -= 1
        return result
                
            
def checkstrike(criminal):
    if criminal.strike >= 3:
        print "Removed "+ criminal.name
        criminal.remove()
class order:
    def __init__(self,player,message):
        self.player = player 
        self.message = message
class game:
    def __init__(self):
        self.ingame = 0
        self.roundnum = 0 
        self.offerlist = []
        self.phase = -1 
        self.attackgrid = [[0 for x in xrange(30)] for x in xrange(30)]
        self.chatroom = [] 
        self.lobbytime = time.time()
        for i in range(31):
            self.chatroom.append(player())
    def newround(self):
        for players in self.chatroom:
            players.didattack = 0
            players.sentoffer = 0
            players.opponents = 0
            players.nooffer = 1
            players.recoffer = 0
            if players.playernum != -1 and players.name is not None:
                players.ingame =  1
            elif players.troops <= 0:
                players.ingame = 0
    def checkendgame(self):
        countlive = 0
        keep = None
        for players in self.chatroom:
            if players.playernum != -1 and players.name is not None and players.ingame == 1:
                countlive += 1
                keep = players
            if countlive == 2:
                return 1
        if keep:
            keep.sd.send("(schat(SERVER)(You won the game))")
        return 0 

gameroom = game()
def DOSNAME(name, currentsd):
    namecnt = 0
    base = 0
    r = re.compile("[a-zA-Z.0-9~]*")
    result = r.findall(name)
    filtername = ""
    for strings in result:
        filtername = filtername + strings
        print strings
    fixname = filtername.strip('.').upper()
    strlen = len(fixname)
    if strlen > 6:
        strlen = 6
        fixname = fixname[:6]
    for player in gameroom.chatroom:
        if currentsd != player.sd and player.sd != sock and player.name is not None:
            checkname = player.name
            if '~' in player.name:
                checkname = player.name.split('~')[0]
            if fixname[:strlen] == checkname: 
                namecnt += 1
    if namecnt >= 10:
        base = 1
    if namecnt > 0:
        if base:
            fixname = fixname.strip()+"~"+str(namecnt)
        else:
            fixname = fixname+"~"+str(namecnt)
    return fixname 
gameroom = game(); 
active = 1
argindex = 0
if len(commands) > 1:
    for prompt in commands:
        if prompt == "-t":
            player_activity = int(prompt[argindex + 1])
        argindex += 1
            
while active:
    
    timeout = 1
    #put in select statement then accept
    readready, outputready, exceptready = select.select(inputs,[] ,[], timeout)
    if not (readready or outputready or exceptready):
        for people in gameroom.chatroom:
            if people.playernum != -1:
                if people.checktime() == 1:
                    checkstrike(people)
    else:
	    for s in readready:
		if s == sock:                         #accepting new players
		    if playersize >= MAXPLAYER:        #this case is for a full chatroom
			gameroom.chatroom[30].sd, other = sock.accept()
			gameroom.chatroom[30].sd.send("(snovac)")
			gameroom.chatroom[30].remove()
		    else:                             #this is for anyone joining the server
			notfound = 1
			index = 0
			for spots in gameroom.chatroom:
			    if spots.sd == sock:
				break
			    else:
				index += 1 
			connection, ports = sock.accept()
			gameroom.chatroom[index].sd = connection
                        gameroom.chatroom[index].playernum = index
			inputs.append(connection)
                        gameroom.chatroom[index].time = time.time()
			print ports
			print gameroom.chatroom[index].sd
			playersize += 1
		elif s == sys.stdin:                  #input from stdin
		    active = 0
		    for index in gameroom.chatroom:  #force boots everyone out
			if index.sd != sock:
			  index.remove()
		else:              #this is for receiving chat data
                    raw = ""
                    Getdata = 1
		    sender = None
		    for users in gameroom.chatroom:
			if users.sd == s:
			    sender = users
                    s.setblocking(0)
                    sender.time = time.time()
                    badchar = 0
                    valid = 1
		    while Getdata: 
                        try:
                            raw += s.recv(BUFFERSIZE)
                            if not raw:
                                valid = 0
                                sender.remove()
                                break
                        except:
                            break 
		        for c in raw:                 #checks if all characters are ASCII
                            if not c:
                                badchar = 1
                                break
                            if ord(c) < 127 and ord(c) > 31:
                                sender.wbuffer += c
                        if badchar == 1:
                            break
                    if valid == 0:
                        break
                    if badchar == 1:
                        break
		    processcmd = 0
		    sender.wbuffer = re.sub(r"^[^c\(]*","", raw).strip()
		    data = sender.wbuffer
		    sender.wbuffer.rstrip()
		    if "(cjoin" ==  data[:6]:              #player cjoin command, lets them actually join the server
			[args.strip(')') for args in sender.wbuffer.split('(')]
			openparen = sender.wbuffer.count('(')
			closeparen = sender.wbuffer.count(')')
			if closeparen != 2 & openparen != 2:
			    sender.strike += 1
			    output = "(strike("+str(sender.strike)+")(cjoin: Malfromed String))"
			    s.send(output)
			    checkstrike(sender)
			    break
			elif args:
			    blankname = 1 
			    if sender.name is not None:
				sender.strike += 1
				output = "(strike("+str(sender.strike)+")(cjoin: Malformed String))"
				s.send(output)
				checkstrike(sender)
				break
			    if blankname & len(args.strip("))")) <= 8:
				rawname = args.strip("))")
				if rawname.upper() == "ANY" or rawname.upper() == "ALL":
				    sender.strike += 1
				    output = "(strike("+str(sender.strike)+")(cjoin: Malformed String))"
				    s.send(output)
				    checkstrike(sender)
				    break
				sender.name = DOSNAME(rawname, sender.sd) 
				output = "sjoin("+sender.name+")("
				debug = sender.name+" Joined"
                                gameroom.ingame += 1
				print debug 
			    else:               #there is something wrong with the format
				sender.strike += 1
				if sender.name:
				    output = "(strike("+str(sender.strike)+")(cjoin: You have a name))"   
				    s.send(output)
				    checkstrike(sender)
			    names = "("
			    for index in gameroom.chatroom:
				if index.name is not None:
				    names += index.name+","
			    info = "("+str(playersize)+","+str(minplayers)+","+str(playertimeout)+"))"
			    for others in gameroom.chatroom:
				if others.name is not None:
				    outmessage = "(sjoin("+others.name+")"
				    message = outmessage+names.strip(",")+")"+info
				    others.sd.send(message)
				    print message
		    elif "(cstat)" == data:                                    #cstat functionality
			sstat = "(sstat("
			gotname = 1
			name = sender.name
			if name is None:
			    sender.strike += 1
			    output = "(strike("+str(sender.strike)+")(cstat: Malformed String))"
			    s.send(output)
			    checkstrike(sender)
			    gotname = 0
			    break
			if gotname:
			    for players in gameroom.chatroom:
				if players.name is not None:
				    print players.name
				    sstat += players.name+","+str(players.strike)+","+str(players.troops)+","
			    sstat = sstat.strip(',')+"))" 
			    print sstat 
			    s.send(sstat)       
		    elif "(cchat" in data[:6]:                                      #cchat functionality
			regex = re.compile("\(([^\(\)]+)\)")
			openparen = data.count('(')
			closeparen = data.count(')')
			args = regex.findall(data)
                        print data
			allflag = 0
			anyflag = 0 
			serverflag = 0
			if closeparen != 3 & openparen != 3:
			    sender.strike += 1
			    output = "(strike("+str(sender.strike)+")(cchat: Malformed String 1))"
			    s.send(output)
			    checkstrike(sender)
			    break
			else:
			    if args[0].upper() == "ALL":
				allflag = 1
			    elif args[0].upper() == "ANY":
				anyflag = 1
			    elif args[0].upper() == "SERVER":
				serverflag = 1 
                            message = None
                            if len(args) < 2:
				sender.strike += 1
				output = "(strike("+str(sender.strike)+")(cctat: Malformed String 2))"
				s.send(output)
				checkstrike(sender)
				gotname = 0
				break
                            if len(args[1]) > 80:
			        message = args[1][:80]
                            else:
                                message = args[1]
			    name = None
			    gotname = 1
			    name = sender.name
			    if name is None:
				sender.strike += 1
				output = "(strike("+str(sender.strike)+")(cctat: Malformed String 3))"
				s.send(output)
				checkstrike(sender)
				gotname = 0
				break
			    if gotname:
				senddata = "(schat("+name+")("+message[:MAXBUFFER].strip('\n')+"))" 
				if allflag:                                        #send to everyone
				    for index in gameroom.chatroom:
					if index.sd != s and index.sd != sock:
					    index.sd.send(senddata) 
				    print senddata
				elif anyflag:
				    temp = sender.sd
				    while (temp == s or temp == sock or temp == sys.stdin or temp == sender.sd) and playersize > 1:
					temp = random.choice(inputs)
				    temp.send(senddata)
				    print senddata
				else:                                              #send message to only people named
				    allnames = args[0].split(',')
                                    goodnames = 1
                                    for people in allnames:
                                        if people.upper() == "ALL" or people.upper() == "ANY":
                                            goodnames = 0
                                            break
                                    if goodnames == 1:
				        for index in gameroom.chatroom:
					    if index.sd != s:
					        if index.name in allnames:
					    	    index.sd.send(senddata)
                                    else:
				        sender.strike += 1
				        output = "(strike("+str(sender.strike)+")(cchat: Malformed string 4))"
				        s.send(output)
				        checkstrike(sender)
				        break 
				    print senddata
		    else:                                                     #anything else goes here
			sender.strike += 1
			output = "(strike("+str(sender.strike)+")(Wrong format))"
			try:
			    s.send(output)
			except:
			    sender.remove()
			checkstrike(sender)
			break

sock.close() 
