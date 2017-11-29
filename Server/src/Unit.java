
public abstract class Unit {
	protected int healthpoints;
	protected int attackpower;
	protected int position_x;
	protected int position_y;
	
	public Unit(){
		
	}
	
	private void loseHealth(int hp)
	{
		healthpoints -= hp;
	}
	
}
