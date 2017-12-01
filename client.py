from utils  import * #receive and send
from socket import *
from gui    import Gui, Dragon, Player
from board  import Board
from empty  import Empty
import pygame, sys, time

class Client:
	def __init__(self, med_list):
		self.s = None #Will hold the connection between client and server
		self.med_list = med_list

		ip, port = self.getServer() #Fetch a server from the mediator

		self.s = socket(AF_INET, SOCK_STREAM) 
		self.s.connect((ip, port))  #Connect to server

		print 'Successfully connected. Gonna exit now tough'

	def getServer(self):
		print "Inside getServer"
		errors = 0
		while 1:
			for mediator in range(len(self.med_list)): #Trying all the possible mediators.
				s = socket(AF_INET, SOCK_STREAM)
				s.settimeout(0.5)
				ip = self.med_list[mediator][0]
				port = self.med_list[mediator][1]
				try:
					s.connect((ip, port)) #Connect to mediator
					nodeType = {"type":"InitialConnection","content":{"nodeType":0}} #JSon indicating that it is a cliet trying to connect
					send(s, json.dumps(nodeType))
					print "I indicated the mediator that I am a client"
					message = receive(s)								#Receive server ip and port
					print "Received server to connect to"
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
			
	def getAddress(self, initial_msg):
		return eval(initial_msg) #(ip,port)

	def receiveBoard(self, board) :
		msg = receive(self.s)
		msg = eval(msg)

		for x in range(25):
			for y in range(25):
				if msg[x][y][0] == 'dragon':
					#create new dragon
					#put it in the board
					print 'reads Dragon from message'
				elif msg[x][y][0] == 'player':
					#create player
					#put it in the board
					print 'reads Player from message'

	def receivePlayerPosition(self, board):
		msg = receive(self.s) #receives ID of "your" player
		#Point out the player 


IP = 'localhost'

PORT = 6969


s = Client(MED_LIST)
gui = Gui()
board = Board()
#s.receiveBoard(board)
#s.receivePlayerPosition(board)
drag1 = Dragon(5,6)
board.insertObject(drag1)
drag2 = Dragon(9,6)
board.insertObject(drag2)
play1 = Player(14, 12)
board.insertObject(play1)
play2 = Player(15, 12)
board.insertObject(play2)

changed = 1
while 1:
	if changed:
		gui.screen.fill((0,0,0))
		changed = 0
		gui.drawLines()
		gui.drawUnits(board.board)
	changed = gui.handleEvents(play1, drag1, board.board)	
	pygame.display.flip()

