from socket import *
from sys import argv
import threading
import time

DEFAULT_PORTNUM= 54333
buffsize = 2048

# Usernames and passwords
users = dict([('test1', 'p000'), ('test2', 'p000'), ('test3', 'p000')])
#list of online users
online = []

def talk():

    #check parameters for a port number to use. If none is provided, use default port number
    if len(argv) == 2 and int(argv[1]) < 65535:
        portnum = int(argv[1])
    else:
        portnum = DEFAULT_PORTNUM
        print "Usage: python", argv[0], "[port number]"
        print "Running", argv[0], "on port", DEFAULT_PORTNUM, "instead"
    host = 'localhost'
    hostIP = gethostbyname(host)
    addr = (hostIP, portnum)
    s = socket()
    s.bind(addr)
    s.listen(5)

    print "Listening on", hostIP, portnum

    while True:
        #accept connections
        con, retaddr = s.accept()
        print "Connected to", retaddr[0], "on port", retaddr[1]

        #start new thread to listen at every connection
        recv = listener(1, "Listener", s, con, retaddr)
        recv.start()


class listener(threading.Thread):
    username = ""
    def __init__(self, threadID, name, s, con, retaddr):
        threading.Thread.__init__(self)
        self.name=name
        self.threadID = threadID
        self.con = con
        self.retaddr = retaddr
        self.s = s
        self.listening = True
    def run(self):
        print ("Started thread")
        msg = self.con.recv(buffsize)

        #Listen for HELLO and reply with HELLO.
        if (len(msg) > 0 and msg == 'HELLO\n'):
            print "received", msg
            self.con.send("HELLO\n")
        else:
            self.s.close()

        # Login Loop
        loggingIn = True
        while loggingIn == True:

            msg = self.con.recv(buffsize)
            if (len(msg) > 0):

                #split string by colins and remove newline
                msg = msg.strip("\n")
                msg = msg.split(":")
                print "received", msg

                if (msg[0] == "AUTH"):
                    self.username = msg[1]
                    pw = msg[2]
                    #check if username and password matches
                    if self.username in users and pw == users[self.username]:
                        self.con.send("AUTHYES\n")
                        online.append([self.username, self.con])
                        print online
                        loggingIn = False
                        break;
                    else:
                        self.con.send("AUTHNO\n")
                else:
                    self.con.send("AUTHNO\n")

        time.sleep(.1)
        # send SIGNIN notification to every user
        broadcast("SIGNIN:" + self.username)

        # Listen for message and respond accordingly
        while (self.listening):
            msg = self.con.recv(buffsize)
            if len(msg) > 0:
                print "received", msg, "from", self.username
                # remove newlines
                msg = msg.strip("\n")

                #if LIST is received, grab list of all online users and send
                if msg == "LIST":
                    uniqueUsers = []
                    for user in online:
                        if user[0] not in uniqueUsers:
                            uniqueUsers.append(user[0])
                    list = " ".join(uniqueUsers)
                    self.con.send(list)

                #if BYE is received, send SIGNOFF to all users and close connection
                elif msg == "BYE":
                    broadcast("SIGNOFF:" + self.username)
                    userdata = [self.username, self.con]

                    online.remove(userdata)
                    self.s.close()

                #otherwise, send a message to a specified user
                else:
                    try:
                        msg = msg.split(":")
                        # username to send to
                        sendto = msg[1]
                        # contents of the message to send
                        data = msg[2]

                        sendmsg = "FROM:" + self.username + ":" + data

                        # grab connection data from online using username
                        for user in online:
                            if user[0] == sendto:
                                con = user[1]
                        # gemerage message and send
                                sendmsg = "FROM:" + self.username + ":" + data
                                con.send(sendmsg)
                    except:
                        print "unable to send message to" , sendto

# function to send a message to all online users
def broadcast(msg):
    for user in online:
        print user
        print "sending" , msg, "to", user[0]
        con = user[1]
        con.send(msg + "\n")
talk()