#importing required libraries
import socket
import threading
import os
from inputimeout import inputimeout , TimeoutOccurred
from termcolor import colored

#initializing host, port, and variables to be used in the code
host = socket.gethostbyname(socket.gethostname())
port = 5050
num_rounds = 3
round_count = 1
s = "Wrong input! You are disqualified from this round."
l = "Player disconnected. Game Over."
disconnected = False

#define a function to be run in the thread and that keeps communicating with the server
def listening():
    global run, disconnected
    response = client_socket.recv(1024)
    while response.decode()[0:4] == 'data': #in the server code, the server kept sending the players a message data to check if the connection is still active
        response = client_socket.recv(1024) #as long as the message that is being received by the clients is 'data', we keep listening for a diffrent message
    print(response.decode())
    if response.decode() == l:  #checking if the received message is the disconnection message
        disconnected = True
        os._exit(0)
    else:
        if response.decode().strip() == s:  #checking if the received message is the 'wrong input' message
            results = client_socket.recv(1024)  #to wait for the results of the round
            while results.decode()[0:4] == 'data':
                results = client_socket.recv(1024)
            if results.decode() == l:   
                print(results)
                disconnected = True
                os._exit(0)
            print(results.decode())
    run = True

#starting the socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((host, port))
    welcome_msg = client_socket.recv(1024) #receiving the welcome message
    print(welcome_msg.decode()) 

    while round_count <= num_rounds and not disconnected:
        question_msg = client_socket.recv(1024)  #in the server code, the server kept sending the players a message data to check if the connection is still active
        while question_msg.decode()[:4] == 'data':   #as long as the message that is being received by the clients is 'data', we keep listening for a diffrent message
            question_msg = client_socket.recv(1024) #receiving the random number
        print(question_msg.decode())
        if question_msg.decode() == l:  #checking if the received message is the disconnection message
            disconnected = True
            break
        run = False
        thread1 = threading.Thread(target=listening, args=())   #starting the thread to keep listening to the server
        thread1.start()
        try:            
            answer = inputimeout( prompt ="Quick!", timeout=10) #prompting the user to enter an input, with a timeout of 10 seconds
        except TimeoutOccurred:
            answer= "Timeout!" #if the player exceeded the timeout duration, the code will print 'timeout'
            print (colored(answer, "white", "on_red"))
        if not disconnected:
            client_socket.sendall(answer.encode())  #sending the player's answer to the server
            round_count += 1
        else:
            break
        thread1.join()  #wait until the thread ends

    if not disconnected:
        print(colored(client_socket.recv(1024).decode(),"light_blue"))  #displaying the winner player
        print("Game is over. Hope you enjoyed it!") #printing the 'Game Over' message (ending message)