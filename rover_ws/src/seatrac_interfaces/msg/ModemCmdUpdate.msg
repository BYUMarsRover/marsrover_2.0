std_msgs/Header header

# Definitions of Seatrac defined enums and types (ie CID_E, BID_E, CST_E, ...) can be found
# in the Seatrac Developer Guide https://www.blueprintsubsea.com/downloads/seatrac/UM-140-D00221-07.pdf

uint8 msg_id            # CID_E - Command Identification Code. Indicates the type of report recieved from the beacon.
                        # Different msg types include different information, and therefore populate different fields.
                        # Not all CID_E msg types are captured or supported in this ros message.

### Command Status Code Fields ###
        # Command Status Codes tell you if a command executed sucessfully, and if not, what error the command encountered
        # Reports that include a command status code usually do not include any other fields besides msg_id and local_beacon_id
uint8 command_status_code # CST_E. Indicates the status of the 
uint8 target_id   # BID_E. For error reports from acoustic transmissions, the target_id is the id of the remote beacon.
