import java.rmi.*;
import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;

@SuppressWarnings("serial")
public class MediatorRemote extends UnicastRemoteObject implements Mediator {
	private ArrayList<String> connectedServers;
	public MediatorRemote() throws RemoteException {
		this.connectedServers = new ArrayList<String>();
	}
	public void addServer (String serverName) {
		this.connectedServers.add(serverName);
	}
	public void removeServer (String serverName) {
		this.connectedServers.remove(serverName);
	}
	
	public static void main(String[] args) {
		try{  
			Mediator stub=new MediatorRemote();  
			Naming.rebind("rmi://localhost:5000/mediator",stub);  
		}
		catch(Exception e){System.out.println(e);}   
	}
}
