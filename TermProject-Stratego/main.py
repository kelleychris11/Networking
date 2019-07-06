
import tkinter
import functools
import sys
from functools import partial
from tkinter import messagebox
from tkinter import *
import json
import time
import random
import client
from client import Client

#class to send JSON player move to server
class SendAction:
    def __init__(self, action, fromRow, fromCol, toRow, toCol):
        self.action = action
        self.fromRow = fromRow
        self.fromCol = fromCol
        self.toRow = toRow
        self.toCol = toCol

#class for receiving JSON move from opponent
class Action:
    def __init__(self, jsonString):
        self.__dict__ = json.loads(jsonString)

#holds tile information
class Item:
     def __init__(self, tileType, tileValue, displayValue):
         self.tileType = tileType
         self.tileValue = tileValue
         self.displayValue = displayValue


#First Window on game start -- accepts user name
class Register:

    username = ""
    loginWindow = Tk()
    loginInfoString = ""
    loginInfo = None

    #submit username
    def loginOnClick(self, username):
        if username == "":
            self.loginInfoString = "Username must contain characters"
            self.loginInfo.config(text=self.loginInfoString)
            self.loginWindow.update()
            return
        if len(username) > 20:
            self.loginInfoString = "Username must be less than 20 characters"
            self.loginInfo.config(text=self.loginInfoString)
            self.loginWindow.update()
            return

        self.username = username
        self.loginWindow.quit()
        self.loginWindow.destroy()

    #create login window
    def createWindow(self):
        self.loginWindow.protocol("WM_DELETE_WINDOW", sys.exit)
        self.loginWindow.title("Register")
        self.loginWindow.geometry("300x100")
        userNameTxt = Entry(self.loginWindow)
        userNameLabel = Label(self.loginWindow, text="Enter User Name: ", font=("Helvetica", 12, "bold"))
        loginBtn = Button(self.loginWindow, font=BTN_FONT, bg="LightBlue1", borderwidth=BTN_BORDER_WIDTH, text="Submit", command=lambda: self.loginOnClick(userNameTxt.get()))
        self.loginInfo = Label(self.loginWindow, text=self.loginInfoString)
        userNameLabel.grid(row=1, column=0)
        userNameTxt.grid(row=1, column=1)
        loginBtn.grid(row=3, column=0)
        self.loginInfo.grid(row=4, column=0, columnspan=2)
        self.loginWindow.mainloop()

class WaitingRoom:
    waitingWindow = None
    waitLabel = None
    isExitWindow = False

    def __init__(self):
        self.waitingWindow = Tk()

    def exitWaitingRoom(self):
        self.isExitWindow = True


    def createWindow(self):
        #display waiting room while user is waiting for other player
        self.waitingWindow.protocol("WM_DELETE_WINDOW", self.exitWaitingRoom)
        self.waitLabel = Label(self.waitingWindow, width=50, font=BTN_FONT, height=6, text="Waiting for Your Opponent")
        self.waitLabel.grid(row=0, column=0)
        while not client.isOpponentConnected():
            if self.isExitWindow:
                self.waitingWindow.quit()
                self.waitingWindow.destroy()
                sys.exit()
            self.waitingWindow.update()

        self.waitingWindow.quit()
        self.waitingWindow.destroy()
           
#window that allows player to choose which room to join (or create)
class RoomSelect:

    roomList = []
    roomWindow = None
    roomBtnArray = None
    roomFrame = None
    isFull = False
    isFirst = False

    def __init__(self, roomList):
        self.roomWindow = Tk()
        self.roomList = roomList
        self.roomFrame = Frame(self.roomWindow, borderwidth=30)
        self.roomFrame.grid(row=1, column=0)

    #create new room, player automatically joins
    def createRoom(self):
        self.isFirst = True
        client.createRoom()
        self.roomWindow.quit()
        self.roomWindow.destroy()

    #refresh list of available rooms
    def refreshList(self):
        #send to server
        newList = client.listRooms()
        self.roomList.clear()
        for i in newList:
            self.roomList.append(i)

        #delete buttons already created
        for button in self.roomBtnArray:
            button.destroy()
        self.setRoomButtons()

    #client joins room already created
    def roomSelect(self, roomID):
        if not client.joinRoom(roomID):
            self.refreshList()
            return
        self.roomWindow.quit()
        self.roomWindow.destroy()

    #set a button for each available room
    def setRoomButtons(self):
        numRooms = len(self.roomList)
        self.roomBtnArray = [0 for x in range(len(self.roomList))]
        for i in range(numRooms):
            roomString = "ROOM: " + str(self.roomList[i].roomID) + " ---- Player: " + roomList[i].username
            roomBtn = Button(self.roomFrame, borderwidth=5, bg="light cyan", width=40, font=("Helvetica", 13, "bold"), \
                text=roomString, command=partial(self.roomSelect, self.roomList[i].roomID))
            roomBtn.grid(row=i+1, column=0)
            self.roomBtnArray[i] = roomBtn
        otherBtnFrame = Frame(self.roomWindow, borderwidth=20)
        otherBtnFrame.grid(row=2, column=0)
        spaceLabel = Label(otherBtnFrame, text=" ")
        spaceLabel.grid(row=1, column=0)
        createRoomBtn = Button(otherBtnFrame, text="Create Room ", bg="azure", width=20, \
            borderwidth=5, command=lambda: self.createRoom())
        createRoomBtn.grid(row=2, column=0)
        refreshBtn = Button(otherBtnFrame, text="Refresh List", width=15, \
            borderwidth=5, bg="green", fg="white", command=lambda: self.refreshList())
        refreshBtn.grid(row=3, column=0, columnspan=2)

    #create room select window
    def createWindow(self):
        self.roomWindow.protocol("WM_DELETE_WINDOW", sys.exit)
        roomLabel = Label(self.roomWindow, text="Select/Create Room")
        roomLabel.config(font=("Helvetica", 13, "bold"))
        roomLabel.grid(row=0, column=0, columnspan=2)

        self.setRoomButtons()
        self.roomWindow.mainloop() 

#get board setup for player and opponent
def getBoardSetup():
    #TODO send player setup to server
    #set random tile positions
    pieces = [6, 1, 8, 5, 4, 4, 4, 3, 2, 1, 1, 1]
    playerBoard = [[0 for x in range(10)] for y in range(4)]
    opponentBoard = [[0 for x in range(10)] for y in range(4)]
    board = [-1 for x in range(40)]
    for i in range(12):
        for j in range(pieces[i]):
            rand = random.randint(0, 39)
            while board[rand] != -1:
                rand = (rand + 1) % 40
            board[rand] = i
    
    #convert to JSON
    boardString = json.dumps(board)
    #send to server, get opponent board in return
    while not client.sendCommand(boardString):
        time.sleep(1)

    oppSetupString = client.recvCommand()
    while oppSetupString == "":
        time.sleep(1)
        oppSetupString = client.recvCommand()

    #convert opponent board JSON string to object
    oppBoard = json.loads(oppSetupString)

    #convert playerBoard to 2D array
    for i in range(4):
        for j in range(10):
            playerBoard[i][j] = board[i * 10 + j]
    
    #convert opponent board to 2d array
    for i in range(4):
        for j in range(10):
            opponentBoard[i][j] = oppBoard[i * 10 + j] 
    return playerBoard, opponentBoard

#Player won game -- display winning screen
def playerWonGame():
    global buttons
    for i in range(10):
        for j in range(10):
            buttons[i][j].grid_forget()
            buttons[i][j].destroy()
    frame = Frame(root)
    frame.grid(row=0,column=0)
    label = Label(frame, text="You Won!!!", font=("Helvetica", 20, "bold"), width=30, height=10)
    label.grid(row=0,column=0)
    root.update()
    time.sleep(7)
    client.disconnect()
    sys.exit()

#player lost the game -- send message to player and server
def endGamePlayerLost():
    global buttons
    for i in range(10):
        for j in range(10):
            buttons[i][j].grid_forget()
            buttons[i][j].destroy()
    frame = Frame(root)
    frame.grid(row=0,column=0)
    label = Label(frame, text="You Lost!!!", font=("Helvetica", 20, "bold"), width=30, height=10)
    label.grid(row=0,column=0)
    root.update()
    time.sleep(7)
    client.disconnect()
    sys.exit()

#check that attempted movement is acceptable
def checkMovement(row, col):
    prevRow = prevPos[0]
    prevCol = prevPos[1]
    if board[prevRow][prevCol].tileValue == 0:
        helpLabel.config(text="Can't move bombs.")
        return False
    if board[prevRow][prevCol].tileValue == 1:
        helpLabel.config(text="Can't move flags.")
        return False
    rowDiff = abs(row - prevRow)
    colDiff = abs(col - prevCol)
    if(board[row][col].tileType == PLAYER):
        helpLabel.config(text="You've got a piece there already.")
        return False
    if(((rowDiff == 1) or (colDiff == 1)) and (rowDiff + colDiff == 1) and ((row - prevRow) != 1)):
        return True
    else:
        helpLabel.config(text="Can't move that way. Only adjacent vertical or horizontal.")
        return False 

#perform game logic when player presses game tile
def btnOnClick(row, col):
    global btnClicked
    global isPlayerTurn
    turnFinished = False
    pRow = prevPos[0]
    pCol = prevPos[1]
    playerWon = False
    actionType = ""

    #check if it is the player's turn
    if not isPlayerTurn:
        helpLabel.config(text="It's not your turn, be patient...")
        return

    #no other tile clicked, this is piece to move
    if not btnClicked:
        if not roomSelect.isFirst:
            return
        if board[row][col].tileType == PLAYER:
            buttons[row][col].config(relief=SUNKEN)
            prevPos[0] = row
            prevPos[1] = col
            btnClicked = True
        else:
            return
    #check tile to move piece
    elif checkMovement(row, col):
        #if tile is unused, okay to move opponent there
        if board[row][col].tileType == UNUSED:
            buttons[row][col].config(bg=BTN_PLAYER_COLOR, text=board[pRow][pCol].displayValue)
            buttons[pRow][pCol].config(bg=BTN_UNUSED_COLOR, relief=RAISED, text="")

            # switch value of tiles
            prevTile = board[pRow][pCol]
            currTile = board[row][col]
            temp = prevTile
            board[row][col] = temp
            board[pRow][pCol] = currTile
            btnClicked = False
            turnFinished = True
            actionType = "move"
        #other tile is opponent -- attack
        elif board[row][col].tileType == OPPONENT:
            #cannot attack with bomb
            if board[pRow][pCol].tileValue == 0:
                buttons[pRow][pCol].config(relief=RAISED)
                btnClicked = False
                helpLabel.config(text="Can't attack with a bomb.")
                return
            #cannot attack with flag
            elif board[pRow][pCol].tileValue == 1:
                buttons[pRow][pCol].config(relief=RAISED)
                btnClicked = False
                helpLabel.config(text="Can't attack with the flag.")
                return
            #flash attacking tiles
            for i in range(10):
                if i % 2 == 0:
                    buttons[row][col].config(bg=BTN_FLASH_COLOR, text=board[row][col].displayValue)
                    buttons[pRow][pCol].config(bg=BTN_FLASH_COLOR)
                    root.update()
                    time.sleep(.3)
                else:
                    buttons[row][col].config(bg=BTN_ENEMY_COLOR)
                    buttons[pRow][pCol].config(bg=BTN_PLAYER_COLOR)
                    root.update()
                    time.sleep(.3)

            #hide opponent tile value
            buttons[row][col].config(text="")

            #bomb attacked -- this piece gets destroyed
            if(board[row][col].tileValue == 0):
                board[pRow][pCol].tileType = UNUSED
                buttons[pRow][pCol].config(bg=BTN_UNUSED_COLOR, text="")    
            #flag attacked -- player wins the game            
            elif(board[row][col].tileValue == 1):
                playerWon = True
            elif(board[pRow][pCol].tileValue > board[row][col].tileValue):
                #player wins attack
                board[row][col].tileType = UNUSED
                buttons[row][col].config(bg=BTN_UNUSED_COLOR, text="")
            else:
                #player loses the attack
                board[pRow][pCol].tileType = UNUSED
                buttons[pRow][pCol].config(bg=BTN_UNUSED_COLOR, text="")

            buttons[pRow][pCol].config(relief=RAISED)
            btnClicked = False
            turnFinished = True
            actionType = "attack"
        else:
            buttons[pRow][pCol].config(relief=RAISED)
            btnClicked = False
            turnFinished = True
    else:
        buttons[pRow][pCol].config(relief=RAISED)
        btnClicked = False
    
    #turn is finished, send move to server
    if turnFinished:
        sendAction = SendAction(actionType, pRow, pCol, row, col)
        actionString = json.dumps(sendAction.__dict__)
        root.update()
        client.sendCommand(actionString)
        turnFinished = False
        if playerWon:
            playerWonGame()
        else:
            endTurn()

#place game pieces (buttons)
def placeButtons(player, opp):
    buttons = [[0 for x in range(10)] for y in range(10)]
    board = [[0 for x in range(10)] for y in range(10)]
    #setup opponent pieces
    for i in range(4):
        for j in range(10):
            btn = Button(rightFrame, bg=BTN_ENEMY_COLOR, width=BTN_WIDTH, \
                         height=BTN_HEIGHT, borderwidth=BTN_BORDER_WIDTH, font=BTN_FONT)
            btn.grid(row=i, column=j)
            buttons[i][j] = btn
            displayValue = opp[i][j]
            if opp[i][j] == 1:
                displayValue = 'F'
            if opp[i][j] == 0:
                displayValue = 'B'
            item = Item(OPPONENT, opp[i][j], displayValue)
            board[i][j] = item

    #set center buttons -- initially unused
    for i in range(2):
        for j in range(10):
            btn = Button(rightFrame, bg=BTN_UNUSED_COLOR, width=BTN_WIDTH, height=BTN_HEIGHT, \
                font=BTN_FONT, borderwidth=BTN_BORDER_WIDTH)
            btn.grid(row=i + 4, column=j)
            buttons[i + 4][j] = btn
            item = Item(UNUSED, 0, 0)
            board[i + 4][j] = item

    #set player buttons
    for i in range(4):
        for j in range(10):
            btn = Button(rightFrame, text=player[i][j], bg=BTN_PLAYER_COLOR, width=BTN_WIDTH, height=BTN_HEIGHT, borderwidth=BTN_BORDER_WIDTH, font=BTN_FONT)
            btn.grid(row=i + 6, column=j)
            buttons[i + 6][j] = btn
            displayValue = player[i][j]
            if player[i][j] == 1:
                displayValue = 'F'
            if player[i][j] == 0:
                displayValue = 'B'
            item = Item(PLAYER, player[i][j], displayValue)
            btn.config(text=displayValue)
            board[i + 6][j] = item
    return buttons, board

#set onclick command for game pieces (buttons)
def setOnClick():
    for i in range(10):
        for j in range(10):
            buttons[i][j].config(command=partial(btnOnClick, i, j))

#move opponent (from action received from server)
def moveOpponent(fromRow, fromCol, toRow, toCol):
    buttons[fromRow][fromCol].config(bg=BTN_UNUSED_COLOR, relief=RAISED, text="")
    buttons[toRow][toCol].config(bg=BTN_ENEMY_COLOR, text="")
    #flip from/to tile values
    prevTile = board[fromRow][fromCol]
    currTile = board[toRow][toCol]
    board[toRow][toCol] = prevTile
    board[fromRow][fromCol] = currTile

#opponent attacks (from action received fro server)
def opponentAttack(fromRow, fromCol, toRow, toCol):

    #flash attacking tiles
    for i in range(10):
        if i % 2 == 0:
            buttons[fromRow][fromCol].config(bg=BTN_FLASH_COLOR, text=board[fromRow][fromCol].displayValue)
            buttons[toRow][toCol].config(bg=BTN_FLASH_COLOR)
            root.update()
            time.sleep(.3)
        else:
            buttons[fromRow][fromCol].config(bg=BTN_ENEMY_COLOR)
            buttons[toRow][toCol].config(bg=BTN_PLAYER_COLOR)
            root.update()
            time.sleep(.3)

    #hide opponent tile value
    buttons[fromRow][fromCol].config(text="")

    #check if attacking a bomb -- immediate death
    if(board[toRow][toCol].tileValue == 0):
        board[fromRow][fromCol].tileType = UNUSED
        buttons[fromRow][fromCol].config(bg=BTN_UNUSED_COLOR, text="")
    #check if attacking the flag -- win state        
    elif(board[toRow][toCol].tileValue == 1):
        endGamePlayerLost()
    #check if opponent wins attack
    elif(board[fromRow][fromCol].tileValue > board[toRow][toCol].tileValue):
        board[toRow][toCol].tileType = UNUSED
        buttons[toRow][toCol].config(bg=BTN_UNUSED_COLOR, text="")
    #opponent loses attack
    else:
        board[fromRow][fromCol].tileType = UNUSED
        buttons[fromRow][fromCol].config(bg=BTN_UNUSED_COLOR, text="")


#used for translating from player side to opponent side of board
def translateRow(row):
    switch = {0:9, 1:8, 2:7, 3:6, 4:5, 5:4, 6:3, 7:2, 8:1, 9:0}
    return switch.get(row)

#used for translating from plaer side to opponent side of board
def translateColumn(col):
    switch = {0:9, 1:8, 2:7, 3:6, 4:5, 5:4, 6:3, 7:2, 8:1, 9:0}
    return switch.get(col)
    
#end turn logic, wait for move from opponent (through server)
def endTurn():
    statusLabel.config(text="Opponent's Turn")
    global isPlayerTurn
    global isExitGame
    isPlayerTurn = False
    jsonOppMove = client.recvCommand()

    #keep checking server for input (nonblocking socket)
    while jsonOppMove == "":
        #exit game was triggered by this client
        if isExitGame:
            client.disconnect()
            sys.exit()
        #exit game was triggered by other client
        if not client.isOpponentConnected():
            messagebox.showerror("Player Left", "The Player Left the Game. You Win.")
            client.disconnect()
            sys.exit()
        root.update()
        jsonOppMove = client.recvCommand()

    #convert opponent action received to object    
    oppMove = Action(jsonOppMove)
    #translate tiles from player side to opponent side
    fromRow = translateRow(oppMove.fromRow)
    fromCol = translateColumn(oppMove.fromCol)
    toRow = translateRow(oppMove.toRow)
    toCol = translateColumn(oppMove.toCol)

    #check if player action type
    if(oppMove.action == "move"):
        moveOpponent(fromRow, fromCol, toRow, toCol)
    elif(oppMove.action == "attack"):
        opponentAttack(fromRow, fromCol, toRow, toCol)
    roomSelect.isFirst = True
    isPlayerTurn = True
    statusLabel.config(text="Your Turn")
    helpLabel.config(text="")

#translate opponent initial board piece (rotate to other side of board)
def translateIntialBoardRow(row):
    switch = {3:0, 2:1, 1:2, 0:3}
    return switch.get(row)

#translate opponent initial board piece (rotate to other side of board)
def translateInitialBoardCol(col):
    switch = {0:9, 1:8, 2:7, 3:6, 4:5, 5:4, 6:3, 7:2, 8:1, 9:0}
    return switch.get(col)

#translate opponent board pieces (rotate to other side of board)
def translateBoard(oppSetup):
    newOppSetup = [[0 for x in range(10)] for y in range(4)]
    for i in range(4):
        for j in range(10):
            row = translateIntialBoardRow(i)
            col = translateInitialBoardCol(j)
            newOppSetup[row][col] = oppSetup[i][j]

    return newOppSetup

#player triggered exit game
def exitGame():
    global isExitGame
    isExitGame = True
    client.disconnect()
    sys.exit()

#constants
SERVER_IP = "54.193.77.230"
if len(sys.argv) >= 2 and sys.argv[1] == "-l":
    SERVER_IP = "127.0.0.1"
SERVER_PORT = 5393
BTN_WIDTH = 4
BTN_HEIGHT = 1
BTN_BORDER_WIDTH = 3
BTN_PLAYER_COLOR = "RoyalBlue1"
BTN_ENEMY_COLOR = "firebrick2"
BTN_FLASH_COLOR = "yellow"
BTN_UNUSED_COLOR = "SpringGreen3"
BTN_FONT = ("Helvetica", 12, "bold")
PLAYER = "player"
UNUSED = "unused"
OPPONENT = "opponent"
isPlayerTurn = True
isExitGame = False

#create login window
register = Register()
register.createWindow()

#setup networking
client = Client(SERVER_IP, SERVER_PORT)
client.connect()
client.changeName(register.username)
roomList = client.listRooms()

roomSelect = RoomSelect(roomList)
roomSelect.createWindow()

if roomSelect.isFirst:
    waitingRoom = WaitingRoom()
    waitingRoom.createWindow()

btnClicked = False
prevPos = [100, 100]

root = Tk()
root.minsize(width=520, height=465)
root.maxsize(width=520, height=465)

root.protocol("WM_DELETE_WINDOW", exitGame)
root.title("Stratego")
rightFrame = Frame(root, bg="green")
rightFrame.grid(row=0, column=0)

#set up opponent, player, and board
playerSetup, oppSetup = getBoardSetup()
oppSetup = translateBoard(oppSetup)
buttons, board = placeButtons(playerSetup, oppSetup)

#setup widgets (buttons, labels)
bottomFrame = Frame(root, bg="azure")
bottomFrame.grid(row=1, column=0)
statusLabel = Label(bottomFrame, bg="lavender", text="Your Turn", width=51, height=3, font=BTN_FONT)
statusLabel.grid(row=0, column=0)
helpLabel = Label(bottomFrame, width=60, height=3, bg="mint cream")
helpLabel.grid(row=1,column=0)
setOnClick()

if not roomSelect.isFirst:
    root.update()
    endTurn()

root.mainloop()
