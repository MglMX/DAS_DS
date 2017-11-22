import java.rmi.Remote;
import java.rmi.RemoteException;

public interface Mediator extends Remote {
    public void addServer (String serverName) throws RemoteException;
    public void removeServer (String serverName) throws RemoteException;
}
