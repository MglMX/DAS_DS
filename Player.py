class PLayer(Unit):

def var timeBetweenTurns
def var MIN_TIME_BETWEEN_TURNS = 2
def var MAX_TIME_BETWEEN_TURNS = 7
def var MAX_HITPOINTS = 20
def var MIN_HITPOINTS = 10
def var MIN_ATTACKPOINTS = 1
def var MAX_ATTACKPOINTS = 10

    def _init_(x, y):
	#random hitpoint and attackpoints
	#random delay
	if(!spawn(x, y)):
	    return
	#player thread?

    def run()
	def var direction
	def var adjacentUnitType
	def var targetX = 0
	def var targetY = 0
	self.running = true
	
	while(GameState.getRunningState() && self.running):
	    try:
		#sleep while player considers next move
		if(getHitPoints <=0):
		    break
	#random direction to move if no units present
	#if player at end of map/can't move there x4 NWSE
	#if noUnits in square move if there's player attempt healing if dragin there attempot attacking
