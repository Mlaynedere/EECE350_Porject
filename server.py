#Group8:
#Dany Solh contributed to the server client class, as well as a small part of the game logic.
#Hussein Mallah focused mainly on the game logic and dealing with the players.
#Lana Noura worked on the thread part in the client code.
#Alaa Khanafer worked on the other part of the client code, and on adding music and colors.
#Other features and handling errors were worked on by all members together during online & in-person meetings.

#importing required libraries
import socket
import time
import random
import threading
import pygame  # for playing music
from termcolor import colored  # for printing colored text

#Creating a client (player) class to be used in the code
class client(object):
    #initialize the client
    def __init__(self, number, conn, addr):
        self.number = number
        self.points = 0
        self.cumulative_score = 0
        self.conn = conn
        self.addr = addr
        self.timer = 0
        self.RTT = 0
        self.result = None
        self.qualified = False

    #send a welcome message to the client
    def welcome(self):
        s = "Welcome to the game!! You are Player" + str(self.number) + " Waiting for additional players to enter"
        self.conn.send(s.encode())

    #send a random number to the client and starting the timer for each player
    def send_number(self, generated_num):
        self.RTT = 0
        self.qualified = False
        num = "The number is: " + str(generated_num)
        self.conn.send(num.encode())
        self.timer = time.time()
        
    #receive the client's response and getting his RTT
    def receive_result(self, generated_number):
        self.result = self.conn.recv(1024).decode()
        self.RTT = time.time() - self.timer
        try:
            self.result = int(self.result)  #checking the correctness of the client's response
            if self.result == generated_number:
                self.qualified = True
        except:
            pass

#define a function to be used by the thread to check the connection status of the clients
def check_connection():
    global players, disconnect
    while run:
        try:    #sending a test message to each client to check their connection status
            players[0].conn.send('data'.encode())
            players[1].conn.send('data'.encode())
            players[2].conn.send('data'.encode())
        except:
            disconnect = True
            for k in players:
                try:
                    #if a player was disconnected, the server sends this message, ends the game and closes the connections
                    k.conn.send("Player disconnected. Game Over.".encode())
                    k.conn.close()
                except ConnectionResetError:
                    k.conn.close()
            break
        time.sleep(1)

#This the part wich enables the music in the game
pygame.init()
pygame.mixer.music.load(r"C:\Users\Owner\Downloads\Darude - Sandstorm.mp3")
pygame.mixer.music.play()

#create a socket connection
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((socket.gethostbyname(socket.gethostname()), 5050))
players = []
RTTs = []
run = True
disconnect = False

server.listen()
print("Waiting for players to connect...")

#waiting for all the players to connect
while len(players) < 3:
    conn, addr = server.accept()
    x = client(len(players)+1, conn, addr)
    x.welcome()
    players.append(x)

print("All players have joined the game!\n")

#starting the function we stated ealier inside of a thread
thread1 = threading.Thread(target=check_connection, args=())
thread1.start()

try:
    # function to send the scores to the players
    def send_scores(round):  
        players.sort(key=lambda y: y.cumulative_score)  #sorting the players according to the cumulative score
        r = "Round " + str(round) + "\n"
        s = colored( "Player         Points       Cumulative score" , "black", "on_white")
        l = colored( f"\n{players[2].number}  \t\t {players[2].points}   \t\t {players[2].cumulative_score} \n", "light_red")
        m = colored( f"{players[1].number}  \t\t {players[1].points}   \t\t {players[1].cumulative_score} \n", "light_red")
        n = colored( f"{players[0].number}  \t\t {players[0].points}   \t\t {players[0].cumulative_score} \n", "light_red")
        msg = r+s+l+m+n
        for j in range(3):
            players[j].conn.send(msg.encode())
        players.sort(key=lambda y: y.number)    #sorting the players according to their numbers to get original list back


    for i in range(3):
        RTTs = []
        random_num = random.randint(0, 9)  # generating random number between 0 and 9
        for j in range(3):  # loop to send the number to players, receive their answer, and check if they are qualified
            players[j].send_number(random_num) #sending the number to the player
            players[j].receive_result(random_num) #reciving response from the player
            if not players[j].qualified:    # handling the case where the player is not qualified due to timeout or wrong input
                if players[j].result != "Timeout":  
                    players[j].conn.send("Wrong input! You are disqualified from this round.".encode())
                    players[j].points = 0
                    continue
            RTTs.append(players[j].number-1)

        if len(RTTs) == 1:  # checking which player has the lowest RTT for the cases where 1, 2, or 3 players qualified
            players[RTTs[0]].points = 2
            players[RTTs[0]].cumulative_score += 2
        elif len(RTTs) == 2:
            if players[RTTs[0]].RTT > players[RTTs[1]].RTT:
                players[RTTs[0]].points = 2
                players[RTTs[0]].cumulative_score += 2
                players[RTTs[1]].points = 1
                players[RTTs[1]].cumulative_score += 1
            else:
                players[RTTs[1]].points = 2
                players[RTTs[1]].cumulative_score += 2
                players[RTTs[0]].points = 1
                players[RTTs[0]].cumulative_score += 1
        elif len(RTTs) == 3:
            players.sort(key=lambda y: y.RTT)  # to get lowest RTT in simple way, sort the players according to their RTT
            for j in range(3):
                players[j].points = 2-j  # set player score for this round. Player can receive 2, 1, or 0 points.
                players[j].cumulative_score += 2-j  # increase player cumulative score by received points
            players.sort(key=lambda y: y.number)  # sort the players according to their number to get back original player list
        send_scores(i+1)     # sending the scores to the players after each round

    players.sort(key=lambda y: y.cumulative_score)  # sorting the players in terms of their cumulative score to get winne
    s1 = "Player " + str(players[2].number) + " won the game."
    for k in players:  # send to players who is the winner
        k.conn.send(s1.encode())
        k.conn.close()
    run = False
except:  # in case of error, send to players that the game is over
    if not disconnect:
        for k in players:
            try:
                print('sent')
                k.conn.send("Player disconnected. Game Over.".encode())
                k.conn.close()
            except ConnectionResetError:
                k.conn.close()
    run = False

#stopping the thread
thread1.join()
pygame.mixer.music.stop()   #stop the music
