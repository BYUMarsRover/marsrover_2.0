import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import math

class GPSFix(Node):
    """
    Simply check if the GPS lat and lon are not nan and set the status flag to 0 if they are.

    :author: Nelson Durrant
    :date: Apr 2025

    Subscribers:
    - coug1/fix (sensor_msgs/NavSatFix)
    Publishers:
    - gps/fix (sensor_msgs/NavSatFix)
    """

    def __init__(self):
        super().__init__("gps_fix")

        self.gps_sub = self.create_subscription(
            NavSatFix, "coug1/fix", self.gps_callback, 10
        )
        self.gps_pub = self.create_publisher(NavSatFix, "gps/fix", 10)
        self.get_logger().info("GPS fix node started. Waiting for GPS data...")

    def gps_callback(self, msg: NavSatFix):
        """
        Callback for GPS subscriber. Checks if the GPS data is valid and publishes it.
        """
        if not (math.isnan(msg.latitude) or math.isnan(msg.longitude)):
            msg.status.status = 0
            msg.status.service = 1
            self.gps_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    gps_fix_node = GPSFix()
    rclpy.spin(gps_fix_node)
    gps_fix_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
