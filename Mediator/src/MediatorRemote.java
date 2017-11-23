import java.net.MalformedURLException;
import java.rmi.*;
import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;

@SuppressWarnings("serial")
public class MediatorRemote extends UnicastRemoteObject implements Mediator {
	private ArrayList<Server> connectedServers;
	public MediatorRemote() throws RemoteException {
		super();
		this.connectedServers = new ArrayList<Server>();
	}
	public void addServer (String serverName) throws MalformedURLException, RemoteException, NotBoundException {
		Server stub=(Server)Naming.lookup("rmi://localhost:5000/server/"+serverName); 
		this.connectedServers.add(stub);
		try {
			stub.notifyConnected();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		System.out.printf("Server %s added\n", serverName);
	}
	public void removeServer (String serverName) throws MalformedURLException, RemoteException, NotBoundException {
		/*Server stub=(Server)Naming.lookup("rmi://localhost:5000/server/"+serverName); 
		this.connectedServers.remove(stub);*/
	}
	
	public Server getServerToConnect () throws RemoteException{
		return this.connectedServers.get(0); //FIXME make this smarter
	}
	
	public static void main(String[] args) {
		try{  
			Mediator stub=new MediatorRemote();  
			Naming.rebind("rmi://localhost:5000/mediator",stub);  
		}
		catch(Exception e){System.out.println(e);}   
	}
}
