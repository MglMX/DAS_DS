from socket import *

class Client:
	def __init__(self, ipMediator, portMediator):
		print 'Client :D'

IP = 'localhost'
PORT = 6969
s = Client(IP, PORT)
