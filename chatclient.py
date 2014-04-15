#!/usr/bin/env python
import socket
import sys
import select
import random
import re
#host = '140.160.138.214'
#port = 36708
commands = sys.argv
host = '127.0.1.1'
port = 36731
buffersize = 1024
autoflag = 0
timeout = 0
phase = 0
roundnum = 0
if len(commands) > 1:
    argindex = 0
    for prompt in commands:
        if prompt == "-a":
            autoflag = 1
            timeout = 2 
        elif prompt == "-s":
            host = commands[argindex + 1]  
        elif prompt == "-p":
            port = int(commands[argindex + 1])
        argindex += 1
ai_lines = ["Hi there you moron",  "You suck", "fjakdl;fjlkajfkaj;", "vjaiojfkjlajk ladkfjak;kjf", "jfiioj qqjkflaj", "akhjlvhaisdf"]
ai_wait = 0.0
if autoflag:
    f = open("script")
    ai_lines = f.readlines()
    f.close()
    ai_wait = 10.0
    
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_sock.connect((host,port))
active = 1
serverinput = [client_sock, sys.stdin]
if autoflag == 1:
    client_sock.send("(cjoin(sammy))") 
while active:
    inputready, outputready,exceptready = select.select(serverinput, [],[], timeout) 
    if not (inputready or outputready or exceptready) and autoflag == 1:
        client_sock.send("(cchat(ALL)("+random.choice(ai_lines)+"))")
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
		    if "schat(SERVER)" in message:
			regex = re.compile("\(([^\(\)]+)\)")
			args = regex.findall(message)  
			if args[0] == "PLAN":
			    phase = 0
			elif args[0] == "OFFERL":
			    phase = 1
			elif args[0] == "ACTION":
			    phase = 2
			roundnum = int(args[1].split(',')[1])
		    print message
		    if message == "":
			active = 0 
		elif i == sys.stdin:
		    data = None
                    break
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
		    client_sock.send(write) 
		else:
		    active = 0
client_sock.close() 
