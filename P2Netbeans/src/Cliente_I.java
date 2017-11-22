
import java.rmi.Remote;
import java.rmi.RemoteException;

/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates


/**
 *
 * @author MiKe
 */
public interface Cliente_I extends Remote{
    public void mostrar_mensaje(String usuario, String mensaje) throws RemoteException;
}
