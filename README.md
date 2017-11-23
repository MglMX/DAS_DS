# DAS_DS
Repository for Distributed Systems

# How to compile and run:
	Compile all files (using eclipse or javac)

	Go to Mediator/bin folder and run rmic MediatorRemote in terminal 1
	Go to Server/bin folder and run rmic ServerRemote in terminal 2
	Go to Client/bin folder and run rmic ClientRemote in terminal 3

	Copy Server.class and ServerRemote_Stub.class in Server/bin to Mediator/bin
	Copy Client.class and ClientRemote_Stub.class in Client/bin to Mediator/bin

	Run rmiregistry 5000 in a terminal in Mediator/bin in terminal 4

	Copy Client.class and Mediator.class to Server/bin
	Copy Server.class Mediator.class to Client/bin

	Run java MediatorRemote in terminal 1
	Run java ServerRemote in terminal 2
	Run java ClientRemote in terminal 3
