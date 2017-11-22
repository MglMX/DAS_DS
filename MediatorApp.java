
package org.komparator.mediator.ws;

import java.util.Timer;

public class MediatorApp {

	public static void main(String[] args) throws Exception {
		// Check arguments
		if (args.length == 0 || args.length == 2) {
			System.err.println("Argument(s) missing!");
			System.err.println("Usage: java " + MediatorApp.class.getName() + " wsURL OR uddiURL wsName wsURL");
			return;
		}
		String uddiURL = null;
		String wsName = null;
		String wsURL = null;

		// Create server implementation object, according to options
		MediatorEndpointManager endpoint = null;
		if (args.length == 1) {
			wsURL = args[0];
			endpoint = new MediatorEndpointManager(wsURL);
		} else if (args.length >= 3) {
			uddiURL = args[0];
			wsName = args[1];
			wsURL = args[2];
			endpoint = new MediatorEndpointManager(uddiURL, wsName, wsURL);
			endpoint.setVerbose(true);
		}

		try {
			char isPrimary = endpoint.getI();
			Timer timer = null;

			endpoint.start();

			if (isPrimary == '1') {
				System.out.println("Primary Mediator");
				timer = new Timer(true);

				LifeProof myLifeProof = new LifeProof(isPrimary);

				timer.schedule(myLifeProof, 0, 5 * 1000);
				endpoint.awaitConnections();
			} else {
				System.out.println("Secondary Mediator");
				LifeProof myLifeProof = new LifeProof(isPrimary);

				while (!myLifeProof.getExceededMaxDelay()) {
					myLifeProof.run();
					Thread.sleep(5 * 1000);
					if (System.in.available() != 0)
						break;
				}
				if (System.in.available() == 0) {
					endpoint.publishToUDDI();
					endpoint.awaitConnections();
				}
			}

			if (timer != null)
				timer.cancel();

		} finally {
			endpoint.stop();
		}

	}

}

