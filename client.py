from utils  import * #receive and send
from socket import *
from gui    import Gui
from Dragon import Dragon
from Player import Player
from board  import Board
from empty  import Empty
from clientAI import clientAI
import pygame, sys, time, random

from threading import Thread, Semaphore #There is a thread waiting for server commands and updating the gui

def undoCommand(command, client):
	''' TODO - Generate anti command with the command '''
	if command["cmd"] == "move": #MOVE CMD
		u_id = command["id"]
		pos = command["where"]

		client.board.movePlayer(u_id, pos)
		client.changed = 1

	elif command["cmd"] == "spawn" : #SPAWN CMD
		player = command["player"]
		x = player["x"]
		y = player["y"]
		u_id = player["id"]
		hp = player["hp"]
		ap = player["ap"]
		player = Player(x,y,u_id)
		if u_id == client.id:
			print '\nI was spawned... again\n'
			player.isUser=True
			client.spawned = True
			client.player = player
		player.hp = hp
		player.ap = ap
		player.maxHP = hp
		client.board.board[x][y] = player
		client.changed = 1

	elif command["cmd"] == "despawn":
		u_id = command["id"]
		obj = client.board.findObject(u_id)
		if obj:
			x = obj.x
			y = obj.y
			if client.board.board[x][y].name != 'empty':
				if client.board.board[x][y].name == 'player' and client.board.board[x][y].isUser:
					print '\nYou died'
					client.dead = True
					#FIXME
					return
				client.board.board[x][y] = Empty(x,y)
				client.changed = 1

	elif command["cmd"] == "heal":
		u_id = command["id"]
		#Heal player
		obj = client.board.findObject(u_id)
		if obj:
			x = obj.x
			y = obj.y
			#self.board.board[x][y].healDamage(self.board, x, y)
			obj.hp = command["finalHP"]
			client.changed = 1
	elif command["cmd"] == "damage":
		u_id = command["id"]
		#Damage dragon
		obj = client.board.findObject(u_id)
		if obj:
			x = obj.x
			y = obj.y
			#self.board.board[x][y].dealDamage(self.board, x, y)
			obj.hp = command["finalHP"]
		client.changed = 1

class Client:
	def __init__(self, med_list, reuse_id=None, reuse_gui=None):
		self.s = None #Will hold the connection between client and server
		self.med_list = med_list

		ip, port = self.getServer() #Fetch a server from the mediator

		print 'Connecting to',ip,port
		self.s = socket(AF_INET, SOCK_STREAM) 
		self.s.connect((ip, port))  #Connect to server
		self.s.settimeout(2) #FIXME timeout

		server_connection = json.dumps({"type":"ConnectionToServer","content":{"nodeType":0, "reuse_id": reuse_id}})

		try:
			send(self.s,server_connection) #Indicate to the server that I am a client
		except Exception,e:
			print "Error indicating server that I am a client ",e


		self.board = Board()
		self.lock = Semaphore()
		self.dead = False
		self.spawned = False #Necessary because a server might have trouble creating the client

		self.changed = 0 #Board has changed
		print 'Successfully connected.'
		self.lookupAnotherServer = False

		if not reuse_gui:
			self.gui = Gui()
		else:
			self.gui = reuse_gui

	def getServer(self):
		errors = 0
		while 1:
			for mediator in range(len(self.med_list)): #Trying all the possible mediators.
				s = socket(AF_INET, SOCK_STREAM)
				s.settimeout(0.5)
				ip = self.med_list[mediator][0]
				port = self.med_list[mediator][1]
				try:
					s.connect((ip, port)) #Connect to mediator
					nodeType = json.dumps({"type":"InitialConnection","content":{"nodeType":0}}) #JSon indicating that it is a client trying to connect
					send(s, nodeType)
					print "I indicated the mediator that I am a client"
					message = receive(s)								#Receive server ip and port
					break								
				except Exception, e:
					print 'Mediator number %s is not active: %s' % (mediator,e)
			else:
				errors += 1
				if errors == 3:
					print 'There is no active mediator...'
					sys.exit(0)
				else:
					print 'Trying again...'
					time.sleep(1)
					continue
			break
		if message["type"]=="Error":
			print "The was an error while getting the server Info"
			print message
			sys.exit()
		elif message["type"]=="ServerInfo":
			print "Getting server info"
			server = (message["content"]["ip"],message["content"]["port"])
			return server

	def serverConnectionDaemon(self):
		commandList = [] #Command list ordered by arrival of commands (commands should arrive in order --> TCP)
		try:
			while 1:
				command = receive(self.s)

				if command["type"] == "Error":
					if command["content"]["info"] == "timedout":
						continue

				assert command["type"] == "command"
				command = command["content"]

				self.lock.acquire()

				if command["cmd"] == "move": #MOVE CMD
					u_id = command["id"]
					pos = command["where"]

					self.board.movePlayer(u_id, pos)
					self.changed = 1
					commandList.append("TODO")

				elif command["cmd"] == "spawn" : #SPAWN CMD
					player = command["player"]
					x = player["x"]
					y = player["y"]
					u_id = player["id"]
					hp = player["hp"]
					ap = player["ap"]
					player = Player(x,y,u_id)
					if u_id == self.id:
						print '\nI was spawned\n'
						player.isUser=True
						self.spawned = True
						self.player = player
					player.hp = hp
					player.ap = ap
					player.maxHP = hp
					self.board.board[x][y] = player
					self.changed = 1
					commandList.append("TODO")

				elif command["cmd"] == "despawn":
					u_id = command["id"]
					obj = self.board.findObject(u_id)
					if obj:
						x = obj.x
						y = obj.y
						if self.board.board[x][y].name != 'empty':
							if self.board.board[x][y].name == 'player' and self.board.board[x][y].isUser:
								print '\nYou died'
								self.dead = True
								self.lock.release()
								return
							self.board.board[x][y] = Empty(x,y)
							self.changed = 1
					commandList.append("TODO")

				elif command["cmd"] == "heal":
					u_id = command["id"]
					#Heal player
					obj = self.board.findObject(u_id)
					if obj:
						x = obj.x
						y = obj.y
						#self.board.board[x][y].healDamage(self.board, x, y)
						obj.hp = command["finalHP"]
						self.changed = 1
					commandList.append("TODO")
				elif command["cmd"] == "damage":
					u_id = command["id"]
					#Damage dragon
					obj = self.board.findObject(u_id)
					if obj:
						x = obj.x
						y = obj.y
						#self.board.board[x][y].dealDamage(self.board, x, y)
						obj.hp = command["finalHP"]
					self.changed = 1
					commandList.append("TODO")
				elif command["cmd"] == "rollback": #Rollback
					howMany = command["number"]
					for i in range(howMany):
						undoCommand(commandList[-i-1], self) # "anti-commands"
					commandList = commandList[:-howMany]
				self.lock.release()

		except Exception,e:
			print 'Error ready command: ' + str(e)
			print type(e)
			self.lock.acquire()
			if not self.dead:
				self.lookupAnotherServer = True
			self.lock.release()
			return

	def receiveBoard(self):
		msg = receive(self.s)
		assert msg["type"] == "board"
		msg = msg["content"]
		
		boardServer = msg["board"]
		playerID = msg["ID"]

		self.id = playerID

		for x in range(25):
			for y in range(25):
				if boardServer[x][y][0] == 'dragon':
					newDragon = Dragon(x, y, boardServer[x][y][1])
					newDragon.hp = boardServer[x][y][2]
					newDragon.ap = boardServer[x][y][3]
					self.board.insertObject(newDragon)


				elif boardServer[x][y][0] == 'player':
					newPlayer = Player(x, y, boardServer[x][y][1])
					newPlayer.hp = boardServer[x][y][2]
					newPlayer.ap = boardServer[x][y][3]
					newPlayer.maxHP = boardServer[x][y][4]
					if newPlayer.id == self.id:
						newPlayer.isUser=True
						self.spawned = True
						self.player = newPlayer
					self.board.insertObject(newPlayer)

	def sendCommand(self, command):
		try:
			send(self.s, command)
		except Exception, e:
			print "Error sending command:" + str(e)
			if not self.dead:
				self.lookupAnotherServer = True

	def runGame(self):
		''' Careful with accessing shared resources. Use locks. '''

		#Setup daemon to continuosly run commands
		t = Thread(target=self.serverConnectionDaemon)
		t.setDaemon(True)

		
		self.receiveBoard()

		self.changed = 1
		t.start() #Start daemon after receiving the full board

		while 1:
			self.lock.acquire()

			if not self.spawned:
				self.lock.release()
				continue
			if self.dead or self.lookupAnotherServer:
				self.s.close()
				self.lock.release()
				t.join()
				return 0

			if self.changed:
				self.changed = 0
				self.gui.drawLines()			 #Draw grid
				self.gui.drawUnits(self.board.board)

			event = self.gui.handleEvents(self.player, self.board.board, self.lock)
			if event != 0:
				self.changed = 1
			
			if event in (1,2,3,4):   #Left
				self.sendCommand(json.dumps({"type":"command", "content": {"cmd": "move", "id": self.player.id, "where": (self.player.x, self.player.y)}}))
			elif event == 5: #Event for when all the dragons are killed
				self.sendCommand(json.dumps({"type":"command", "content": {"cmd": "disconnect", "id": self.player.id}}))
				print "All the dragons are killed. I will now exit"
				self.lock.release()
				sys.exit()
			elif event != 0:
				target = self.board.board[event[0]][event[1]]
				if target.name == 'dragon':
					cmd = "damage"
				elif target.name == 'player':
					cmd = "heal"
				else:
					self.lock.release()
					continue
				self.sendCommand(json.dumps({"type":"command", "content": {"cmd": cmd, "id": target.id}}))
			self.lock.release()



if __name__ == "__main__":
	s = Client(MED_LIST)
	#s = Client(MED_LIST,reuse_gui=clientAI()) #Comment in order to not use AI
	while 1:
		status = s.runGame()
		if s.lookupAnotherServer: #Server crashed or something
			s = Client(MED_LIST, reuse_id=s.id, reuse_gui=s.gui)
		elif s.dead:
			break