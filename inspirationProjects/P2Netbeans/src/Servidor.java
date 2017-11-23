
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;

import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.lang.Thread;
import java.rmi.AccessException;
import java.rmi.NotBoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;


public class Servidor implements Servidor_I {
    private Map<String,Cliente_I> clientes;
    private static String host;
    
    public Servidor() {
        clientes = new HashMap();
    }

    public void registrar (String nombreCliente) throws RemoteException{
        if (System.getSecurityManager() == null) {
            System.setSecurityManager(new SecurityManager());
        }
        try {
            
            Registry registry = LocateRegistry.getRegistry(host);
            Cliente_I cliente = (Cliente_I) registry.lookup(nombreCliente);
            
            clientes.put(nombreCliente,cliente);
            
            //servidor.registrar("Hola holitaaa ");
        } catch (Exception e) {
            System.err.println("Servidor buscando cliente exception:");
            e.printStackTrace();
        }
    }
    
    public void difundirMensaje(String usuario, String mensaje) throws RemoteException{
              
        
        for (Map.Entry e : clientes.entrySet()) {
            ((Cliente_I)e.getValue()).mostrar_mensaje(usuario, mensaje);        
        }
        
    }
    
    public void desconectar(String nombreCliente) throws RemoteException, AccessException{
        
        Registry registry = LocateRegistry.getRegistry(host);
        try {
            registry.unbind(nombreCliente);
        } catch (NotBoundException ex) {
            Logger.getLogger(Servidor.class.getName()).log(Level.SEVERE, null, ex);
        }
        
        //Elimino el cliente del Map. 
        clientes.remove(nombreCliente);  
        
        //Aviso de que se ha desconectado ese usario
        this.difundirMensaje("SISTEMA", "El usuario "+nombreCliente+" ha abandanado la sala");
        
    }
    
    public static void main(String[] args) {
        if (System.getSecurityManager() == null) {
            System.setSecurityManager(new SecurityManager());
        }
        try {
            host=args[0];
            String nombre_objeto_remoto = "Servidor";
            Servidor_I server = new Servidor();
            Servidor_I stub =
                (Servidor_I) UnicastRemoteObject.exportObject(server, 0);
            Registry registry = LocateRegistry.getRegistry();
            registry.rebind(nombre_objeto_remoto, stub);
            System.out.println("Servidor ejecutandose");
        } catch (Exception e) {
            System.err.println("Ejemplo exception:");
            e.printStackTrace();
        }
    }
}
