from utils import *
from clientAI import *
import client,time

from threading import *
import sys

def handleClient():
	s = client.Client(MED_LIST,reuse_gui=clientAI(graphical=False))
	while 1:
		status = s.runGame()
		if s.lookupAnotherServer: #Server crashed or something
			s = client.Client(MED_LIST, reuse_id=s.id, reuse_gui=s.gui)
		elif s.dead:
			break

threads = []
for i in range(100): #100 players
	t = Thread(target=handleClient)
	t.setDaemon(True)
	t.start()
	threads.append(t)
	time.sleep(float(TIME_BETWEEN_COMMANDS)/100)

#s = client.Client(MED_LIST, observer=True)
#s.runGame()

for t in threads:
	t.join()

print 'Done'
