import java.rmi.Remote;
import java.rmi.RemoteException;

public interface Mediator_I extends Remote {
    public void addServer (String serverName) throws RemoteException;
}
