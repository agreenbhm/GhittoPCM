import sys
import threading
import tftpy
import socket
import time



def startTftpServer():
	#create TFTP server using defined directory for target
	tftpServer = tftpy.TftpServer(".\\")
	tftpServer.listen('0.0.0.0', 69)

#testing TFTP server

tftp = socket.gethostbyname(socket.gethostname())

serverThread = threading.Thread(target=startTftpServer)
serverThread.start()

#code to test that tftp server has started properly
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = '127.0.0.1'
port = 69
try:
	s.connect((address, port))
	print "connected to " + address
	while True:
		sys.stdout.write(".")
		sys.stdout.flush()
		time.sleep(1)
		
	#sys.exit()

#if tftp server isn't accessible
except Exception, e:
	print "TFTP server unable to start.  Exception type is " + `e`
	sys.exit()