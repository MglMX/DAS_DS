

import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;

public class Cliente implements Cliente_I{
    private String nombreRemoto;
    private Servidor_I server;
    private static Ventana ventana;
    
    public Cliente (String nombre){
        nombreRemoto=nombre;
        //Creamos el stub del cliente
        
        
    }
    
    @Override
    public void mostrar_mensaje(String usuario,String mensaje){
        ventana.imprimeMensaje(usuario+": "+mensaje);
        //System.out.println(mensaje);
    }
    
    public static void main(String[] args){
        //Obtenemos el objeto servidor
        
        try{
            //Obtenemos el servidor            
            String nombre_server = "Servidor";
            System.out.println("Buscando el objeto remoto");
            Registry registry = LocateRegistry.getRegistry(args[0]);
            Servidor_I servidor = (Servidor_I) registry.lookup(nombre_server);
            //servidor.registrar("Hola holitaaa ");
            
            ventana = new Ventana(servidor);
            InicioSesion inicio = new InicioSesion(ventana, true);
            String nombre = inicio.getNombre();        
            ventana.setUsuario(nombre);

            
        
            //CReamos el stub del cliente
            if (System.getSecurityManager() == null) {
                System.setSecurityManager(new SecurityManager());
            }
            try {
                String nombre_cliente = nombre;
                Cliente_I cliente = new Cliente(nombre);
                Cliente_I stub =
                    (Cliente_I) UnicastRemoteObject.exportObject(cliente, 0);
                //Registry registry = LocateRegistry.getRegistry();
                registry.rebind(nombre_cliente, stub);
                System.out.println("Cliente subido a RMIRegistry");
                
                
                //Añado el cliente al Array de clientes del servidor
                servidor.registrar(nombre_cliente);
               
                //Mostramos la ventana
                ventana.showView();
                
                System.out.println("Llego hasta aquí");
                
            } catch (Exception e) {
                System.err.println("Ejemplo exception:");
                e.printStackTrace();
            }
        }catch (Exception e) {
            System.err.println("Ejemplo_I exception:");
            e.printStackTrace();
        }
        
        //Cliente cliente = new Cliente(args[0]);
        
        
        
        
        
    }
    
}
