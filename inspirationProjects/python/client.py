from socket import *
from utils import * #receive and send
import sys

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
		ip = initial_msg
		ip = ip[2:]
		ip = ip[:-1]
		ip = ip.split(',')
		port = int(ip[1][1:])
		ip = ip[0][:-1]
		return ip,port

IP = 'localhost'
PORT = 6969

s = Client(IP, PORT)
