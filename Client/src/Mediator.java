import java.net.MalformedURLException;
import java.rmi.NotBoundException;
import java.rmi.Remote;
import java.rmi.RemoteException;

public interface Mediator extends Remote {
    public void addServer (String serverName) throws MalformedURLException, RemoteException, NotBoundException;
    public void removeServer (String serverName) throws MalformedURLException, RemoteException, NotBoundException;
    public Server getServerToConnect () throws RemoteException;
}
