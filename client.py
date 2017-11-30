from socket import *
from utils import * #receive and send
import sys, board
from gui import Gui, Dragon, Player
from board import Board
import pygame
from empty import Empty

class Client:
	def __init__(self, ipMediator, portMediator):
		self.s = None #Will hold the connection between client and server
		self.ipMediator = ipMediator
		self.portMediator = portMediator

		ip, port = self.getServer() #Fetch a server from the mediator

		self.s = socket(AF_INET, SOCK_STREAM) 
		self.s.connect((ip, port))  #Connect to server

		print 'Successfully connected. Gonna exit now tough'

	def getServer(self):
		s = socket(AF_INET, SOCK_STREAM)

		try:
			s.connect((self.ipMediator, self.portMediator)) #Connect to mediator
			s.send('0')										#Send message to say I am a client
			msg = receive(s)								#Receive server ip and port
		except:
			print 'Mediator is offline'
			return

		if "ERROR" in msg:
			print msg
			sys.exit()
		else:
			return self.getAddress(msg)
	def getAddress(self, initial_msg):
		return eval(initial_msg)

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


s = Client(IP, PORT)
gui = Gui()
board = Board()
s.receiveBoard(board)
s.receivePlayerPosition(board)
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

