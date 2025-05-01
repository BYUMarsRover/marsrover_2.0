std_msgs/Header header

# Definitions of Seatrac defined enums and types (ie CID_E, AMSGTYPE_E, NAV_QUERY_T, ...) can be found
# in the Seatrac Developer Guide https://www.blueprintsubsea.com/downloads/seatrac/UM-140-D00221-07.pdf

# ModemSend is used to transmit an acoustic message to a remote beacon.

uint8 msg_id           # CID_E - Command Identification Code. Indicates the type of command to send to the beacon.
                       #    This ros message only supports the 4 commands relating to acoustic protocols:
                       #        CID_PING_SEND: Sends an acoustic signal without packet data and requires a response
                       #        CID_DAT_SEND: Sends a message with a data packet that can be one way or require a response
                       #        CID_ECHO_SEND: Requires a response and the response includes the same data packet
                       #        CID_NAV_SEND: Sends a message requesting a response with specific information from the other beacon

uint8 dest_id          # BID_E. Beacon id of the beacon to send the acoustic transmission to. (1-15 or 0 for all beacons)
uint8 msg_type         # AMSGTYPE_E. Specifies how the remote beacon should respond to the transmission. 
                       # Used with the PING, DAT, and ECHO protocols but not for the NAV protocol. 

uint8 packet_len       # optional packet length for data send commands (0 to 30)
uint8[30] packet_data  # optional packet data array for data send commands

bool insert_timestamp  # for some applications, it may be usefull to include a timestamp with the message taken at
                       # at the last possible moment before it sends. If true, the timestamp will be written as an 
                       # unsigned 4 byte/32 bit integer to the 2nd - 5th bytes in packet_data.
                       # (the first byte is reserved for the message type)

uint8 nav_query_flags  # NAV_QUERY_T. Bit mask indicating which fields the NAV response should return.
                       # Used only with the NAV protocol

