class Player(Unit):

	self.MIN_TIME_BETWEEN_TURNS = 2
	self.MAX_TIME_BETWEEN_TURNS = 7
	self.MAX_HITPOINTS = 20
	self.MIN_HITPOINTS = 10
	self.MIN_ATTACKPOINTS = 1
	self.MAX_ATTACKPOINTS = 10

    def __init__(x, y):
		#random hitpoint and attackpoints
		#random delay
		if(!spawn(x, y)):
		    return
		#player thread?

    def run()
		var direction
		var adjacentUnitType
		var targetX = 0
		var targetY = 0
		self.running = true
		
		while(GameState.getRunningState() && self.running):
		    try:
			#sleep while player considers next move
			if(getHitPoints <=0):
			    break
		#random direction to move if no units present
		#if player at end of map/can't move there x4 NWSE
		#if noUnits in square move if there's player attempt healing if dragin there attempot attacking
