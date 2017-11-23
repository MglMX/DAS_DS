import java.rmi.Remote;
import java.rmi.RemoteException;

public interface Server extends Remote {
	public boolean connectClient (String clientName) throws RemoteException;
	public int getNumberOfClients() throws RemoteException;
	public void notifyConnected() throws RemoteException;
}
