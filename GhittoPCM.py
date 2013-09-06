import telnetlib
import sys
import time
import threading
import tftpy
import ConfigParser
import socket
import os

def main():

	global globalError
	
	#create config file parser
	config = ConfigParser.ConfigParser()
	
	#set config file as "GhittoPCM.ini" in same directory this script is in
	configFile = os.path.dirname(os.path.realpath(__file__)) + '\GhittoPCM.ini'
	
	#read from GhittoPCM.ini
	config.read(configFile)
	
	#read username & password from GhittoPCM.ini
	user = config.get('credentials', 'switchUsername')
	password = config.get('credentials', 'switchPassword')
	
	#read directory to store config files/root for TFTP server from GhittoPCM.ini
	tftpRoot = config.get('directory', 'tftpRoot')
	
	#check if tftp root folder exists, create if non-existent
	if not os.path.exists(tftpRoot):
		os.makedirs(tftpRoot)
	
	#read git username & email address from GhittoPCM.ini
	gitUser = config.get('git', 'gitUsername')
	gitEmail = config.get('git', 'gitEmail')
	
	#read full file path of switch list from GhittoPCM.ini (is it clear you must name the config file that?)
	hostFile = config.get('files', 'switchList')
	
	#check if options section exists in GhittoPCM.ini
	#if options section does exist
	if config.has_section('options') == True:
	
		#check if continueBannerSwitchListExist exists in options section
		#of continueBannerSwitchListExist does exist
		if config.has_option('options', 'continueBannerSwitchListExist'):
			#read value
			continueBannerSwitchListExist = config.get('options', 'continueBannerSwitchListExist')
			
		#if continueBannerSwitchListExist does not exist
		else:
			continueBannerSwitchListExist = "no"
	
	#if options section does not exist
	else:
		continueBannerSwitchListExist = "no"
	
	#if option to enable second list of switches (with continue banner) is set to yes
	if continueBannerSwitchListExist == "yes":
		#read full file path of second list of switches (with continue banner) from GhittoPCM.ini
		continueBannerSwitchList = config.get('files', 'continueBannerSwitchList')
	
	#ip of system running this program, for switches to upload file to
	tftp = socket.gethostbyname(socket.gethostname())
	
	#clear console & print banner
	os.system("cls")
	print "GhittoPCM v1.0.20130906\n"
	print "by AGreen BHM\n"
	print "---------------"
	print "\nStarting TFTP server..."
	
	#create separate thread for TFTP server (so it doesn't hang the program)
	serverThread = threading.Thread(target=startTftpServer, args=(tftpRoot,))
	serverThread.start()
	
	time.sleep(.1)
	
	if globalError == True:
		print "\nExiting..."
		endThreads()
	
	#wait 2 seconds before continuing
	time.sleep(.1)

	print "\nStarted"
	print "\nUsing Continue Banner switch list: " + continueBannerSwitchListExist
	print "\nConfig Directory: " + tftpRoot + "\n\n---------------\n"
	
	#go to function to read hosts and get configs
	readAndConnect(user, password, tftp, hostFile)
	
	#if second list of switches (with continue banner), re-run download using second list (and pass argument to enable)
	if continueBannerSwitchListExist == "yes":
		readAndConnect(user, password, tftp, continueBannerSwitchList, continueBannerSwitchListExist)
	
	#go to function to perform git tasks
	git(tftpRoot, gitUser, gitEmail)
	
def startTftpServer(tftpRoot):
	#create TFTP server using defined directory for target
	global globalError
	
	try:
		tftpServer = tftpy.TftpServer(tftpRoot)
		tftpServer.listen('0.0.0.0', 69)
	
	except Exception, e:
		print "\nError starting TFTP server (maybe another instance is running?)"
		print "\nError message is: " + str(e)
		globalError = True
		
def readAndConnect(user, password, tftp, hostFile, continueBannerSwitchListExist="no"):
	
	#open switch list file for reading
	hostFile = open(hostFile, "r")
	
	#read each host and perform actions, sequentially
	for host in hostFile:
	
		#remove newlines from host
		host = host.strip(' \t\n\r')
		print "\tConnecting to " + host + "..."

		#connect to host via telnet
		tn = telnetlib.Telnet(host)

		#if continue banner on switch, wait for it, then send newline (enter)
		if continueBannerSwitchListExist == "yes":
			tn.read_until("Press any key to continue")
			tn.write("\n")
		
		#parse telnet output until username
		tn.read_until("Username: ")
		
		print "\tDone"
		
		#send username & newline (enter)
		tn.write(user + "\n")
		
		#parse telnet output until password
		tn.read_until("Password: ")
		
		#send password & newline (enter)
		tn.write(password + "\n")
		
		#wait 3 seconds for switch to be ready
		time.sleep(3)
	
		#send newline character (enter) to bypass stacking screen
		tn.write("\n")
		
		#parse telnet output until ready
		tn.read_until("# ")

		#create string with config download command
		download = "copy running-config tftp %s %s.txt \n" % (tftp, host)
		
		#send command to download config
		tn.write(download)
		
		#print status message
		print "\n\tDownloading running-config from " + host + "..."
		
		#parse telnet output until done
		tn.read_until("# ")
		print "\tDone\n"
		
		#disconnect from switch
		tn.close()

def git(tftpRoot, gitUser, gitEmail):
	#set directory variables
	gitDir = tftpRoot + "\.git"
	gitDirPath = "--git-dir=\"" + gitDir + "\""
	gitWorkTree = "--work-tree=\"" + tftpRoot + "\""
	
	#write to log file
	os.system("echo %date% %time% >> \"" + tftpRoot + "\"\..\GhittoPCM.log")
	
	#if git hasn't been initialized
	if not os.path.exists(gitDir):
		os.system("git init \"" + tftpRoot + "\" >> \"" + tftpRoot + "\"\..\GhittoPCM.log")
		os.system("git " + gitDirPath + " " + gitWorkTree + " config --local user.name \"" + gitUser + "\"")
		os.system("git " + gitDirPath + " " + gitWorkTree + " config --local user.email \"" + gitEmail + "\"")
		
	#add new files to git repo
	print "---------------"
	print "\nAdding new files to repo..."
	os.system("git " + gitDirPath + " " + gitWorkTree + " add . -A >> \"" + tftpRoot + "\"\..\GhittoPCM.log")
	print "Done"
	
	#commit changes to git repo
	print "\nCommitting changes to repo..."
	os.system("git " + gitDirPath + " " + gitWorkTree + " commit -a -m \"%date% %time%\" >> \"" + tftpRoot + "\"\..\GhittoPCM.log")
	print "Done"
	os.system("echo. >> \"" + tftpRoot + "\"\..\GhittoPCM.log")
	os.system("echo. >> \"" + tftpRoot + "\"\..\GhittoPCM.log")

def endThreads():	
	#terminate TFTP server
	for thread in threading.enumerate():
		#if threads still running
		if thread.isAlive():
			try:
				#end thread
				thread._Thread__stop()
			except:
				print(str(thread.getName()) + ' could not be terminated')
	sys.exit()
	

if __name__ == '__main__':
	#execute main commands
	globalError = False
	main()
	endThreads()

