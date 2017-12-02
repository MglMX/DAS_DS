class Dragon(Unit):

def var timeBetweenTurns
def var MIN_TIME_BETWEEN_TURNS = 2;
def var MAX_TIME_BETWEEN_TURNS = 7;
def var MIN_HITPOINTS = 50;
def var MAX_HITPOINTS = 100;
def var MIN_ATTACKPOINTS = 5;
def var MAX_ATTACKPOINTS = 20;

     def _init_(x, y):
	##random n of hitpoints
	#random delay

	if(!spawn(x, y):
	    return


     def run():
	adjacentPLayers = ArrayList<Direction>
	self.running = true
	while(Gamestate.getRunningState() && this.running):
	    try:
		#Sleep while Dragon considers next move
		#Stop if dragon runs out of hitpoints
		if(self.getHitpoints() <= 0):
		    break
		#Decide which Players are near
		#Pick random player to attack
		##No PLayers
		##Attack Player
