#include "UdpSocket.h"
#include "Timer.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
//---------------------------------------------------
//File: UdpSocket.h
//Author: Chris Kelley
//Created: 2/14/2019
//Last Modified: 2/14/2019
// Purpose: Header file, defines methods used in
// Case 2 (Stop-and-wait) and Case 3 (Sliding Window)
//---------------------------------------------------


//---------CASE 2 (STOP-AND-WAIT) FUNCTIONS------------------------

//sends message[] and receives acknowledgement from server 'max'
// times using sock object. If client cannot receive AK immediately, it
// starts timer. If timout (1500 usec) client resends message.
//Function returns number of retransmitted messages
int clientStopWait(UdpSocket &sock, const int max, int message[]);


//Repeats receiving message[] and sending ACK at a server side 'max'
// times using the sock object
void serverReliable(UdpSocket &sock, const int max, int message[]);

//--------CASE 3 (SLIDING WINDOW) FUNCTIONS-------------------------

//sends message[] and receives ack from server 'max' times using sock object
// Client may continuously send new messages as long as the number of in-transit
// messages is less than 'windowSize'. windowSize should be decremented with each ACK
// If number of unACKed messages reaches window size, a timer starts. If timeout
// (1500 usec), minimum sequence number is resent.
// Functino returns the count of re-transmitted messages
int clientSlidingWindow(UdpSocket &sock, const int max, int message[], int windowSize);


//Receives message[] and sends ACK 'max' times using sock object. Every time
// new message is received, message's sequence number is saved in array and 
// cumulative ACK is sent to client (last rec'd message in order)
void serverEarlyRetrans(UdpSocket &sock, const int max, int message[], int windowSize);