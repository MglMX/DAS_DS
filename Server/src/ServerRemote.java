import java.net.MalformedURLException;
import java.rmi.*;
import java.rmi.server.UnicastRemoteObject;
import java.util.HashSet;

@SuppressWarnings("serial")
public class ServerRemote extends UnicastRemoteObject implements Server{
	private HashSet<String> connectedClients; //FIXME replace String with RemoteClient
	
	public ServerRemote() throws RemoteException {
		super();
		connectedClients = new HashSet<String>();
	}
	
	public void notifyConnected() {
		System.out.println("Connected to the Mediator");
	}
	public boolean connectClient (String clientName) {
		try{  
			//Client stub=(Client)Naming.lookup("rmi://localhost:5000/client/"+clientName);  
			//System.out.println(stub.add(34,4));  
			//connectedClients.add(stub);
		}
		catch(Exception e){}  
		return true;
	}
	public int getNumberOfClients() throws RemoteException{
		return connectedClients.size();
	}
	public static void main(String[] args) throws MalformedURLException, RemoteException, NotBoundException {
		if (args.length < 1) {
			System.out.println("Please introduce the name of the server");
			return;
		}
		
		String serverName = args[0];
		
		try{  
			Server stub=new ServerRemote();  
			Naming.rebind("rmi://localhost:5000/server/"+serverName,stub);  
		}
		catch(Exception e){System.out.println(e);}
		
		Mediator stub=(Mediator)Naming.lookup("rmi://localhost:5000/mediator"); 
		stub.addServer(serverName);
	}
}
