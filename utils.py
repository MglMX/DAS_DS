#Utils with communication functions that are common to all modules
import json
from gameLog import Logger

log = Logger(1)

MED_LIST = [('localhost', 6969), ('localhost', 6970)] #FIXME at deployment --> This is the list of mediator (first element) and its replicas

def send(sock, message):
	log.println('Sending message: '+message, 3, ['message'])
	sock.send('<MSG>'+message+'</MSG>')

def getMessageString(sock, MAX_SIZE=4096):
	try:
		message = ''
		curr_size = 0
		find = '<MSG>'

		for i in range(len(find)):
			c = sock.recv(1)
			if not c:
				return '{"type":"Error","content":{"info":"not able to receive since the beggining"}}'
			if c != find[i]:
				log.println('Error in receive. Invalid header', 2, ['error'])
				return '{"type":"Error","content":{"info":"Invalid header"}}'

		while '</MSG>' not in message:
			c = sock.recv(1)
			if not c:
				return '{"type":"Error","content":{"info":"not able to receive"}}'
			message += c
			if curr_size > MAX_SIZE+6:
				log.println('Received message bigger than MAX_SIZE', 2, ['error'])
				return '{"type":"Error","content":{"info":"Received message bigger than MAX_SIZE"}}'

		return message[:-6]
	except:
		log.println('Error in receive. Not enough data in buffer or invalid headers', 2, ['error'])
		return '{"type":"Error","content":{"info":"Not enough data in buffer or invalid headers"}}'

def receive(sock, MAX_SIZE=4096):
	message = getMessageString(sock,MAX_SIZE)
	log.println('Message received: ' + message, 3, ['message'])
	try:
		return json.loads(message)
	except:
		log.println('Error in receive. Couldnt load JSON object from what has been received', 2, ['error'])
		return json.loads('{"type":"Error","content":{"info":"Message is not json object"}}')
	
	

