# DAS_DS
Repository for Distributed Systems

# How to compile and run:
	Compile all files (using eclipse or javac)

	Go to Mediator/bin folder and run rmic MediatorRemote in terminal 1
	Go to Server/bin folder and run rmic ServerRemote in terminal 2

	Copy Server.class and ServerRemote_Stub.class in Server/bin to Mediator/bin

	Run rmiregistry 5000 in a terminal in Mediator/bin in terminal 3

	Run java MediatorRemote in terminal 1
	Run java ServerRemote in terminal 2
