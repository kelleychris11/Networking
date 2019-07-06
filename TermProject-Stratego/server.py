"""
This module contains the various classes used for the Stratego server.
"""
from enum import IntEnum
import socket
import threading
import json


class ServerProtocol(IntEnum):
    """
    ServerProtcol is an enum of the possible server commands
    """
    DISCONNECT = 1
    CREATE_ROOM = 2
    JOIN_ROOM = 3
    LEAVE_ROOM = 4
    GET_ROOMS = 5
    CHANGE_NAME = 6
    SEND_COMMAND = 7
    RECV_COMMAND = 8
    CHECK_OPPONENT = 9


class ResponseType(IntEnum):
    """
    ResponseType is an enum of possible types of responses
    """
    FAILURE = 0
    SUCCESS = 1


class Response():
    """
    Represents response messages to commands
    """

    def __init__(self, code=0, data=""):
        """
        Response constructor
        """
        self.code = code
        self.data = data

    def readJson(self, j):
        """
        Creates response from json
        """
        dict = json.loads(j)
        self.__init__(dict['code'], dict['data'])


class Command:
    """
    Represents commands that can be sent to server
    """

    def __init__(self, code=0, args=""):
        """
        Command constructor
        """
        self.code = code
        self.args = args

    def readJson(self, j):
        """
        Creates command from json
        """
        dict = json.loads(j)
        self.__init__(dict['code'], dict['args'])


class Room():
    """
    Represent server game room
    """

    def __init__(self, roomID,  name):
        self.roomID = roomID
        self.name = name
        self.users = []
        self.isJoinable = True

    def getSize(self):
        """
        Returns the amount of users inside the room
        """
        return len(self.users)

    def getOtherUser(self, user):
        """
        Returns the other user in room
        """
        if self.getSize() < 2:
            return None
        for otherUser in self.users:
            if otherUser is not user:
                print(otherUser.name)
                return otherUser
        return None

    def toJson(self):
        return {'roomID': self.roomID, 'name': self.name,
                'user': self.users[0]}


class User():
    """
    Represents user in server
    """

    def __init__(self, name, sock):
        self.name = name
        self.sock = sock
        self.room = None
        self.commandBuf = None


class Server():
    """
    Server
    """

    def __init__(self, port):
        """
        Server Constructor, sets port and binds socket to port
        """
        self.lock = threading.Lock()
        self.nextRoomId = 0
        self.users = []  # All users in server
        self.rooms = []  # All rooms in server
        self.port = port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind(('', self.port))

    def start(self):
        """
        Starts server, begins to listen for client connections
        """
        self.serverSocket.listen(50)
        while True:
            conn, addr = self.serverSocket.accept()
            thread = threading.Thread(target=self.connect, args=(conn,))
            thread.start()

    def connect(self, sock):
        """
        Creates user for connection, deletes user and close socket at end
        """
        user = User("User", sock)
        self.users.append(user)
        self.userService(user)
        user.sock.close()
        if user.room is not None:
            self.leaveRoom(user)
        self.users.remove(user)

    def sendResponse(self, user, response):
        """
        Sends response to given user
        """
        user.sock.send(json.dumps(response.__dict__).encode())

    def userService(self, user):
        """
        Receive and process commands from user until exit
        """
        while True:
            try:
                # Get command json from client
                msg = user.sock.recv(1024).decode()
            except socket.error:
                break
            if msg == '':  # User has disconnected
                break
            command = Command()  # Need to create object before read json
            command.readJson(msg)  # Turn command json into command object
            if command.code == ServerProtocol.DISCONNECT:
                self.sendResponse(user, Response(ResponseType.SUCCESS))
                break
            response = self.processCommand(command, user)
            self.sendResponse(user, response)

    def processCommand(self, command, user):
        """
        Performs action depending on command passed
        """
        if command.code == ServerProtocol.CREATE_ROOM:
            return self.createRoom(user)
        if command.code == ServerProtocol.JOIN_ROOM:
            return self.joinRoom(user, self.findRoom(command.args))
        if command.code == ServerProtocol.LEAVE_ROOM:
            return self.leaveRoom(user)
        if command.code == ServerProtocol.GET_ROOMS:
            return self.getRooms()
        if command.code == ServerProtocol.CHANGE_NAME:
            return self.changeName(user, command.args)
        if command.code == ServerProtocol.SEND_COMMAND:
            return self.sendCommand(user, command.args)
        if command.code == ServerProtocol.RECV_COMMAND:
            return self.recvCommand(user)
        if command.code == ServerProtocol.CHECK_OPPONENT:
            return self.checkOpponent(user)
        return Response(ResponseType.FAILURE, "Unknown Command")

    def findRoom(self, roomID):
        """
        Finds and returns the room with the given id
        """
        for room in self.rooms:
            if room.roomID == int(roomID):
                return room
        return None

    def createRoom(self, user):
        """
        Creates room and adds user to room
        """
        if user.room is not None:
            return Response(ResponseType.FAILURE, "User already in room")
        self.lock.acquire()
        room = Room(self.nextRoomId, "Room " + str(self.nextRoomId))
        self.nextRoomId += 1
        self.lock.release()
        self.joinRoom(user, room)
        self.rooms.append(room)  # Add room to list
        return Response(ResponseType.SUCCESS)

    def joinRoom(self, user, room):
        """
        Adds user to room
        """
        self.lock.acquire()
        if room is None or not room.isJoinable or user.room is not None:
            self.lock.release()
            return Response(ResponseType.FAILURE)
        user.room = room
        room.users.append(user)
        if room.getSize() >= 2:
            room.isJoinable = False
        self.lock.release()
        return Response(ResponseType.SUCCESS)

    def leaveRoom(self, user):
        """
        Remove user from room
        """
        if user.room is None:
            return Response(ResponseType.FAILURE, "User in not in a room")
        user.room.users.remove(user)
        if user.room.getSize() <= 0:  # Remove room if empty
            self.rooms.remove(user.room)
        user.room = None
        user.commandBuf = None
        return Response(ResponseType.SUCCESS)

    def getRooms(self):
        """
        Returns list of avaliable rooms
        Response needs rework
        """
        message = []
        for room in self.rooms:
            if room.isJoinable:
                message.append(
                    {'roomID': room.roomID, 'username': room.users[0].name})
        return Response(ResponseType.SUCCESS, message)

    def changeName(self, user, name):
        """
        Change user name
        """
        user.name = name
        return Response(ResponseType.SUCCESS)

    def sendCommand(self, user, command):
        """
        Sends command to user
        """
        # Check if user is in valid room
        if user.room is None or user.room.getOtherUser(user) is None:
            return Response(ResponseType.FAILURE, "Not in valid room")
        otherUser = user.room.getOtherUser(user)
        # print(command)
        # send = Response(ResponseType.SUCCESS, command)
        # self.sendResponse(otherUser, send)
        otherUser.commandBuf = command
        return Response(ResponseType.SUCCESS)

    def recvCommand(self, user):
        """
        Receive command currently in users buffer
        Returns a failed response if buffer is empty
        """
        if user.commandBuf is None:
            return Response(ResponseType.FAILURE, '')
        msg = user.commandBuf
        user.commandBuf = None
        return Response(ResponseType.SUCCESS, msg)

    def checkOpponent(self, user):
        """
        Checks if users opponent is still connected to room
        """
        return Response(int(
            user.room is not None and user.room.getSize() >= 2))


if __name__ == "__main__":
    server = Server(5393)
    server.start()
