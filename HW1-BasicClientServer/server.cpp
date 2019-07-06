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
using namespace std;

unsigned long long getTime();
void * runner(void * req);

//-----------------------------------------------------------------------
//File: server.cpp
//Author: Chris Kelley
//Date Created: 1/10/2019
//Last Modified: 1/18/2019
//Purpose: Listen for client connection through a socket. When a connection
// is made, create a new thread that reads in the data sent by the client.
// when the data if finished being read, send back the number of reads to 
// the client.
//------------------------------------------------------------------------

const int BUFSIZE = 1500;
const int NUM_THREADS = 3;
const int NUM_CONN = 5;


//handles client connection requests, passed to thread runner method
struct Request
{
	//number of repetitions
	int reps;
	//new file(socket) descriptor created to handle the current request
	int newfd;
};

int main(int argc, char * argv[])
{
	//hold client connection request data
	struct Request req;	

	//check if args are valid
	if(argv[1] == NULL || argv[2] == NULL)
	{
		cout << "enter port and reps" << endl;
		return 0;
	}

	int port = atoi(argv[1]);
	req.reps = atoi(argv[2]);
	
	if(port == 0 || req.reps == 0)
	{
		cout << "enter valid numbers for port and repetitions" << endl;
		return 0;
	}

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
	char * databuf[BUFSIZE];
	unsigned long long startTime = getTime();
	int newfd = thisReq->newfd;
	
	int count = 0; 
	int totalRead = 0;
	int repsCompleted = 0;
	//read data from client
	while(repsCompleted < thisReq->reps)
	{
		int nRead = 0;
		while(nRead < BUFSIZE)
		{
			int currRead = read(newfd, databuf, BUFSIZE - nRead);
			nRead += currRead;
			count++;
		}
		totalRead += nRead;
		repsCompleted++;
	}
	//write number of reads back to client
	int countToSend = htonl(count);

	unsigned long long endTime = getTime();
	unsigned long long duration = endTime - startTime;
	cout << "data-receiving-time: " << duration << " usecs" << endl;

	int bytesSent = write(newfd, &countToSend, sizeof(countToSend));
}

//get the current time in microseconds
unsigned long long getTime()
{
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return ((unsigned long long)tv.tv_sec * 1000000ULL) +
	(unsigned long long)tv.tv_usec;
}


