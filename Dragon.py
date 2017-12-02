class Dragon(Unit):

	self.MIN_TIME_BETWEEN_TURNS = 2;
	self.MAX_TIME_BETWEEN_TURNS = 7;
	self.MIN_HITPOINTS = 50;
	self.MAX_HITPOINTS = 100;
	self.MIN_ATTACKPOINTS = 5;
	self.MAX_ATTACKPOINTS = 20;

    def __init__(x, y):
		##random n of hitpoints
		#random delay

		if not self.spawn(x, y):
		    return


    def run():
		adjacentPLayers = ArrayList<Direction>
		self.running = true
		while Gamestate.getRunningState() and this.running:
		    try:
				#Sleep while Dragon considers next move
				#Stop if dragon runs out of hitpoints
				if(self.getHitpoints() <= 0):
				    break
				#Decide which Players are near
				#Pick random player to attack
				##No PLayers
				##Attack Player
			except:
				pass