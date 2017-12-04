from gameLog import Logger
from board  import Board
from empty  import Empty
from Dragon import Dragon
from Player import Player

from socket import *
from utils  import *
import sys, time
import select, random

DRAGONS_TO_SPAWN = 2

log = Logger(1, [])
#log.println(msg, priority, keywords)

class ClientConn:
	def __init__(self, conn, server):
		''' Responsible for managing a client.
			Creates a player in the board.
			Has attributes like the player id, the connecting socket, the last time it sent a report, etc '''

		self.server = server
		self.conn = conn
		self.id = self.server.curr_id
		self.server.curr_id += 1
		self.player = self.spawnPlayer()
		self.lastTimeReport = self.server.timer.getTime()

	def spawnPlayer(self):
		''' Spawn player whereven it can. FIXME: concurrency problems  '''
		while 1:
			x = random.randint(0,24)
			y = random.randint(0,24)
			if self.server.board.board[x][y].name == 'empty':
				break
		player = Player(x, y, self.id)
		self.server.board.insertObject(player)
		print 'THIS IS THE PLAYERS HP IN THE SERVER', player.hp
		return player

	def removePlayer(self):
		''' Despawn player and remove it from clients list. FIXME: concurrency problems '''
		self.server.board.board[self.player.x][self.player.y] = Empty(self.player.x, self.player.y)
		self.server.clients.remove(self)
		self.server.players_number -= 1

		#broadcast despawn
		self.server.broadcastCommand({"cmd": "despawn", "playerID": self.id})

	def checkIdle(self, curr_time):
		return curr_time-self.lastTimeReport > 70 #AFK X seconds = disconnnect. FIXME


class Timer:
	''' To check the correct time (as the mediator see's it) '''
	def __init__(self):
		self.timeDiff = 0 #Difference of time between server and mediator
	def getTime(self):
		return time.time()+self.timeDiff

class SendReportState():
	def __init__(self, server):
		'''
		Sends a report to the mediator about how many players are connected to the server
		All states have function "run" '''
		self.server = server
		self.stateName = "Send Report State"
	def run(self):
		#First, check if any clients are idle and remove them if needed.
		toRemove = []
		curr_time = self.server.timer.getTime()
		for client in self.server.clients:
			if client.checkIdle(curr_time):
				toRemove.append(client)
		for client in toRemove:
			client.removePlayer()

		#Then send updated list of clients to mediator
		if self.server.med_sock is None:
			log.println('Error. No mediator socket. Should publish again', 3, ['error'])
			self.server.state = InitialState(self.server)
		else:
			try:
				report = json.dumps({"type":"Report", "content":{"connectedPlayers":int (self.server.players_number)}})
				send(self.server.med_sock, report)
				self.server.state = HandleClientsState(self.server)
			except Exception, e: #Mediator is inactive
				log.println('Error: '+e, 1, ['error'])
				self.server.state = InitialState(self.server) #Try to contact other mediator
			

class HandleClientsState():
	''' All states have function "run" '''
	def __init__(self, server):
		self.server = server
		self.stateName = "Handle Clients State"
		self.TIME_BETWEEN_REPORT = 5 #X.   Each X seconds the server should send the mediator a report with the players that are connected
	
	def handleNewClient(self):
		''' First, accept connection. Then, send the board and the player ID '''

		#Accept connection
		conn,addr = self.server.sock.accept() #conn holds the socket necessary to connect to the client
		conn.settimeout(1) #FIXME set timeout properly

		log.println('Player connected', 1, ['player'])

		#Send board and player ID

		client = ClientConn(conn, self.server)
		board = json.dumps({"type": "board", "content": {"ID": client.id, "board": self.server.board.getBoard()}})
		send(conn, board)

		#Broadcast spawn command to everyone except the client itself
		x = client.player.x
		y = client.player.y
		u_id = client.player.id
		hp = client.player.hp
		ap = client.player.ap
		self.server.broadcastCommand({"cmd": "spawn", "player": {"x":x,"y":y,"id":u_id,"hp":hp,"ap":ap}}, exceptClient=client)
	
		#Add player to list of clients
		self.server.players_number += 1
		self.server.clients.append(client)
		print 'CLIENT.PLAYER.AP', client.player.ap

	def validMove(self, pos):
		if pos[0] > -1 and pos[0] < 25 and pos[1] > -1 and pos[1] < 25:
			return True
		return False



	def handleCommands(self, readable, curr_time):
		toRemove = []
		for client in self.server.clients:
			if client.conn in readable:
				try:
					command = receive(client.conn)
					assert command["type"] == "command"
					command = command["content"]
					if command["cmd"] == "move":
						u_id = command["id"]
						pos = command["where"]
						if self.validMove(pos) and self.server.board.board[pos[0]][pos[1]].name == 'empty':
							self.server.board.movePlayer(u_id, pos) 
							self.server.broadcastCommand(command)

					elif command["cmd"] == "heal":
						u_id = command["id"]
						#Heal player
						obj = self.server.board.findObject(u_id)
						x = obj.x
						y = obj.y
						if(abs(client.player.x - x) + abs(client.player.y - y ) <= 5): #Check if the player is within right distance
							client.player.healDamage(self.server.board, x, y)
							self.server.broadcastCommand(command)
					elif command["cmd"] == "damage":
						u_id = command["id"]
						#Damage dragon
						obj = self.server.board.findObject(u_id)
						if not obj:
							continue
						x = obj.x
						y = obj.y
						if(abs(client.player.x - x) + abs(client.player.y - y ) <= 2): #Check if the dragon is within right distance
							client.player.dealDamage(self.server.board, x, y)
							print "HP for dragon is", self.server.board.board[obj.x][obj.y].hp
							if self.server.board.board[obj.x][obj.y].hp <= 0:
								print 'remove object'
								self.server.broadcastCommand({"cmd": "despawn", "playerID": self.server.board.board[obj.x][obj.y].id})
								self.server.board.board[x][y] = Empty(x,y)
							else:
								command["finalHP"] = obj.hp
								self.server.broadcastCommand(command)
					elif command["cmd"] == "disconnect":
						u_id = command["id"]
						self.server.board.deleteObject(u_id)
						log.println("Player: "+u_id+" deleted from the board",1)
						toRemove.append(client)
					client.lastTimeReport = curr_time
				except Exception, e:
					log.println("Error handling commands: " + str(e) + str(type(e)), 2, ['command', 'error'])
					toRemove.append(client)
		for client in toRemove:
			client.removePlayer()


	def run(self):
		begin = self.server.timer.getTime()
		while 1:
			current = self.server.timer.getTime()
			if current-begin > self.TIME_BETWEEN_REPORT: #Check if the time to handle clients has passed so the state should be changed to sendReport
				break
			elif current > self.server.timeToSynch:
				self.server.state = SynchronizeTimeState(self.server)
				return
			elif current > self.server.nextTime:
				self.server.time += 1
				players = self.server.board.dragonsAI(self.server.time)
				if players:
					for player in players:
						print 'IM HERE!'
						if player.hp == 0:
							print ':)'
							self.server.broadcastCommand({"cmd": "despawn", "playerID": player.id})
						else:
							print ':('
							self.server.broadcastCommand({"cmd": "damage", "id": player.id, "finalHP": player.hp})


			toCheck = [i.conn for i in self.server.clients]
			toCheck.append(self.server.sock)
			toCheck.append(self.server.med_sock)
			readable, writeable, error = select.select(toCheck, [], [], (self.TIME_BETWEEN_REPORT+begin-current))
			
			if self.server.sock in readable:
				try:
					self.handleNewClient()
				except Exception,e:
					log.println('Error receiving client: '+str(e), 1, ['error'])

			elif self.server.med_sock in readable:
				''' Receive list of servers.
					For now I think it is the only thing the mediator sends the servers '''
				message = receive(self.server.med_sock)
				if message["type"] == "ServerList":
					self.server.neighbours = message["content"]["servers"]
					log.println('Server neighbour list updated: '+str(self.server.neighbours), 1, ['update'])
				elif message["type"] == "Error":
					self.server.med_sock = None
					self.server.state = InitialState(self.server) #Seek for another mediator
					return
			else:
				#Client commands
				self.handleCommands(readable, current)

		self.server.state = SendReportState(self.server)

class SynchronizeTimeState():
	''' All states have function "run" '''
	def __init__(self, server):
		self.server = server
		self.stateName = "Synchronization state"
	def run(self):
		''' Run synchronization algorithm:
				Send message to mediator
				Receive T1 from mediator (T1 is the time.time() at the mediator when the mediator sends this message)
				Let x be the time that it took to send and receive that answer. x = Tsend + Treceive. Lets assume Tsend = Treceive
				Let T be the time the server should have. T = T1 + Treceive =~ T1 + (Tsend + Treceive) / 2 = T1 + x / 2
				For precision, repeat this process a few times and calculate an average for x/2.
			TODO: the last step (precision) '''
		try:
			msg = json.dumps({"type":"Synch", "content":"Give me your time"})

			T0 = time.time()
			send(self.server.med_sock, msg)
			T1 = receive(self.server.med_sock)
			T2 = time.time()
			x = T2 - T0

			assert T1["type"] == "Synch"
			T1 = float(T1["content"])

			print '\nx: ' + str(x) + ' | TIME AT MEDIATOR: ' + str(T1 + x/2) + '\n' #FIXME remove this print

			self.server.timer.timeDiff = T2 - (T1 + x/2)
			self.server.timeToSynch = self.server.timer.getTime()+200 #FIXME each 200 seconds the server synchronizes
			self.server.state = HandleClientsState(self.server)

		except Exception, e:
			log.println("Error in SynchronizeTimeState: " + str(e), 2, ['error', 'synch'])
			self.server.state = InitialState(self.server)

		
class InitialState():
	''' All states have function "run"	'''
	def __init__(self, server):
		self.server = server
		self.stateName = "Initial State"
	def run(self):
		self.server.publish()
		self.server.state = SynchronizeTimeState(self.server)
		try:
			message = receive(self.server.med_sock)
			assert message["type"] == 'ServerList'
			self.server.neighbours = message["content"]["servers"]
		except Exception, e:
			log.println("Error in InitialState: " + str(e), 2, ['error', 'init'])


class Server:
	def __init__(self, local_port, med_list):
		self.local_ip = self.findIp()
		self.local_port = local_port
		self.med_list = med_list
		self.sock = socket(AF_INET, SOCK_STREAM)

		log.println('Binding to ('+self.local_ip+' , ' + str(self.local_port)+')',3,['init'])
		self.sock.bind((self.local_ip, local_port))
		self.sock.listen(50)
		self.med_sock = None
		self.state = InitialState(self)

		self.players_number = 0
		self.neighbours = [] #Other servers
		self.timer = Timer()
		self.timeToSynch = None

		self.board = Board()
		self.time = 0 #TURN
		self.nextTime = self.timer.getTime() + 1 #FIXME time until next turn
		self.curr_id = 1 #Next ID to assign
		#################
		self.spawnDragons()
		self.clients = []

	def spawnDragons(self):
		i = 0
		while i < DRAGONS_TO_SPAWN:
			x = random.randint(0,24)
			y = random.randint(0,24)
			if self.board.board[x][y].name == 'empty':
				self.board.insertObject(Dragon(x,y,self.curr_id))
				self.curr_id += 1
				i += 1



			
	def findIp(self):
		''' Find local IP address '''
		s = socket(AF_INET, SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		res = s.getsockname()[0]
		s.close()
		return res

	def run(self): 
		#State machine
		self.state.run()
	def publish(self):
		''' Publish this server on the mediator allowing it to receive updates from other servers '''
		errors = 0
		while 1:
			for mediator in range(len(self.med_list)):
				s = socket(AF_INET, SOCK_STREAM)
				s.settimeout(1)
				ip = self.med_list[mediator][0]
				port = self.med_list[mediator][1]
				try: #Try connecting to each mediator in the same order as it is in utils.py
					log.println('Trying the mediator at ('+ip+','+str(port)+')',1,['publish'])
					s.connect((ip, port))
					nodeType = json.dumps({"type":"InitialConnection","content":{"nodeType":1}}) #JSon indicating that it is a server trying to connect
					send(s, nodeType)
					serverInfo = json.dumps({"type":"ServerInfo","content":{"ip":self.local_ip,"port":self.local_port}}) #JSon with the info of the server
					send(s, serverInfo)

					self.med_sock = s
					break
				except Exception,e:
					log.println('Mediator number %s is not active: %s' % (mediator,e), 1, ['publish'])
					
			else:
				time.sleep(1)
				log.println('There is no active mediator...', 3, ['publish'])
				errors += 1
				if errors == 3: #Try three times before quitting [FIXME number of times]
					sys.exit()
				else:
					continue
			break
	def broadcastCommand(self, command, exceptClient=None):
		''' FIXME should group commands and send them all at once right?'''
		toRemove = []
		for client in self.clients:
			if client != exceptClient:
				try:
					send(client.conn, json.dumps({"type": "command", "content": command}))
				except Exception, e:
					log.println("Error broadcasting command: " + str(e), 2, ['error'])
					toRemove.append(client)
		for client in toRemove:
			client.removePlayer()

PORT = 6971

try:
	PORT=int(sys.argv[1]) #optional port passing in case there are more than one server in the network.
except:
	print "Indicate port. Ex: 6971"
	PORT = int(raw_input("port: "))

s = Server(PORT, MED_LIST)

while 1:
	log.println(s.state.stateName,1,'state') #Debug
	s.run()