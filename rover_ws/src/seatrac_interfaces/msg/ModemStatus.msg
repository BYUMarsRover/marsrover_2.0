std_msgs/Header header

# Definitions of Seatrac defined enums and types (ie CID_E, BID_E, CST_E, ...) can be found
# in the Seatrac Developer Guide https://www.blueprintsubsea.com/downloads/seatrac/UM-140-D00221-07.pdf

uint8 msg_id            # CIDE - Command Identification Code. Indicates the type of report recieved from the beacon.
                        # Different msg types include different information, and therefore populate different fields.
                        # Not all CID_E msg types are captured or supported in this ros message.

### Status Fields ###
        # This report is a Status message if CID_E msg_id = CID_STATUS = 0x10
        # Status messages can be generated at a user defined interval between 1 and 25 Hz
uint64 timestamp  # time since beacon was last powered up in milliseconds

bool   includes_env_fields
uint16 supply_voltage  # Beacon's supply voltage. Divide by 1000 for value in Volts.
int16  env_temp        # Temperature of air/water in contact with pressure sensor. Divide by 10 for value in Celsius.
int32  env_pressure    # External air/water pressure in milli-bars, with tolerance of +\-1 Bar.
int16    depth_local  # Divide by 10 for local depth im meters
uint16   vos          # Divide by 10 for velocity of sound in meters per second.

bool     includes_local_attitude
int16    attitude_yaw    # Divide by 10 for local yaw in degrees
int16    attitude_pitch  # Divide by 10 for local pitch in degrees
int16    attitude_roll   # Divide by 10 for local roll in degrees

bool   includes_comp_ahrs
float64 acc_x
float64 acc_y
float64 acc_z
float64 mag_x
float64 mag_y
float64 mag_z
float64 gyro_x
float64 gyro_y
float64 gyro_z
