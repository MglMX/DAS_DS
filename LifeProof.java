package org.komparator.mediator.ws;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.TimerTask;

import org.komparator.mediator.ws.cli.MediatorClient;
import org.komparator.mediator.ws.cli.MediatorClientException;

import com.sun.xml.ws.client.ClientTransportException;

public class LifeProof extends TimerTask {

	char isPrimary;
	boolean exceededMaxDelay = false;
	private final long MAXDELAY = 15;

	public LifeProof(Object argument) {
		this.isPrimary = (char) argument;
	}

	@Override
	public void run() {
		if (isPrimary == '1') {
			try {
				MediatorClient mc = new MediatorClient("http://localhost:8072/mediator-ws/endpoint");
				mc.imAlive();
				System.out.println("Sent life proof to secondary mediator...");
			} catch (ClientTransportException e) {
				System.out.println("There is no secondary mediator");
			} catch (MediatorClientException e) {
				e.printStackTrace();
			}
		} else {
			LocalDateTime date = MediatorPortImpl.mightBeAlive;
			ZoneId zoneId = ZoneId.systemDefault();

			long seconds = date.atZone(zoneId).toEpochSecond();
			long seconds2 = LocalDateTime.now().atZone(zoneId).toEpochSecond();

			if ((seconds2 - seconds) > this.MAXDELAY) {
				System.out.println("Primary mediator is down, so i'll take over");
				this.exceededMaxDelay = true;
				this.cancel();
			}
		}

	}

	public boolean getExceededMaxDelay() {
		return this.exceededMaxDelay;
	}

}
