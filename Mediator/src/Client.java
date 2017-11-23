import java.rmi.Remote;
import java.rmi.RemoteException;

public interface Client extends Remote {
	public void notifyConnected() throws RemoteException;
}
