from socket import *
from sys import argv
import threading


defaultHost = "cyberlab.pacific.edu"
portnum = 12000
buffsize = 2048

def connect():
    # Prompt for server host name and port number
    defaultHost = raw_input("Server Hostname: ")
    portnum = raw_input("Server Port Number: ")

    #attempt to get IP of hostname and connect
    try:
        dest = gethostbyname(defaultHost)
    except:
        errno, errstr = msg.args
        print("\n" + dest)
        return
    print ("Connected to " + dest + ":" + portnum)
    addr = (dest, int(portnum))
    s = socket()
    res = s.connect_ex(addr)

    if res != 0:
        print ("Connect to", addr, "on port", portnum, "failed")

    #send HELLO to begin talking to server
    try:
        s.send("HELLO\n")
    except:
        print("err")
        return
    #wait for HELLO to be received from server
    msg = s.recv(buffsize)
    if (len(msg) > 0) and msg == "HELLO\n":
        print ("Connected!")
    else:
        print("Connection Failed")
        return

    #login loop
    loggingIn = True
    while (loggingIn == True):
        #prompt user/pass and construct auth string
        username = raw_input("Username: ")
        password = raw_input("Password: ")
        auth = "AUTH:" + username + ":" + password + "\n"
        try:
            s.send(auth)
        except:
            print("Connection to server lost")
            return

        #sent auth string and wait for AUTHYES. Exit loop if AUTHYES is received
        msg = s.recv(buffsize)
        if (len(msg) > 0) and msg == "AUTHYES\n":
            print ("Login Successful!")
            loggingIn = False
        else:
            print("Invalid username or password")

    # receive SIGNIN:USER string and parse
    msg = s.recv(buffsize)
    if (len(msg) > 0):
        msg = msg.strip('\n');
        msg = msg.split(":")
        print ("Logged in as " + msg[1] + "\n")
    else:
        print("err")
        return

    #create and start thread for receiver
    recv = receiver(1, "receive", s)
    recv.start();

    #loop for prompts
    while 1:
        print ("Choose an Option")
        print ("1. List Online Users")
        print ("2. Send someone a message")
        print ("3. Sign off")

        #wait for option to be entered
        option = int(raw_input("") or 0)

        #send LIST for getting online users
        if option == 1:
            s.send("LIST\n")

        #Construct message string for sending user message and send
        elif option == 2:
            user = (raw_input("User you would like to message: ") or "null")
            message = (raw_input("Message: ") or "null")
            pkt = "TO:" + user + ":" + message + "\n"
            s.send(pkt)
        #tell receiver to close connection
        elif option == 3:
            recv.close()
            return

        else:
            print ("Invalid option")



class receiver(threading.Thread):
    listening = True
    #initialize receiver
    def __init__(self, threadID, name, s):
        threading.Thread.__init__(self)
        self.name=name
        self.threadID = threadID
        self.listening=True
        self.s = s
    #run the receiver
    def run(self):
        #continue listening until cancelled
        while (self.listening == True):
            #exit listener when prompted
            if (self.listening == False):
                return

            data = self.s.recv(buffsize)
            if (len(data) > 0):
                #remove colins and newlines
                data = data.strip('\n');
                data = data.split(":")
                #print data
                #print when SIGNIN is received
                if (data[0] == "SIGNIN"):
                    signinText = "User " + data[1] + " has signed in"
                    print (signinText)

                #print when a message is received
                elif (data[0] == "FROM"):
                    print ("Message from " + data[1] + ":")
                    print (data[2])

                #print when SIGNOFF is received
                elif (data[0] == "SIGNOFF"):
                    print ("User " + data[1] + " has signed off")

                #every other message is a response from a LIST request
                else:
                    print ("Online Users:")
                    for users in data:
                        print (users)

    #close receiver
    def close(self):
        #set listening to false, send BYE to log out and close socket
        self.listening = False
        self.s.send("BYE\n")
        self.s.close()

connect()
