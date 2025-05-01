import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from robot_localization.srv import SetDatum
import sys

class SyncOrigin(Node):
    """
    Syncs the origin of mapviz with the origin of navsat_transform on the first GPS fix

    :author: Nelson Durrant
    :date: Apr 2025

    Subscribers:
    - gps/fix (sensor_msgs/NavSatFix)
    Publishers:
    - mapviz/origin (sensor_msgs/NavSatFix)
    Clients:
    - datum (robot_localization/SetDatum)
    """

    def __init__(self):
        super().__init__("sync_origin")

        self.declare_parameter('publish_rate_hz', 1.0) # Rate in Hz for publishing origin
        publish_rate = self.get_parameter('publish_rate_hz').get_parameter_value().double_value
        self.timer_period = 1.0 / publish_rate if publish_rate > 0 else 1.0 # seconds

        self.origin_msg: NavSatFix = None # Stores the first received GPS message
        self.origin_set_attempted = False # Flag to track if we tried processing the first fix

        self.gps_sub = self.create_subscription(
            NavSatFix, "gps/fix", self.gps_callback, 10
        )

        self.gps_pub = self.create_publisher(NavSatFix, "mapviz/origin", 10)

        self.srv_client = self.create_client(SetDatum, "datum")
        while not self.srv_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for SetDatum service...")

        # Timer for periodic publishing - starts immediately but only publishes after origin_msg is set
        self.publish_timer = self.create_timer(self.timer_period, self.publish_origin_callback)

        self.get_logger().info(f"SyncOrigin node started. Waiting for first GPS fix... 1")
        self.get_logger().info(f"Publishing mapviz origin at {publish_rate} Hz.")

        self.origin_set_attempted = False


    def gps_callback(self, msg: NavSatFix):
        """
        Callback for GPS subscriber. Stores the first fix, calls SetDatum,
        and destroys the subscriber.
        """

        if self.origin_set_attempted:
            return # Only process the first message

        self.origin_set_attempted = True # Mark that we are processing the first message
        self.get_logger().info(
            f"First GPS fix received: Lat {msg.latitude}, Lon {msg.longitude}, Alt {msg.altitude}. Storing origin and calling SetDatum."
        )

        # Store the message - this allows the timer to start publishing
        self.origin_msg = msg

        request = SetDatum.Request()
        request.geo_pose.position.latitude = msg.latitude
        request.geo_pose.position.longitude = msg.longitude
        request.geo_pose.position.altitude = msg.altitude
        # Default orientation
        request.geo_pose.orientation.x = 0.0
        request.geo_pose.orientation.y = 0.0
        request.geo_pose.orientation.z = 0.0
        request.geo_pose.orientation.w = 1.0

        future = self.srv_client.call_async(request)
        future.add_done_callback(self.datum_service_callback)

        # Destroy subscriber after initiating service call
        self.destroy_subscription(self.gps_sub)
        self.gps_sub = None
        self.get_logger().info("SetDatum call initiated. GPS subscriber destroyed.")


    def datum_service_callback(self, future):
        """
        Callback for the SetDatum service response.
        """

        try:
            response = future.result()
            self.get_logger().info("Successfully called SetDatum service.")
        except Exception as e:
            self.get_logger().error(f"SetDatum service call failed: {e!r}")


    def publish_origin_callback(self):
        """
        Called by the timer to periodically publish the stored origin.
        """

        if self.origin_msg is not None:
            # Update the timestamp to current time for freshness
            self.origin_msg.header.stamp = self.get_clock().now().to_msg()
            self.gps_pub.publish(self.origin_msg)


def main(args=None):
    rclpy.init(args=args)
    sync_origin_node = SyncOrigin()

    try:
        rclpy.spin(sync_origin_node)
    except KeyboardInterrupt:
        pass
    finally:
        sync_origin_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
