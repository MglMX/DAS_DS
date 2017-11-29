import pygame,random,sys

pygame.init()

WIDTH = 500
HEIGHT = 500
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

def handleEvents(play, drag, board):
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == 2:
			if event.key == 276:
				if 0 < play.x and board[play.x-1][play.y].name == 'empty':
					play.x = play.x - 1
					board[play.x][play.y] = play
					board[play.x+1][play.y] = Empty(play.x+1,play.y)
					print 'left', play.x
					return 1
			elif event.key == 273:
				if 0 < play.y and board[play.x][play.y-1].name == 'empty':
					play.y = play.y - 1
					board[play.x][play.y] = play
					board[play.x][play.y+1] = Empty(play.x,play.y+1)
					print 'up', play.y
					return 1	
			elif event.key == 275:
				if 24 > play.x  and board[play.x+1][play.y].name == 'empty':
					play.x = play.x + 1
					board[play.x][play.y] = play
					board[play.x-1][play.y] = Empty(play.x-1,play.y)
					print 'right', play.x
					return 1
			elif event.key == 274:
				if 24 > play.y and board[play.x][play.y+1].name == 'empty':
					play.y = play.y + 1
					board[play.x][play.y] = play
					board[play.x][play.y-1] = Empty(play.x,play.y-1)
					print 'down', play.y
					return 1	
			elif event.key == 32:
				print 'fire'
			else:
				print event.key
			return 0
		elif event.type == 5:
			(x,y) = event.pos
			x = x/20
			y = y/20
			print x, y
			if board[x][y].name == 'dragon':
				#attack
				print 'attack dragon'
			elif board[x][y].name == 'player':
				#heal
				print 'heal player'
				


			
			print x,y,event.pos

board = []
for x in range(25):
	board.append([])
	for y in range(25):
		board[x].append(Empty(x,y))
drag1 = Dragon(5,6)
board[drag1.x][drag1.y] = drag1
drag2 = Dragon(9,6)
board[drag2.x][drag2.y] = drag2
play1 = Player(14, 12)
board[play1.x][play1.y] = play1
play2 = Player(15, 12)
board[play2.x][play2.y] = play2

changed = 1
while 1:
	if changed:
		screen.fill((0,0,0))
		changed = 0
		drawLines()
		drawUnits(board)
	changed = handleEvents(play1, drag1, board)	
	pygame.display.flip()