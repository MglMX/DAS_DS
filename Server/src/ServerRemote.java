import java.rmi.*;
import java.util.HashSet;

public class ServerRemote {
	private HashSet connectedClients = new HashSet<String>(); //FIXME replace String with RemoteClient
	
	public ServerRemote() throws RemoteException {
		//TODO
	}
	public boolean connectClient (String clientName) {
		try{  
			Client stub=(Client)Naming.lookup("rmi://localhost:5000/client/"+clientName);  
			//System.out.println(stub.add(34,4));  
			connectedClients.add(stub);
		}
		catch(Exception e){}  
	}
	public int getNumberOfClients() throws RemoteException{
		return connectedClients.size();
	}
	public static void main(String[] args) {
		if (args.length < 2) {
			System.out.println("Please introduce the name of the server");
			return;
		}
		
		try{  
			Server stub=new ServerRemote();  
			Naming.rebind("rmi://localhost:5000/server"+args[1],stub);  
		}
		catch(Exception e){System.out.println(e);}  
	}
}
