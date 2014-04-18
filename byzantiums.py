#!/usr/bin/env python
import socket
import select
import sys
import re 
import random
import time
import string

commands = sys.argv
HOST, PORT = socket.gethostbyname(socket.gethostname()), 36731
print HOST
MAXPLAYER = 30
BUFFERSIZE = 240
MAXBUFFER = 80
playersize = 0 
minplayers = 2 
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
             if troopsize > 99999:
                 troopsize = 99999
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
        self.troops = 0
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
        try:
            self.sd.close()
        except:
            print "not close"
        global playersize
        playersize -= 1
        self.playernum = -1
        self.sd = sock
        self.strike = 0
        self.wbuffer = "" 
        self.name = None
        self.time = None
        self.resync = 0
        self.isturn = 0
        self.troops = 0
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
    def checkcomplete(self):
        openparen = 0
        closeparen = 0
        for chars in self.wbuffer:
            if chars == '(':
                openparen += 1
            elif chars == ')':
                closeparen += 1
        if closeparen == openparen:
            return 1 
        else:
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
        self.attacklist = []
        for i in range(31):
            self.chatroom.append(player())
    def newround(self):
        self.attacklist = []
        self.offerlist = []
        for i in range(0,30):
            for j in range(0,30):
                self.attackgrid[i][j] = 0
        for players in self.chatroom:
            players.didattack = 0
            players.sentoffer = 0
            players.opponents = 0
            players.nooffer = 1
            players.recoffer = 0
            if players.playernum != -1 and players.name is not None:
                players.ingame =  1
            elif players.troops <= 0 and players.name is not None:
                players.remove()
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
            self.roundnum = 0
            self.phase = -1
            for players in self.chatroom:
                if players.troops == 0:
                    players.troops = troopsize
                    players.dead = 0
                    players.ingame = 1
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
while active:
    timeout = 1
    if playersize == 0:
        gameroom.phase = -1
    #put in select statement then accept
    readready, outputready, exceptready = select.select(inputs,[] ,[], timeout)
    if not (readready or outputready or exceptready):
        for people in gameroom.chatroom:
            if people.playernum != -1:
                if people.checktime() == 1:
                    checkstrike(people)
        if gameroom.phase == -1:
            print "Game not started"
            if playersize >= minplayers:
                if time.time() - gameroom.lobbytime > lobbywait:
                    gameroom.phase = 0
                    for players in gameroom.chatroom:
                        if players.playernum != -1:
                            players.troops = troopsize
                    for players in gameroom.chatroom:
                        if players.playernum != -1:
                            players.ingame = 1
                            try:
                                players.sd.send("(schat(SERVER)(PLAN,"+str(gameroom.roundnum + 1)+"))")
                            except:
                                if players.playernum != -1:
                                    players.remove()
        if gameroom.phase == 0:
            print "Phase 1"
            sendmessages = 1 
            for people in gameroom.chatroom:
                if people.sentoffer == 0 and people.playernum != -1 and people.ingame == 1:
                    sendmessages = 0
                    break
            if sendmessages == 1:
                for orders in gameroom.offerlist:
                    data = orders.message 
                    try:
                        orders.player.sd.send(data)
                    except:
                        orders.player.remove()
                    orders.player.nooffer = 0
                    orders.player.recoffer += 1
                gameroom.phase = 1
                del gameroom.offerlist[:]
                for people in gameroom.chatroom:
                    if people.playernum != -1 and people.nooffer == 1 and people.dead == 0 and people.ingame == 1:
                        try:
                            people.sd.send("(schat(SERVER)(OFFERL,"+str(gameroom.roundnum +1)+"))")
                        except:
                            if players.playernum != -1:
                                players.remove()
        elif gameroom.phase == 1:
            print "Phase 2"
            everyoneaccept = 1
            for people in gameroom.chatroom:
                if people.recoffer > 0 and people.playernum != -1 and players.ingame == 1:
                    everyoneaccept = 0
                    break
            if everyoneaccept == 1:
                gameroom.phase = 2 
                for players in gameroom.chatroom:
                    if players.playernum != -1 and players.ingame == 1:
                        try:
                            players.sd.send("(schat(SERVER)(ACTION,"+str(gameroom.roundnum + 1)+"))")
                        except:
                            if players.playernum != -1:
                                players.remove()
                        players.nooffer = 0
        elif gameroom.phase == 2:
            print "Phase 3"
            everyoneact = 1
            for people in gameroom.chatroom:
                if people.didattack == 0 and people.playernum != -1 and people.ingame == 1:
                    print people.name+" Needs to act"
                    everyoneact = 0
                    break
            if everyoneact == 1:
                gameroom.phase = 0 
                gameroom.roundnum += 1
                if gameroom.roundnum > 99999:
                    gameroom.roundnum = 0
                print gameroom.attackgrid
                for guys in range(0, 30):
                    fought = 0
                    distribution = gameroom.chatroom[guys].calctroops()
                    if distribution:
                        #for people in range(0,30):
                        #    for others in range(0,30):
                        #        if gameroom.attackgrid[people][others] == 1:
                        #            message = "(schat(SERVER)(NOTIFY,"+str(gameroom.roundnum)+","+gameroom.chatroom[people].name+","gameroom.chatroom[others].name]+"))"
                        for opponents in range(0, 30):
                            if gameroom.attackgrid[guys][opponents] == 1 and gameroom.chatroom[opponents].troops > 0:
                                if gameroom.chatroom[guys].troops <= 0:
                                    break
                                troops = distribution[gameroom.chatroom[guys].fought]
                                odistribution = gameroom.chatroom[opponents].calctroops()
                                otroops = odistribution[gameroom.chatroom[opponents].fought]
                                troopslost = 0
                                otroopslost = 0
                                troopthreshold = 0
                                otroopthreshold = 0
                                if troops <= 10:
                                    troopthreshold = troops
                                else:
                                    troopthreshold = troops/2
                                if otroops <= 10:
                                    otroopthreshold = otroops
                                else:
                                    otroopthreshold = otroops/2
                                if troopthreshold <= 10:
                                    troopthreshold = gameroom.chatroom[guys].troops
                                if otroopthreshold <= 10:
                                    otroopthreshold = gameroom.chatroom[opponents].troops
                                if gameroom.attackgrid[opponents][guys] == 1:
                                    while troopslost < troopthreshold and otroopslost < otroopthreshold:
                                        if troops > 10:
                                            yourroll = [random.randint(0,10) , random.randint(0,10) , random.randint(0,10)]
                                            opponentroll = [random.randint(0,10) , random.randint(0,10) , random.randint(0,10)]
                                            if max(yourroll) > max(opponentroll):
                                                otroopslost += 1
                                                gameroom.chatroom[opponents].troops -= 1
                                            else:
                                                troopslost += 1
                                                gameroom.chatroom[guys].troops -= 1
                                        else:
                                            gameroom.chatroom[guys].troops = 0
                                            gameroom.attackgrid[opponents][guys] = 0
                                    if otroops <= 10:
                                        gameroom.chatroom[opponents].troops = 0
                                else:
                                    while troopslost < troopthreshold and otroopslost < otroopthreshold:
                                        if troops > 10:
                                            yourroll = [random.randint(0,10) , random.randint(0,10) , random.randint(0,10)]
                                            opponentroll = [random.randint(0,10) , random.randint(0,10) ]
                                            if max(yourroll) >= max(opponentroll):
                                                otroopslost += 1
                                                gameroom.chatroom[opponents].troops -= 1
                                            else:
                                                troopslost += 1
                                                gameroom.chatroom[guys].troops -= 1
                                        else:
                                            gameroom.chatroom[guys].troops = 0
                                            gameroom.attackgrid[opponents][guys] = 0
                                    if otroops <= 10:
                                        gameroom.chatroom[opponents].troops = 0
                                            
                                    #person is not fighting back
                                gameroom.chatroom[opponents].fought += 1
                                gameroom.chatroom[guys].fought += 1
                                gameroom.attackgrid[guys][opponents] = 0
                                gameroom.attackgrid[opponents][guys] = 0
                                if opponents != guys:
                                    if gameroom.chatroom[opponents].troops <= 0:
                                        gameroom.chatroom[guys].troops += troopsize
                                    if gameroom.chatroom[guys].troops <= 0:
                                        gameroom.chatroom[opponents].troops += troopsize
                sstat = "(sstat("
                data =""
	        for players in gameroom.chatroom:
		    if players.name is not None:
		        sstat += players.name+","+str(players.strike)+","+str(players.troops)+","
		sstat = sstat.strip(',')+"))" 
                print sstat
                for players in gameroom.chatroom:
                    if players.playernum != -1:
                        for messages in gameroom.attacklist:
                            try:
                                players.sd.send(messages)
                            except:
                                players.remove();
                        players.sentoffer = 0
                        players.didattack = 0
                        players.recover = 0
                        players.opponents = 0
                        players.fought = 0
                        try:
                            players.sd.send(sstat)
                            players.sd.send("(schat(SERVER)(PLAN,"+str(gameroom.roundnum + 1)+"))")
                        except:
                            players.remove()
                        if players.troops <= 0:
                            players.playernum = -1
                            players.ingame = 0
                            players.dead = 1
                gameroom.newround()
                if gameroom.checkendgame() == 0:
                    gameroom.phase = -1
                    gameroom.lobbytime = time.time()
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
                    try:
                        s.setblocking(0)
                    except:
                        print playersize
                        break
                    valid = 1;
		    while Getdata: 
                        try:
                            raw += s.recv(BUFFERSIZE)
                            if not raw:
                                sender.remove()
                                valid = 0
                                break
                        except:
                            break 
		        for c in raw:                 #checks if all characters are ASCII
                            if ord(c) < 127 and ord(c) > 31:
                                sender.wbuffer += c
                    if valid == 0:
                        break
                    if sender.checkcomplete() == 0:
                        break
		    processcmd = 0
		    sender.wbuffer.rstrip()
		    data = sender.wbuffer
                    sender.wbuffer = ""
                    print data
		    if "(cjoin" ==  data[:6]:              #player cjoin command, lets them actually join the server
                        sender.time = time.time()
			[args.strip(')') for args in data.split('(')]
			openparen = data.count('(')
			closeparen = data.count(')')
			if closeparen != 2 & openparen != 2:
			    sender.strike += 1
			    output = "(strike("+str(sender.strike)+")(cjoin: Malfromed String))"
			    s.send(output)
			    checkstrike(sender)
			    break
			elif args:
			    blankname = 1 
			    if sender.name is not None:
				blankname = 0 
			    if blankname & len(args.strip("))")) <= 8:
				rawname = args.strip("))")
				if rawname.upper() == "ANY" or rawname.upper() == "ALL":
				    sender.strike += 1
				    output = "(strike("+str(sender.strike)+")(cjoin: Malformed String))"
                                    try:
				        s.send(output)
                                    except:
                                        print "ducktape"
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
                            sstat = "(sstat("
			    for players in gameroom.chatroom:
				if players.name is not None:
				    print players.name
				    sstat += players.name+","+str(players.strike)+","+str(players.troops)+","
			    sstat = sstat.strip(',')+"))" 
			    for others in gameroom.chatroom:
				if others.name is not None:
				    outmessage = "(sjoin("+others.name+")"
				    message = outmessage+names.strip(",")+")"+info
                                    try:
				        others.sd.send(message)
                                        others.sd.send(sstat)
                                    except:
                                        orders.remove()
				    print message
		    elif "(cstat)" == data:                                    #cstat functionality
			sstat = "(sstat("
			gotname = 1
			name = sender.name
			if name is None:
			    sender.strike += 1
			    output = "(strike("+str(sender.strike)+")(Malformed String))"
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
			args = regex.findall(data)
                        print sender.name + ": " + data
			allflag = 0
			anyflag = 0 
			serverflag = 0
			if closeparen != 3 & openparen != 3:
			    sender.strike += 1
			    output = "(strike("+str(sender.strike)+")(cchat: Malformed String))"
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
				output = "(strike("+str(sender.strike)+")(cstat: Malformed String))"
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
				output = "(strike("+str(sender.strike)+")(cstat: Malformed String))"
				s.send(output)
				checkstrike(sender)
				gotname = 0
				break
			    if gotname:
				senddata = "(schat("+name+")("+message[:MAXBUFFER].strip('\n')+"))" 
				if allflag:                                        #send to everyone
				    for index in gameroom.chatroom:
					if index.sd != s and index.sd != sock:
                                            try:
					        index.sd.send(senddata) 
                                            except:
                                                break
				    print senddata
				elif anyflag:
				    temp = sender.sd
				    while (temp == s or temp == sock or temp == sys.stdin or temp == sender.sd) and playersize > 1:
					temp = random.choice(inputs)
				    temp.send(senddata)
				    print senddata
				elif serverflag:
                                    sender.time = time.time()
				    #gamelogic
                                    if sender.ingame == 0: 
					sender.strike += 1
					output = "(strike("+str(sender.strike)+")(Malformed string))"
					s.send(output)
					checkstrike(sender)
                                        break
				    commands = message.split(',')
				    phase = -1 
				    roundnum = int(commands[1])
				    if roundnum != (gameroom.roundnum + 1):
					sender.strike += 1
					output = "(strike("+str(sender.strike)+")(Malformed string))"
					s.send(output)
					checkstrike(sender)
                                        break
                                    if sender.ingame != 1:
					sender.strike += 1
					output = "(strike("+str(sender.strike)+")(Malformed string))"
					s.send(output)
					checkstrike(sender)
                                        break
                                    #proccess the command type
				    if (commands[0].upper() == "PLAN"):
					phase = 0
				    elif commands[0].upper() == "ACCEPT" or commands[0].upper() == "DECLINE":
					phase = 1
				    elif commands[0].upper() == "ACTION":
					phase = 2;
				    if phase != gameroom.phase:
					break
				    if gameroom.phase == 0:
                                        if sender.sentoffer == 1:    ##############################Phase 1#############################
                                            break
					if commands[2].upper() == "PASS":
					    print sender.name + " Passed"
                                            sender.sentoffer = 1
					elif commands[2].upper() == "APPROACH":
					    print "Approach"
					    offer = "(schat(SERVER)(OFFERL," + str(gameroom.roundnum + 1) + ","+ commands[3] + ","+commands[4]+"))"
                                            receiver = None
                                            for index in gameroom.chatroom:
                                                if index.name == commands[3]:
                                                    receiver = index
                                            if receiver is not None:
                                                gameroom.offerlist.append(order(receiver, offer))
                                            sender.sentoffer = 1
					else:
					    sender.strike += 1
					    output = "(strike("+str(sender.strike)+")(Malformed string))"
					    s.send(output)
					    checkstrike(sender)
				    elif gameroom.phase == 1:    ##############################Phase 2##################################
                                        if sender.recoffer == 0:
                                            break
                                        if len(commands) != 3:
					    sender.strike += 1
					    output = "(strike("+str(sender.strike)+")(Malformed string)"
					    s.send(output)
					    checkstrike(sender)
                                            break
					if commands[0] == "ACCEPT" or commands[0] == "DECLINE":
                                            message = "(schat(SERVER)("+commands[0]+","+str(gameroom.roundnum + 1)+","+sender.name+")"
                                            print message;
                                            sd = None
                                            for index in gameroom.chatroom:
                                                if index.name == commands[2] and index.ingame == 1:
                                                    try:
                                                        index.sd.send(message)
                                                        sender.recoffer -= 1
                                                    except:
                                                        index.remove()
                                                    break
                                        else:
					    sender.strike += 1
					    output = "(strike("+str(sender.strike)+")(Malformed string)"
					    s.send(output)
					    checkstrike(sender)
                                            break
				    elif gameroom.phase == 2:    ##############################Phase 3 ##################################
                                        if sender.didattack == 1:
					    sender.strike += 1
                                            print "Error here"
					    output = "(strike("+str(sender.strike)+")(Malformed string)"
					    s.send(output)
					    checkstrike(sender)
                                            break
					if commands[2] == "PASS":
					    sender.didattack = 1
					elif commands[2] == "ATTACK":
                                            foundperson = 0
					    for index in gameroom.chatroom:
                                                if index.name == commands[3] and index.ingame == 1:
                                                    print "Player " + str(sender.playernum) +" attacking player "+str(index.playernum)
                                                    notify = "(schat(SERVER)(NOTIFY,"+str(gameroom.roundnum)+","+sender.name+","+index.name+"))"
                                                    gameroom.attacklist.append(notify)
                                                    gameroom.attackgrid[sender.playernum][index.playernum] = 1
                                                    sender.didattack = 1
                                                    sender.opponents += 1
                                                    index.opponents += 1
                                                    foundperson = 1
                                                    break
                                            if foundperson == 0:
					        sender.strike += 1
					        output = "(strike("+str(sender.strike)+")(Malformed string)"
					        s.send(output)
					        checkstrike(sender)
				                break 
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
                                                    try:
					    	        index.sd.send(senddata)
                                                    except:
                                                        index.remove()
                                    else:
				        sender.strike += 1
				        output = "(strike("+str(sender.strike)+")(Malformed string)"
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
