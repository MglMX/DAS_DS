# DAS_DS
Repository for Distributed Systems

# How to compile and run:
	#First time doing it:
		Install python2.7 : https://www.python.org/download/releases/2.7/   INSTALL 32-Bit version!!! (x86, not x86-64)
		Install pygame for python2.7 on the client side - http://www.pygame.org/download.shtml
			So if you're using windows that would probably be the pygame-1.9.1.win32-py2.7.msi file
		Then follow the normal steps
	#Normal steps:
		Execute "python mediator.py" on the mediator side
		Execute "python mediator.py replica" on the mediator replica device
		Execute "python server.py" on each server you want. If you're running locally you have to provide different ports
		Execute "python client.py" on the client side