import pygame,random,sys

pygame.init()

WIDTH = 950
HEIGHT = 950
scale = (WIDTH/25,HEIGHT/25)

screen = pygame.display.set_mode((WIDTH, HEIGHT))

class Unit:
	def __init__(self, x, y):
		self.x = x
		self.y = y

class Dragon:
	def __init__(self, x, y):
		self.name = 'dragon'
		self.x = x
		self.y = y

class Player:
	def __init__(self, x, y):
		self.name = 'player'
		self.x = x
		self.y = y

class Empty:
	def __init__(self, x, y):
		self.name = 'empty'
		self.x = x
		self.y = y

def drawLines():
	for x in range(25):
		pygame.draw.line(screen, (255,255,255), (x*scale[0],0), (x*scale[0], HEIGHT))
		pygame.draw.line(screen, (255,255,255), (0,x*scale[1]), (WIDTH,x*scale[1]))

def drawUnits(unitBoard):
	for x in range(25):
		for y in range(25):
			if unitBoard[x][y].name == 'dragon':
				pygame.draw.rect(screen, (255,0,0), (x*scale[0],y*scale[1], scale[0], scale[1]))
			elif unitBoard[x][y].name == 'player':
				pygame.draw.rect(screen, (0,0,255), (x*scale[0],y*scale[1], scale[0],scale[1]))

def handleEvents():
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == 2:
			if event.key == 276:
				print 'left'
			elif event.key == 273:
				print 'up'
			elif event.key == 275:
				print 'right'
			elif event.key == 274:
				print 'down'
			elif event.key == 32:
				print 'fire'
			else:
				print event.key

board = []
for x in range(25):
	board.append([])
	for y in range(25):
		board[x].append(Empty(x,y))

board[0][5]=Dragon(x,y)
board[0][6] =Player(x,y)

changed = 1
while 1:
	handleEvents()
	if changed:
		changed = 0
		drawLines()
		drawUnits(board)
	pygame.display.flip()