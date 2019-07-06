#include "UdpSocket.h"
#include "Timer.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

using namespace std;

//--------------------------------------------------------
//File: udphw3.cpp
//Author: Chris Kelley
//Date Created: 2/14/2019
//Last Modified: 2/22/2019
//Purpose: Implement transport protocol methods for client
// and server.
//--------------------------------------------------------

//-------CASE 2 (STOP-AND-WAIT) FUNCTIONS-------------


//sends message[] and receives acknowledgement from server 'max'
// times using sock object. If client cannot receive AK immediately, it
// starts timer. If timout (1500 usec) client resends message.
//Function returns number of retransmitted messages
int clientStopWait(UdpSocket &sock, const int max, int message[])
{
    int numRetransmit = 0;
    //main loop, iterates for each new sequence number sent
    for(int i = 0; i < max; i++)
    {
        bool acked = false;
        //set sequence number
        message[0] = i;
        int bytesSent = sock.sendTo((char *) message, MSGSIZE);
        Timer timer;
        int ackNum;
        //check immediately to see if ack received
        if(sock.pollRecvFrom())
        {
            sock.recvFrom((char *)&ackNum, sizeof(int));
            if(ackNum == i)
            {
                acked = true;
            }
        }

        //if ack not received, start timer
        if(!acked)
        {
            timer.start();
        }

        //wait for ack - keep checking and resending until one is received
        bool timeout = false;
        while(!acked)
        {
            if(timer.lap() >= 1500)
            {
                timeout = true;
                break;
            }

            if(sock.pollRecvFrom())
            {
                sock.recvFrom((char *) &ackNum, sizeof(int));
                if(ackNum == i)
                {
                    acked = true;
                }
            }
        }

        //check if timout occurred
        if(timeout)
        {
            numRetransmit++;
            //set back i count so it will retransmit
            i--;
        }
    }
    return numRetransmit;
}

//Repeats receiving message[] and sending ACK at a server side 'max'
// times using the sock object
void serverReliable(UdpSocket &sock, const int max, int message[])
{
    int numReceived = 0;
    //receive messages -- send acks
    for(int expectedSeqNum = 0; expectedSeqNum < max; expectedSeqNum++)
    {
        sock.recvFrom((char *) message, MSGSIZE);
        
        int ackNum = message[0];
        if(expectedSeqNum != ackNum)
        {
            //decrement expectedSeqNum because it was not received but will increment
            //next loop
            expectedSeqNum--;
            ackNum = expectedSeqNum;
        }
        sock.ackTo((char *)&ackNum, sizeof(int));
    }
}

//------CASE 3 (SLIDING WINDOW) FUNCTIONS-----------------------------------

//Send message and receive ACK 'max' times. Client may send up to 'windowSize' unacked packets
// before waiting and resending the lowest numbered unacked packet.
int clientSlidingWindow(UdpSocket &sock, const int max, int message[], int windowSize)
{
    int base = 0;
    int numRetransmit = 0;

    for(int nextSegNum = 0; nextSegNum < max; nextSegNum++)
    {
        //check if available, unacked spot in window
        if(nextSegNum < base + windowSize)
        {
            message[0] = nextSegNum;
            sock.sendTo((char *)message, MSGSIZE);
        }
        //window is full -- set timer and wait for ack of base
        else
        {
            //start timer -- wait for base ACK
            Timer timer;
            timer.start();
            bool acked = false;
            while(!acked)
            {
                //check for timeout -- if so, resend base
                if(timer.lap() > 1500)
                {
                    message[0] = base;
                    sock.sendTo((char *) message, MSGSIZE);
                    numRetransmit++;
                    //restart timer
                    timer.start();
                }
         
                //check for ack while there are acks to receive
                while(sock.pollRecvFrom())
               	{
                    int ackNum;
                    sock.recvFrom((char *)&ackNum, sizeof(int));
                    if(ackNum >= base)
                    {
                    	base = ackNum + 1;
                        acked = true;
                    }
                }
            }
            message[0] = nextSegNum;
            sock.sendTo((char *) message, MSGSIZE);
        }
        //check for ack while there are acks to receive
        while(sock.pollRecvFrom())
        {
            int ackNum;
            sock.recvFrom((char *)&ackNum, sizeof(int));
            if(ackNum >= base)
            {
                base = ackNum + 1;
            }
        }
    }

    //All segments sent -- wait for any outstanding acks
    Timer timer;
    timer.start();
    while(base < max)
    {
        //send base
        if(timer.lap() > 1500)
        {
            message[0] = base;
            sock.sendTo((char *)message, MSGSIZE);
            numRetransmit++;
        }
        //check for acks
        while(sock.pollRecvFrom())
        {
            int ackNum;
            sock.recvFrom((char *)&ackNum, sizeof(int));
            if(ackNum >= base)
            {
                base = ackNum + 1;
            }
        }
    }
    return numRetransmit;
}

//Server maintains list of segment received, if a packet is received out
// of order, an ack is sent for the last message received in order
void serverEarlyRetrans(UdpSocket &sock, const int max, int message[], int windowSize)
{
    int expectedSeqNum = 0;
    int seqNumsRcvd[max];
    //initialize seqNumRcvd array
    for(int i = 0; i < max; i++)
    {
        seqNumsRcvd[i] = -1;
    }
    while(expectedSeqNum < max)
    {
        sock.recvFrom((char *)message, MSGSIZE);
        int ackNum = message[0];
        if(ackNum == expectedSeqNum)
        {
            seqNumsRcvd[ackNum] = ackNum;
            //check if messages previously received aboved exepectedSeqNum
            for(int i = expectedSeqNum + 1; i < expectedSeqNum + windowSize; i++)
            {
                if(seqNumsRcvd[i] == -1 || (i == expectedSeqNum + windowSize - 1) || (i == max))
                {
                    ackNum = i - 1;
                    break;
                }
            }
            expectedSeqNum = ackNum + 1;        
        }
        //message received out of order, save sequence num for later if within window
        else if(ackNum > expectedSeqNum && ackNum < (expectedSeqNum + windowSize))
        {
            seqNumsRcvd[ackNum] = ackNum;
            ackNum = expectedSeqNum - 1;
        }
        //ackNum < expectedSeqNum
        else
        {
            //send ACK for last message received in order
            ackNum = expectedSeqNum - 1;
        }
        sock.ackTo((char *)&ackNum, sizeof(int));     
    }
}
