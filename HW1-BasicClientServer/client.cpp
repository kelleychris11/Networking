#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <strings.h>
#include <netinet/tcp.h>
#include <sys/uio.h>
#include <iostream>
#include <sys/time.h>
#include <stdlib.h>
#include <stdio.h>
using namespace std;

struct Args getTestData();
struct Args getArgs(char * argv[]);
unsigned long long getTime();
int writeToServer(int sockfd, Args args);

//------------------------------------------------------------
//File: client.cpp
//Author: Chris Kelley
//Date Created: 1/10/2019
//Last Modified: 1/18/2019
//Purpose: Send data to a server using sockets. Receives number
// of reads made by the server as a response. Calculates time
// to read and total round-trip time.
//------------------------------------------------------------

//hold arguments provided to the program
struct Args
{
	char * port;
	int reps;
	int nbufs;
	int bufsize;
	char * addr;
	int type;
	//flag if an arg is invalid
	bool isValid;
};

int main(int argc, char * argv[])
{	
	//get network parameters
	struct Args args = getArgs(argv);
	
	//if valid arguments weren't given, terminate program
	if(!args.isValid)
	{
		return 0;
	}

	//setup socket
	struct addrinfo hints;
	struct addrinfo * res;
	int sockfd;
	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	getaddrinfo(args.addr, args.port, &hints, &res);
	sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
	//connect to server
	connect(sockfd, res->ai_addr, res->ai_addrlen);

	unsigned long long startTime = getTime();
	
	//send data to server
	int sent = writeToServer(sockfd, args);

	//calculate program execution time
	unsigned long long dataSendingTime = getTime() - startTime;

	//receive number of reads that the server made
	int writesToRecv = 0;
	int rc = read(sockfd,&writesToRecv, sizeof(writesToRecv));
	int numWrites = ntohl(writesToRecv);
	unsigned long long roundTripTime = getTime() - startTime;
	cout << "data-sending-time = " << dataSendingTime << " usec" << endl;
	cout << "round-trip-time = " << roundTripTime << " usec" << endl;
	cout << "# of reads = " << numWrites << endl;
}

//writes data to buffer using one of 3 methods, write (one row at a time), 
// writev (whole buffer at once), or write(whole buffer at once)
// returns:  all bytes sent over all repetitions
int writeToServer(int sockfd, Args args)
{
	//get start time for calculation program duration
	unsigned long long startTime = getTime();

	char databuf[args.nbufs][args.bufsize];

	int sent = 0;
	//send data to server	
	for(int i = 0; i < args.reps; i++)
	{
		//option 1: send data one row of the buffer (databuf) at a time
		if(args.type == 1)
		{
			for(int j = 0; j < args.nbufs; j++)
			{	
				sent += write(sockfd, databuf[j], sizeof(databuf[j]));
			}
		}
		//option 2: send data using writev (whole buffer (databuf) at once)
		else if(args.type == 2)
		{
			struct iovec vector[args.nbufs];
			for(int j = 0; j < args.nbufs; j++)
			{
				vector[j].iov_base = databuf[j];
				vector[j].iov_len = args.bufsize;
			}
			sent += writev(sockfd, vector, args.nbufs);
		}
		//option 3: send all data in buffer at once
		else
		{
			sent += write(sockfd, databuf, args.nbufs * args.bufsize);
		}
	}
	return sent;
}

//get current time in microseconds
unsigned long long getTime()
{
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return  ((unsigned long long)tv.tv_sec * 1000000ULL) + 
		(unsigned long long)tv.tv_usec;
}

//get argument data and store it in a Args struct
struct Args getArgs(char * argv[])
{
	struct Args args;
	args.isValid = true;
	for(int i = 1; i < 7; i++)
	{
		if(argv[i] == NULL)
		{
			cout << "enter args: 1-port, 2-reps, 3-nbufs, 4-bufsize";
			cout << ", 5-addr, 6-type" << endl;
			args.isValid = false;
			return args;
		}
	}
	
	args.port = argv[1];
	int port = atoi(args.port);
	if(port < 1024)
	{
		cout << "port should be number > 1024" << endl;
		args.isValid = false;
	}

	args.reps = atoi(argv[2]);
	if(args.reps == 0)
	{
		cout << "reps must be number > 0" << endl;
		args.isValid = false;
	}

	args.nbufs = atoi(argv[3]);
	if(args.nbufs == 0)
	{
		cout << "nbufs must be number > 0" << endl;
		args.isValid = false;
	}

	args.bufsize = atoi(argv[4]);
	if(args.bufsize == 0)
	{
		cout << "bufsize must be number > 0" << endl;
		args.isValid = false;
	}

	args.addr = argv[5];
	
	args.type = atoi(argv[6]);
	if(args.type < 1 || args.type > 3)
	{
		cout << "type must be 1, 2, or 3" << endl;
		args.isValid = false;
	}

	return args;
}

//for testing puposes
struct Args getTestData()
{
	struct Args args;
	args.port = "4000";
	args.reps = 1000;
	args.nbufs = 10;
	args.bufsize = 150;
	//args.addr = "uw1-320-10.uwb.edu";
	args.addr = "127.0.0.1";
	args.type = 3;
	return args;
}

