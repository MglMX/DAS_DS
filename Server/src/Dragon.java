import java.util.Random;

public class Dragon extends Unit{
	protected final int health_max = 100;
	protected final int health_min = 50;
	protected final int attack_max = 20;
	protected final int attack_min = 5;
	
	public Dragon()
	{
		healthpoints = new Random().nextInt(health_max-health_min+1)+health_min;
		attackpower = new Random().nextInt(attack_max-attack_min+1)+attack_min;;
	}
	
	private void attackPlayer()
	{
		
	}
	
	
}
