#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <netinet/tcp.h>
#include <iostream>
#include <stdlib.h>
#include <stdio.h>
#include <fstream>
using namespace std;

//--------------------------------------------------------------
//File: retriever.cpp
//Author: Chris Kelley
//Date Created: 1/24/2019
//Last Modified: 2/9/2019
//Purpose: Make a HTTP structured GET request to either a 
// web server or the server.cpp program. The program requests a
// file, if the requested file is returned from the server, the 
// program prints the body of the message to the screen and saves
// the body of the message to a file: data.txt
//---------------------------------------------------------------


//relevant data parsed from the HTTP response sent by the server
struct HeaderData
{
	int responseCode;
	//lengh of the body of the message
	int length;
};

//Structure containing the domain (uri) and specific file to request (path)
struct URL
{
	string uri;
	string path;
};

//default port
//////const char * PORT = "80";

//prototype methods
HeaderData * getHeader(int sockfd);
void writeToFile(string totalMsg, char * fileName);
URL parseURL(char * argv);


//main method - executes retriever.pp program
int main(int argc, char * argv[])
{
	if(argc != 4)
	{
		cout << "Enter arguments: (1) Request URL  (2) Save-to File (3) Port" << endl;
		return 0;
	}
	
	URL url = parseURL(argv[1]);
	char * fileName = argv[2];
	char * port = argv[3];
	if(port == 0)
	{
		cout << "Enter port 80 (for web server) or port number";
		cout << " greater than 1024" << endl;
	}
	//create socket
	struct addrinfo hints;
	struct addrinfo * res;
	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	getaddrinfo(url.uri.c_str(), port, &hints, &res);
	int sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
	connect(sockfd, res->ai_addr, res->ai_addrlen);
	//create HTTP message to transmit
	string httpMessage = "GET " + url.path + " " +  "HTTP/1.1\r\n" + 
	"Host: " + url.uri + "\r\n\r\n";

	//send HTTP message to server
	int bytesW = write(sockfd, httpMessage.c_str(), httpMessage.length());

	//retrieve data from response header
	struct HeaderData *  data = getHeader(sockfd);
	int code = data->responseCode;
	int bufSize = data->length;
	delete data;

	int nRead = 0;
	char msgBody[bufSize];

	//read data retrived from server
	while(nRead < bufSize)
	{
		//read messaga body, move pointer forward each read by bytes read
		nRead += read(sockfd, msgBody + nRead, bufSize - nRead);
	}
	msgBody[bufSize] = '\0'; //terminate buffer

	//print response message body contents to scrieen
	cout << msgBody << endl;	

	//write response message body conents to file
	if(code == 200)
	{
		writeToFile(string(msgBody), fileName);
	}
}

//Parse URI and path from URL provided as an argument
URL parseURL(char * argv)
{
	URL * url = new URL;
	string args = string(argv);
	int count = 0;
	char c = args[count];
	while((c != '/') && (count < args.length()))
	{
		count++;
		c = args[count];
	}

	url->uri = args.substr(0, count);
	url->path = "";

	if(strlen(args.c_str()) > count + 1)
	{
		url->path = args.substr(count + 1, strlen(args.c_str()));
	}

	return *url;
}

//write message body received to file specified
void writeToFile(string totalMsg, char * fileName)
{
	FILE * inFile = fopen(fileName, "w");

	if(inFile == NULL){
	    cout << "Could not open file" << endl;
	}

	fprintf(inFile, totalMsg.c_str());
	fclose(inFile);
}


//Parse important header data from message received
struct HeaderData * getHeader(int sockfd)
{
	struct HeaderData * data = new HeaderData;

	string currLine = "";
	//current character read from socket
	char currChar[1];
	//last two characters read from socket
	char prevTwo[2];

	bool lineFinished = false;
	int count = 0;
	//while haven't reached \r\n\r\n
	while(!lineFinished)
	{
		//read next character from header
		int bytes = read(sockfd, currChar, sizeof(currChar));

		prevTwo[0] = prevTwo[1];
		prevTwo[1] = currChar[0];
		currLine += currChar[0];

		//check if last 2 characters were carriage-return/line feed (End of line)
		if(prevTwo[0] == '\r' && prevTwo[1] == '\n')
		{
			count++;
			if(count == 1)
			{
				string code = currLine.substr(9,3);
				string responseMessage = currLine.substr(9, currLine.length() - 9);
				cout << "Response Code: " << responseMessage << endl;
				data->responseCode = atoi(code.c_str());
			}
			else if(currLine.substr(0, 15) == "Content-Length:")
			{
				data->length = atoi(currLine.substr(16, 
							currLine.length() - 16).c_str());
			}
			if(currLine == "\r\n" || currLine == "")
			{
				//reached end of HTTP header
				return data;
			}
			//reset current line to empty
			currLine = "";
		}
	}
}
