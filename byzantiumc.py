#!/usr/bin/env python
import socket
import sys
import select
import random
import re
#host = '140.160.138.214'
#port = 36708
commands = sys.argv
host = "127.0.1.1"
port = 36731
buffersize = 1024
autoflag = 1 
timeout = 2 
phase = 0
roundnum = 0
opponents = []
length = 0 
name = "Sambot" 
if len(commands) > 1:
    argindex = 0
    for prompt in commands:
        if prompt == "-s":
            host = commands[argindex + 1]  
        elif prompt == "-p":
            port = int(commands[argindex + 1])
        elif prompt == "-n":
            name = commands[argindex + 1]
        argindex += 1
ai_wait = 0.0
    
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_sock.connect((host,port))
active = 1
serverinput = [client_sock, sys.stdin]
dosomethingelse = 0

client_sock.send("(cjoin("+name+"))") 
while active:
    inputready, outputready,exceptready = select.select(serverinput, [],[], timeout) 
    if not (inputready or outputready or exceptready):
        if autoflag == 1:
            client_sock.send("(cstat)")
            if roundnum > 0:
                dosomethingelse += 1
        if dosomethingelse > 2:
            write = ""
	    if phase == 0:
                client_sock.send("(cchat(SERVER)(PLAN,"+str(roundnum)+",PASS))")
	    elif phase == 1:
	        phase = 1
                if len(args) > 2:
                    write += "(cchat(SERVER)(DECLINE,"+str(roundnum)+","+args[2]+"))"
                    client_sock.send(write)
  	    elif phase == 2:
	        phase = 2
                temp = name
                while temp == name and len > 1:
                    temp = random.choice(opponents)
                    write += "(cchat(SERVER)(ACTION,"+str(roundnum)+",ATTACK,"+temp+"))"
                    client_sock.send(write)
            dosomethingelse = 0
    else:
	    for i in inputready:
		if i == client_sock:
		    message = ""
		    i.setblocking(0)
		    while 1:
			try:
			    message += i.recv(buffersize)
			except:
			    break
                    oparen = 0
                    cparen = 0
                    pos = 0
                    start = 0
                    commands = []
                    for chars in message:
                       if oparen == cparen:
                           start = pos
                       if chars == '(':
                           oparen += 1
                       elif chars == ')':
                           cparen += 1
                       if oparen == cparen:
                           commands.append(message[start:pos])
                       pos += 1
                    for messages in commands:
			    if "schat(SERVER)" in messages:
				regex = re.compile("\(([^\(\)]+)\)")
				everything = regex.findall(messages)
				args = everything[1].split(',')
				trystuff = 1 
				if len(everything) > 3:
				    for index in range(0, len(everything)):
					args = everything[index].split(',')
					if  args[0] == "PLAN" or args[0] == "OFFERL" or args[0] == "ACTION":
					    break
				try:
				    roundnum = int(args[1])
				except:
				    trystuff = 0
				if trystuff == 1: 
				    write = ""
				    if args[0] == "PLAN":
					phase = 0
					client_sock.send("(cchat(SERVER)(PLAN,"+str(roundnum)+",PASS))")
				    elif args[0] == "OFFERL":
					phase = 1
					if len(args) > 2:
					    write += "(cchat(SERVER)(DECLINE,"+str(roundnum)+","+args[2]+"))"
					    client_sock.send(write)
				    elif args[0] == "ACTION":
					phase = 2
					temp = name
					while temp == name and length > 1:
					    temp = random.choice(opponents)
					write += "(cchat(SERVER)(ACTION,"+str(roundnum)+",ATTACK,"+temp+"))"
					client_sock.send(write)
			    elif "(sstat" in messages:
				    regex = re.compile("\(([^\(\)]+)\)")
				    sargs = regex.findall(messages)  
				    allclients = sargs[0].split(',')
				    newlen = len(allclients)
				    if newlen != length:
					if newlen > length:
					    for values in allclients:
						if not values.isdigit() and values not in opponents:
						    opponents.append(values)   
					elif newlen < length:
					    for values in opponents:
						if values not in allclients:
						    if not values.isdigit():
							opponents.remove(values) 
				    print opponents
				    length = newlen
			    elif "(sjoin" in messages:
				regex = re.compile("\(([^\(\)]+)\)")
				args = regex.findall(messages) 
				dudes = args[1].split(',')
				name = args[0]
				for values in dudes:
				    if values not in opponents:
					opponents.append(values) 
			    elif "strike" in messages:
				regex = re.compile("\(([^\(\)]+)\)")
				args = regex.findall(messages) 
			    if messages == "":
				active = 0 
			    print messages
		elif i == sys.stdin:
		    data = None
		    data = sys.stdin.readline().strip()
		    write = ""
		    if data == "stat":
			write += "(cstat)"
		    elif "join" == data[:4]:
			param = data.split()
			write += "(cjoin("+ param[1]+"))"
		    elif data[:2] == "w/":
			param = data[2:].split()
			name = param[0]
			write += "(cchat("+name+")("+data[(3+len(name)):]+"))"
		    elif "any " == data[:4]:
			write += "(cchat(ANY)("+data[4:]+"))"
		    elif "pass" == data[:4]:
			write += "(cchat(SERVER)("
			if phase == 0:
			    write += "PLAN"
			elif phase == 2:
			    write += "ACTION"
			write += ","+str(roundnum)+",PASS))"
		    elif "offer" == data[:5]:
			offerdata = data.split()
			write += "(cchat(SERVER)(PLAN,"+str(roundnum)+",APPROACH,"+offerdata[1]+","+offerdata[2]+"))" 
		    elif "ACCEPT" == data[:6]:
			adata = data.split()
			write += "(cchat(SERVER)(ACCEPT,"+str(roundnum)+","+adata[1]+"))"
		    elif "DECLINE" == data[:7]:
			ddata = data.split()
			write += "(cchat(SERVER)(ACCEPT,"+str(roundnum)+","+ddata[1]+"))"
		    elif "attack" == data[:6]:
			atk = data.split()
			write += "(cchat(SERVER)(ACTION,"+str(roundnum)+",ATTACK,"+atk[1]+"))"
		    else:
			write += "(cchat(ALL)("+data+"))" 
		    for chars in write:
			client_sock.send(chars) 
		else:
		    active = 0
client_sock.close() 
