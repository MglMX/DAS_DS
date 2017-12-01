#Utils with communication functions that are common to all modules
import json
MED_LIST = [('localhost', 6969), ('localhost', 6970)] #FIXME at deployment --> This is the list of mediator (first element) and its replicas

def send(sock, message):
	print 'Sending message:',message
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
				print 'Error in receive. Invalid header'
				return '{"type":"Error","content":{"info":"Invalid header"}}'

		while '</MSG>' not in message:
			c = sock.recv(1)
			if not c:
				return '{"type":"Error","content":{"info":"not able to receive"}}'
			message += c
			if curr_size > MAX_SIZE+6:
				print 'Received message bigger than MAX_SIZE'
				return '{"type":"Error","content":{"info":"Received message bigger than MAX_SIZE"}}'

		return message[:-6]
	except:
		print 'Error in receive. Not enough data in buffer or invalid headers'
		return '{"type":"Error","content":{"info":"Not enough data in buffer or invalid headers"}}'

def receive(sock, MAX_SIZE=4096):
	message = getMessageString(sock,MAX_SIZE)
	print 'Message recived: ' + message
	try:
		return json.loads(message)
	except:
		print 'Error in receive. Couldnt load JSON object from what has been received'
		return json.loads('{"type":"Error","content":{"info":"Message is not json object"}}')
	
	

