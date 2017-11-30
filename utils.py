#Utils with communication functions that are common to all modules

MED_LIST = [('localhost', 6969), ('localhost', 6970)] #FIXME at deployment

def send(sock, message):
	print 'Sending message:',message
	sock.send('<MSG>'+message+'</MSG>')

def receive(sock, MAX_SIZE=4096):
	try:
		message = ''
		curr_size = 0
		find = '<MSG>'

		for i in range(len(find)):
			c = sock.recv(1)
			if not c:
				return 'disconnect'
			if c != find[i]:
				print 'Error in receive. Invalid header'
				return 'disconnect'

		while '</MSG>' not in message:
			c = sock.recv(1)
			if not c:
				return 'disconnect'
			message += c
			if curr_size > MAX_SIZE+6:
				print 'Received message bigger than MAX_SIZE'
				return 'disconnect'

		return message[:-6]
	except:
		print 'Error in receive. Not enough data in buffer or invalid headers'
		return 'disconnect'

