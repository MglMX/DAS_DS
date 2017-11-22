

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface Servidor_I extends Remote {
    public void registrar (String nombreCliente) throws RemoteException;
    public void difundirMensaje(String usuario, String mensaje) throws RemoteException;
    public void desconectar(String nombreCliente) throws RemoteException;
}
