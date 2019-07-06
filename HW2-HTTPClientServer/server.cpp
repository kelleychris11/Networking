#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <string.h>
#include <netinet/tcp.h>
#include <sys/uio.h>
#include <iostream>
#include <sys/time.h>
#include <stdlib.h>
#include <fstream>
#include <stdio.h>
#include <sstream>
using namespace std;

//-----------------------------------------------------------------------
//File: server.cpp
//Author: Chris Kelley
//Date Created: 1/24/2019
//Last Modified: 2/9/2019
//Purpose: Handle a HTTP request by reading request, finding file specified (if it
// exists and is authorized), and responding with contents of file in HTTP format 
//------------------------------------------------------------------------

const int NUM_THREADS = 5;
const int NUM_CONN = 5;

//handles client connection requests, passed to thread runner method
struct Request
{
	//new file(socket) descriptor created to handle the current request
	int newfd;
};

//Handles information relating to server response message
struct Response
{
	string fileName;
	int respCode;
	string respMessage;
	string outHeader;
	int msgLength;
};

//prototyping methods
void * runner(void * req);
struct Response parseHeader(int sockfd);
void getFileName(struct Response * resp, string header);
void getResponseCode(struct Response * resp);
void transmitFile(int sockfd, struct Response * resp, string msgBody);
void prepareHeader(struct Response * resp);
string readFromFile(struct Response * resp, int sockfd);

//main method -- starts server program
int main(int argc, char * argv[])
{
	if(argc != 2)
	{
		cout << "Enter port number." << endl;
		return 0;
	}

	int port = atoi(argv[1]);
	if(port == 0)
	{
		cout << "Enter port number greater than 1024" << endl;
	}

	struct Request req;	

	//set up socket
	sockaddr_in acceptSockAddr;
	bzero((char *)&acceptSockAddr, sizeof(acceptSockAddr));
	acceptSockAddr.sin_family = AF_INET;
	acceptSockAddr.sin_addr.s_addr = htonl(INADDR_ANY);
	acceptSockAddr.sin_port = htons(port);
	int sockfd = socket(AF_INET, SOCK_STREAM, 0);
	const int on = 1;
	setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, (char *)&on, sizeof(int));
	
	//bind socket
	bind(sockfd, (sockaddr *)&acceptSockAddr, sizeof(acceptSockAddr));
	
	pthread_t threads[NUM_THREADS];
	
	//create thread pool to handle client requests
	for(int i = 0; i < NUM_THREADS; i++)
	{
		//listen for client connection
		listen(sockfd, NUM_CONN);
		cout << "listening..." << endl;
		//create new file(socket) descriptior to handle client request
		sockaddr_in newSockAddr;
		socklen_t newSockAddrSize = sizeof(newSockAddr);
		//connect to client
		req.newfd = accept(sockfd, (sockaddr *)&newSockAddr, &newSockAddrSize);
		//create new thread to handle request
		pthread_create(&threads[i], NULL, &runner, (void *)(&req));
	}
	
	//close child threads
	for(int i = 0; i < NUM_THREADS; i++)
	{
		pthread_join(threads[i], NULL);
	}
}

//thread function, executed with each client request
void * runner(void * req)
{
	struct Request * thisReq = (struct Request *) req;
	int sockfd = thisReq->newfd;
	struct Response * resp = new Response;

	//buffer to hold HTTP request header
	char charHeader[200];

	//retrieve HTTP GET request
	int nRead = read(sockfd, charHeader, sizeof(charHeader));
	if(nRead == -1)
	{
		cout << "Error reading HTTP request" << endl;
		pthread_exit(NULL);
	}

	string header = string(charHeader);
	getFileName(resp, header);
	getResponseCode(resp);
	string msgBody = "";

	if(resp->respCode == 200)
	{
		msgBody = readFromFile(resp, sockfd);
	}
	else if(resp->respCode == 404)
	{
		msgBody = "Code 404: The file you requested was not found. Sorry!!";
	}
	
	resp->msgLength = strlen(msgBody.c_str());
	prepareHeader(resp);
	transmitFile(sockfd, resp, msgBody);
	cout << "Retrieving File: " << resp->fileName << endl;
	cout << "Sending Response Code: " << resp->respMessage << endl << endl;

	//Join child thread with parent
	pthread_exit(NULL);
}

//Transmit HTTP response to requestor
void transmitFile(int sockfd, struct Response * resp, string msgBody)
{
	int totalBytesWritten = 0;
	int bytesWritten = 0;
	int messageSize = resp->msgLength + strlen(resp->outHeader.c_str());

	//message to sent to requestor: response header plus message body
	string fullMsg = resp->outHeader + msgBody;
	const char * outBuffer = fullMsg.c_str();

	//send data through socket to requestor
	while(totalBytesWritten < messageSize)
	{
		bytesWritten = write(sockfd, outBuffer + totalBytesWritten, messageSize - totalBytesWritten);
		totalBytesWritten += bytesWritten;
	}
}

//Prepare HTTP response header to be sent to requestor
void prepareHeader(struct Response * resp)
{
	char sMsgLength[10];
	//char array to int conversion
	sprintf(sMsgLength, "%d", resp->msgLength);
	//HTTP response header
	resp->outHeader = "HTTP/1.1 " + resp->respMessage + "\r\n" + 
		"Content-Length: " + sMsgLength + "\r\n\r\n";
}

//Read data from file requested and store in returned string
string readFromFile(struct Response * resp, int sockfd)
{
	string fullMsg = "";
	ifstream inFile;
	stringstream sstr;
	inFile.open(resp->fileName.c_str());
	//read data from file
	sstr << inFile.rdbuf();
	fullMsg = sstr.str();

	inFile.close();
	return fullMsg;
}

//Identify which response code to send back to requestor
void getResponseCode(struct Response * resp)
{
	//check if trying to access parent directory
	if(resp->fileName.substr(0, 2) == "..")
	{
		resp->respCode = 403;
		resp->respMessage = "403 Forbidden";
	}
	//attempt to access forbidden file
	else if(resp->fileName == "SecretFile.html")
	{
		resp->respCode = 401;
		resp->respMessage = "401 Unauthorized";
	}
	//bad request
	else if(resp->fileName == "")
	{
		resp->respCode = 400;
		resp->respMessage = "400 Bad Request";
	}
	//check if file exists
	else if (access(resp->fileName.c_str(), F_OK) != -1)
	{
		resp->respCode = 200;
		resp->respMessage = "200 OK";
	}
	else
	{
		resp->respCode = 404;
		resp->respMessage = "404 Not Found";
	}
}

//Identify the file name requested
void getFileName(struct Response * resp, string header)
{
	//search for file name past: 'GET ' (4 characters in)
	int count = 4;
	if(header[4] == '/')
	{
		count = 5;
	}
		
	char nextChar = header[count];
	while(nextChar != ' ')
	{
		resp->fileName += nextChar;
		count++;
		nextChar = header[count];
	}	
}
