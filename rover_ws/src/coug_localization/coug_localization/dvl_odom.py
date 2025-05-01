import rclpy
from rclpy.node import Node
from dvl_msgs.msg import DVLDR
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data
import math

class DVLOdom(Node):
    """
    Converts DVL data to odometry and publishes it.

    :author: Nelson Durrant
    :date: Apr 2025

    Subscribers:
    - dvl/position (dvl_msgs/DVLDR)
    Publishers:
    - dvl/odometry (nav_msgs/Odometry)
    """

    def __init__(self):
        super().__init__("dvl_odom")

        # sensor data qos profile

        self.dvl_sub = self.create_subscription(
            DVLDR, "coug1/dvl/position", self.dvl_callback, qos_profile=qos_profile_sensor_data
        )
        self.dvl_pub = self.create_publisher(Odometry, "dvl/odometry", 10)
        self.get_logger().info("DVL to Odometry node started. Waiting for DVL data...")

    def quaternion_from_euler(self, roll_deg, pitch_deg, yaw_deg):
        """
        Converts Euler angles (roll in degrees, pitch in degrees, yaw in radians)
        in ZYX convention to a quaternion (x, y, z, w).
        """

        # Convert roll and pitch from degrees to radians
        roll_rad = math.radians(roll_deg)
        pitch_rad = math.radians(pitch_deg)
        yaw_rad = math.radians(yaw_deg)

        # Calculate trigonometric values for half angles
        cy = math.cos(yaw_rad * 0.5)
        sy = math.sin(yaw_rad * 0.5)
        cp = math.cos(pitch_rad * 0.5)
        sp = math.sin(pitch_rad * 0.5)
        cr = math.cos(roll_rad * 0.5)
        sr = math.sin(roll_rad * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return x, y, z, w

    def dvl_callback(self, msg: DVLDR):
        """
        Callback for DVL subscriber. Converts DVL data to odometry and publishes it.
        """

        # Create an Odometry message
        odom_msg = Odometry()
        odom_msg.header.stamp = msg.header.stamp
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_link"

        # Fill in the position data
        odom_msg.pose.pose.position.x = msg.position.x
        odom_msg.pose.pose.position.y = msg.position.y
        # TODO: Probably just want to use the depth sensor for the z position
        odom_msg.pose.pose.position.z = msg.position.z

        # Fill in the orientation data
        odom_msg.pose.pose.orientation.x = self.quaternion_from_euler(msg.roll, msg.pitch, msg.yaw)[0]
        odom_msg.pose.pose.orientation.y = self.quaternion_from_euler(msg.roll, msg.pitch, msg.yaw)[1]
        odom_msg.pose.pose.orientation.z = self.quaternion_from_euler(msg.roll, msg.pitch, msg.yaw)[2]
        odom_msg.pose.pose.orientation.w = self.quaternion_from_euler(msg.roll, msg.pitch, msg.yaw)[3]

        # Fill in the covariance data (use the standard deviation from the DVL message)
        odom_msg.pose.covariance[0] = msg.pos_std ** 2
        odom_msg.pose.covariance[7] = msg.pos_std ** 2
        odom_msg.pose.covariance[14] = msg.pos_std ** 2

        # Publish the Odometry message
        self.dvl_pub.publish(odom_msg)

def main(args=None):

    rclpy.init(args=args)

    dvl_odom_node = DVLOdom()

    try:
        rclpy.spin(dvl_odom_node)
    except KeyboardInterrupt:
        pass
    finally:
        dvl_odom_node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
    