import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

@SuppressWarnings("serial")
public class ClientRemote extends UnicastRemoteObject implements Client {
	public void notifyConnected() throws RemoteException {
		System.out.println("You are connected to the server");
	}
	public ClientRemote() throws RemoteException {
		super();
	}
	public static void main(String[] args) throws RemoteException, MalformedURLException, NotBoundException {
		
		if (args.length == 0) {
			System.out.println("Please introduce the name of the client");
			return;
		}
		Client stub=new ClientRemote();  
		
		String clientName = args[0];
		
		Naming.rebind("rmi://localhost:5000/client/"+clientName,stub); 
		
		Mediator stubMediator =(Mediator)Naming.lookup("rmi://localhost:5000/mediator"); 
		Server stubServer = stubMediator.getServerToConnect();
		
		stubServer.connectClient(clientName);
	}
}
