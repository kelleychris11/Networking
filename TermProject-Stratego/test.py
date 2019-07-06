"""
Text gui for testing of client and server
"""
import os
from client import Client

# client = Client("54.193.77.230", 5393)
client = Client("127.0.0.1", 5393)

# This is mainly to test the client and server using text gui

while True:
    command = input("Enter command: ").lower()
    os.system('clear')
    if command == "connect":
        client.connect()
    if command == "disconnect":
        client.disconnect()
    if command == "list":
        rooms = client.listRooms()
        for room in rooms:
            print(room.roomID)
            print(room.username)
    if command == "create":
        client.createRoom()
    if command == "join":
        roomid = input("Enter roomID: ")
        if client.joinRoom(roomid):
            print("Joined Room")
        else:
            print("Failed to join room")
    if command == "leave":
        if client.leaveRoom():
            print("Leaved Room")
        else:
            print("Failed to leave room")
    if command == "rename":
        client.changeName(input("Enter new name: "))
        print("Changed name")
    if command == 'send':
        send = input("Enter Protocol: ")
        print(send)
        print(client.sendCommand(send))
    if command == 'recv':
        print(client.recvCommand())
    if command == 'check':
        print(client.isOpponentConnected())
    if command == "exit":
        break
