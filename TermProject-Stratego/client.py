"""
Client module
"""
import socket
from server import ServerProtocol, Command, ResponseType, Response
import json


class RoomEntry:
    """
    RoomEntry represents avaliable rooms that user can join
    """

    def __init__(self, roomID=-1, username=""):
        self.roomID = roomID
        self.username = username

    def readJson(self, jso):
        """
        Creates response from json
        """
        dict = json.loads(jso)
        self.__init__(dict['roomID'], dict['username'])


class Client:
    """
    Client is able to connect and send commands to the server
    """
    def __init__(self, serverIp, port):
        """
        Client Constructor
        """
        self.sock = None
        self.serverIp = serverIp
        self.port = port
        self.isConnected = False

    def send(self, command):
        """
        Send command to server, return response
        """
        # Sends command json to server
        if not self.isConnected:
            return Response(ResponseType.FAILURE, "")
        self.sock.send(json.dumps(command.__dict__).encode())

        response = Response(ResponseType.FAILURE)
        jso = self.sock.recv(1024).decode()
        response.readJson(jso)  # Turns json response into response object
        return response

    """
    --- Should only need the commands below for the gui ---
    --- Each of the below methods sends the corresponding command to server ---
    """
    def connect(self):
        """
        Connect to the server
        """
        if self.isConnected:
            return False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.serverIp, self.port))
        self.isConnected = True
        return True

    def disconnect(self):
        """
        Disconnect from the server
        """
        # command = Command(ServerProtocol.DISCONNECT)
        # self.send(command)
        if not self.isConnected:
            return False
        self.sock.close()
        self.isConnected = False
        return True

    def changeName(self, name):
        """
        Sends command to change user name
        """
        command = Command(ServerProtocol.CHANGE_NAME, name)
        return bool(self.send(command).code)  # Returns true or false

    def listRooms(self):
        """
        Sends command to get response with list of avaliable rooms to join
        """
        rooms = []
        command = Command(ServerProtocol.GET_ROOMS)
        response = self.send(command)  # Returns json of room list
        if response.code:
            for jso in response.data:
                entry = RoomEntry(jso['roomID'], jso['username'])
                rooms.append(entry)
        return rooms

    def joinRoom(self, roomID):
        """
        Sends command to join the room with the given id
        """
        command = Command(ServerProtocol.JOIN_ROOM, roomID)
        return bool(self.send(command).code)  # Returns true or false

    def leaveRoom(self):
        """
        Sends command to leave current room
        """
        command = Command(ServerProtocol.LEAVE_ROOM)
        return bool(self.send(command).code)  # Returns true or false

    def createRoom(self):
        """
        Sends command to create room
        """
        command = Command(ServerProtocol.CREATE_ROOM)
        return bool(self.send(command).code)  # Returns true or false

    def sendCommand(self, jso):
        """
        Sends game protocol command to other user in current room
        """
        command = Command(ServerProtocol.SEND_COMMAND, jso)
        return bool(self.send(command).code)

    def recvCommand(self):
        """
        Receives game protocol command from other user in current room
        Returns an empty string if there is nothing to receive
        """
        command = Command(ServerProtocol.RECV_COMMAND)
        # response = Response(ResponseType.FAILURE)
        # jso = self.sock.recv(1024).decode()
        # print(jso)
        # response.readJson(jso)  # Turns json response into response object
        return self.send(command).data

    def isOpponentConnected(self):
        """
        Returns true if opponnent is connected to the user's room
        """
        command = Command(ServerProtocol.CHECK_OPPONENT)
        return bool(self.send(command).code)
