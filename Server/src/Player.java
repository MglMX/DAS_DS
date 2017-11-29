import java.util.Random;

public class Player extends Unit{
	
	protected final int health_max = 20;
	protected final int health_min = 10;
	protected final int attack_max = 10;
	protected final int attack_min = 1;
	
	//Creates a player
	public Player()
	{
		//Sets healthpoints to a value between 10-20 and attackpower between 1-10
		healthpoints = new Random().nextInt(health_max-health_min+1)+health_min;
		attackpower = new Random().nextInt(attack_max-attack_min+1)+attack_min;;
	}
	
	private void movePlayer(int new_x, int new_y)
	{
		//Check if move is less than one square horizontally or vertically
		if(Math.abs(position_x-new_x) + Math.abs(position_y-new_y) != 1)
			return; //Can not move more than one step at at time
		else 
		{
			//sets new position in x and y
			position_x = new_x;
			position_y = new_y;
		}
	}
	
	
	private void attackDragon()
	{
		
	}
	
	private void healPlayer()
	{
		
	}
	
}
