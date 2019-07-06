#include <iostream>
#include "UdpSocket.h"
#include "Timer.h"
#include "stdlib.h"

using namespace std;

#define PORT 1772538 // my UDP port
#define MAX 20000    // times of message transfer
#define MAXWIN 30    // the maximum window size
#define LOOP 10      // loop in test 4 and 5

// client packet sending functions
void clientUnreliable(UdpSocket &sock, const int max, int message[]);
// You must implement the following two functions
int clientStopWait(UdpSocket &sock, const int max, int message[]);
int clientSlidingWindow(UdpSocket &sock, const int max, int message[],
                        int windowSize);
//int clientSlowAIMD( UdpSocket &sock, const int max, int message[],
//		     int windowSize, bool rttOn );

// server packet receiving fucntions
void serverUnreliable(UdpSocket &sock, const int max, int message[]);
// You must implement the following two functions
void serverReliable(UdpSocket &sock, const int max, int message[]);
void serverEarlyRetrans(UdpSocket &sock, const int max, int message[],
                        int windowSize, int error);
//void serverEarlyRetrans( UdpSocket &sock, const int max, int message[],
//			 int windowSize, bool congestion );

enum myPartType
{
  CLIENT,
  SERVER,
  ERROR
} myPart;

int main(int argc, char *argv[])
{

  int message[MSGSIZE / 4]; // prepare a 1460-byte message: 1460/4 = 365 ints;
  UdpSocket sock(PORT);     // define a UDP socket

  myPart = (argc == 2) ? SERVER : CLIENT;

  if (argc != 2 && argc != 3)
  {
    cerr << "usage: " << argv[0] << " [serverIpName]" << endl;
    return -1;
  }

  //get window size
  int windowSize = atoi(argv[1]);

  if (myPart == CLIENT) // I am a client and thus set my server address
    if (sock.setDestAddress(argv[2]) == false)
    {
      cerr << "cannot find the destination IP name: " << argv[1] << endl;
      return -1;
    }
    
  cerr << "   Starting Test 4: sliding windows with errors" << endl;

  if (myPart == CLIENT)
  {

    Timer timer;         // define a timer
    int retransmits = 0; // # retransmissions

    for (int error = 0; error < 11; error++)
    {
      timer.start();
      retransmits = clientSlidingWindow(sock, MAX, message, windowSize);
      cerr << "Error Rate = ";
      cout << error << " ";
      cerr << "Elapsed time = ";
      cout << timer.lap() << endl;
      cerr << "retransmits = " << retransmits << endl;
    }
  }

  if (myPart == SERVER)
  {
    for (int error = 0; error < 11; error++)
    {
      serverEarlyRetrans(sock, MAX, message, windowSize, error);
    }

    // The server should make sure that the last ack has been delivered to
    // the client. Send it three time in three seconds
    cerr << "server ending..." << endl;

    for (int i = 0; i < 10; i++)
    {
      sleep(1);
      int ack = MAX - 1;
      sock.ackTo((char *)&ack, sizeof(ack));
    }

    cerr << "finished" << endl;
  }
  return 0;
}

// Test 1: client unreliable message send -------------------------------------
void clientUnreliable(UdpSocket &sock, const int max, int message[])
{
  cerr << "client: unreliable test:" << endl;

  // transfer message[] max times
  for (int i = 0; i < max; i++)
  {
    message[0] = i;                        // message[0] has a sequence #
    sock.sendTo((char *)message, MSGSIZE); // udp message send
    cerr << "message = " << message[0] << endl;
  }
}

// Test1: server unreliable message receive -----------------------------------
void serverUnreliable(UdpSocket &sock, const int max, int message[])
{
  cerr << "server unreliable test:" << endl;

  // receive message[] max times
  for (int i = 0; i < max; i++)
  {
    sock.recvFrom((char *)message, MSGSIZE); // udp message receive
    cerr << message[0] << endl;              // print out message
  }
}
