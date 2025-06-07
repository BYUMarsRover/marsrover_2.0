import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from action_msgs.msg import GoalStatus
from action_msgs.srv import CancelGoal
from rover_interfaces.action import AutonomyTask
from rover_interfaces.msg import AutonomyLeg
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA
from geometry_msgs.msg import Point, Quaternion, Vector3
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QComboBox,
    QLineEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QThread
import sys
import json
import os


class ROS2Thread(QThread):
    """
    Fix for occasional threading crashes

    :author: Nelson Durrant (w Google Gemini 2.5 Pro)
    :date: Apr 2025
    """

    def __init__(self, node):
        super().__init__()
        self.node = node
        self.close_flag = False

    def run(self):
        # IMPORTANT! This must be run in a separate thread to avoid blocking the GUI
        while not self.close_flag and rclpy.ok():
            rclpy.spin_once(self.node, timeout_sec=0.1)
        self.node.destroy_node()
        rclpy.shutdown()

    def stop(self):
        self.close_flag = True


class WaypointDialog(QDialog):
    """
    Interactive dialog for adding or editing a waypoint

    :author: Nelson Durrant (w Google Gemini 2.5 Pro)
    :date: Apr 2025
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Waypoint")
        self.layout = QFormLayout()

        # Create form fields
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["gps", "aruco", "obj"])
        self.latitude_edit = QLineEdit("0.0")
        self.longitude_edit = QLineEdit("0.0")
        self.tag_id_combo = QComboBox()
        self.tag_id_combo.addItems(["1", "2", "3"])
        self.object_combo = QComboBox()
        self.object_combo.addItems(["mallet", "bottle"])

        # Add fields to layout
        self.layout.addRow("Name:", self.name_edit)
        self.layout.addRow("Type:", self.type_combo)
        self.layout.addRow("Latitude:", self.latitude_edit)
        self.layout.addRow("Longitude:", self.longitude_edit)
        self.layout.addRow("Tag ID:", self.tag_id_combo)
        self.layout.addRow("Object:", self.object_combo)

        # Update visibility of fields based on selected type
        self.type_combo.currentIndexChanged.connect(self.update_fields_visibility)
        self.update_fields_visibility()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def update_fields_visibility(self):
        waypoint_type = self.type_combo.currentText()
        self.latitude_edit.setVisible(waypoint_type in ["gps", "aruco", "obj"])
        self.longitude_edit.setVisible(waypoint_type in ["gps", "aruco", "obj"])
        self.layout.labelForField(self.latitude_edit).setVisible(
            waypoint_type in ["gps", "aruco", "obj"]
        )
        self.layout.labelForField(self.longitude_edit).setVisible(
            waypoint_type in ["gps", "aruco", "obj"]
        )

        self.tag_id_combo.setVisible(waypoint_type == "aruco")
        self.layout.labelForField(self.tag_id_combo).setVisible(
            waypoint_type == "aruco"
        )

        self.object_combo.setVisible(waypoint_type == "obj")
        self.layout.labelForField(self.object_combo).setVisible(waypoint_type == "obj")

    def get_waypoint_data(self):
        waypoint = {}
        waypoint["name"] = self.name_edit.text()
        waypoint["type"] = self.type_combo.currentText()
        try:
            waypoint["latitude"] = float(self.latitude_edit.text())
            waypoint["longitude"] = float(self.longitude_edit.text())
        except ValueError:
            QMessageBox.critical(
                self, "Error", "Latitude and Longitude must be numbers."
            )
            return None
        if waypoint["type"] == "aruco":
            tag_id_text = self.tag_id_combo.currentText()
            waypoint["tag_id"] = int(tag_id_text)
        elif waypoint["type"] == "obj":
            waypoint["object"] = self.object_combo.currentText()
        return waypoint


class AutonomyGUI(Node, QWidget):
    """
    GUI for starting, stopping, and monitoring the rover's autonomy task

    :author: Nelson Durrant (w Google Gemini 2.5 Pro)
    :date: Apr 2025

    Clients:
    - /exec_autonomy_task/_action/cancel_goal (action_msgs/CancelGoal)
    Action Clients:
    - exec_autonomy_task (rover_interfaces/AutonomyTask)
    """

    def __init__(self):
        Node.__init__(self, "autonomy_gui")
        QWidget.__init__(self)

        self.resize(800, 800)

        # Define the default directory for waypoints
        # ~/rover_ws/src/rover_navigation/rover_navigation/waypoints
        self.default_waypoints_dir = os.path.join(os.path.expanduser("~"), "rover_ws", "src", "rover_navigation", "waypoints")

        self.callback_group = ReentrantCallbackGroup()
        self._action_client = ActionClient(
            self,
            AutonomyTask,
            "/exec_autonomy_task",
            callback_group=self.callback_group,
        )
        self.marker_publisher = self.create_publisher(MarkerArray, "/waypoint_previews", 10, callback_group=self.callback_group)

        self.waypoints = []
        self.goal_handle = None
        self.close_flag = False

        self.setWindowTitle("Autonomy Task")
        self.layout = QVBoxLayout()

        # Waypoint Display
        self.waypoint_label = QLabel("Waypoints:")
        self.layout.addWidget(self.waypoint_label)
        self.waypoint_list = QListWidget()
        self.layout.addWidget(self.waypoint_list)

        # Save/Load Layout
        json_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Waypoints")
        self.save_button.clicked.connect(self.save_waypoints_to_file)
        json_layout.addWidget(self.save_button)

        self.load_button = QPushButton("Load Waypoints")
        self.load_button.clicked.connect(self.load_waypoints_from_file)
        json_layout.addWidget(self.load_button)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.open_add_waypoint_dialog)
        buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.open_edit_waypoint_dialog)
        buttons_layout.addWidget(self.edit_button)

        self.duplicate_button = QPushButton("Duplicate")
        self.duplicate_button.clicked.connect(self.duplicate_waypoint)
        buttons_layout.addWidget(self.duplicate_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_waypoint)
        buttons_layout.addWidget(self.remove_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_waypoints)
        buttons_layout.addWidget(self.clear_button)

        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.preview_waypoints)
        buttons_layout.addWidget(self.preview_button)

        # Start/Stop Layout
        task_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Task")
        self.start_button.clicked.connect(self.start_task)
        task_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Task")
        self.stop_button.clicked.connect(self.stop_task)
        task_layout.addWidget(self.stop_button)

        self.layout.addLayout(json_layout)
        self.layout.addLayout(buttons_layout)
        self.layout.addLayout(task_layout)

        # Feedback Display
        self.feedback_label = QLabel("Task Feedback:")
        self.layout.addWidget(self.feedback_label)
        self.feedback_display = QListWidget()
        self.layout.addWidget(self.feedback_display)

        self.layout.setStretch(0, 1)  # Waypoint Label
        self.layout.setStretch(1, 6)  # Waypoint List
        self.layout.setStretch(2, 1)  # Save/Load Buttons
        self.layout.setStretch(3, 1)  # Edit/Duplicate/Remove/Clear Buttons
        self.layout.setStretch(4, 1)  # Start/Stop Buttons
        self.layout.setStretch(5, 1)  # Feedback Label
        self.layout.setStretch(6, 20) # Feedback Display

        self.setLayout(self.layout)

        self.ros2_thread = ROS2Thread(self)
        self.ros2_thread.start()

        self.load_default_waypoints()
        self.update_button_states()

    def load_default_waypoints(self):
        
        # Define the specific file for default waypoints
        default_file_path = os.path.join(self.default_waypoints_dir, "sim_waypoints.json")
        self.get_logger().info(f"Attempting to load default waypoints from: {default_file_path}")

        if not os.path.exists(default_file_path):
            self.get_logger().warn(
                f"Default waypoints file not found at {default_file_path}. "
                "No default waypoints will be loaded."
            )
            return

        try:
            with open(default_file_path, "r") as f:
                default_waypoints_data = json.load(f)

            for leg_data in default_waypoints_data.get("legs", []):
                waypoint = {
                    "name": leg_data.get("name", "DefaultWaypoint"),
                    "type": leg_data.get("type", "gps"),
                    "latitude": leg_data.get("latitude", 0.0),
                    "longitude": leg_data.get("longitude", 0.0),
                }
                if waypoint["type"] == "aruco":
                    waypoint["tag_id"] = int(leg_data.get("tag_id", 0))
                elif waypoint["type"] == "obj":
                    waypoint["object"] = leg_data.get("object", "")
                
                self.waypoints.append(waypoint)
            
            if self.waypoints:
                self.get_logger().info(f"Successfully loaded {len(self.waypoints)} default waypoints from {default_file_path}.")
            else:
                self.get_logger().info(f"No valid 'legs' found in {default_file_path} or file was empty.")

            self.update_waypoint_list()

        except FileNotFoundError:
            self.get_logger().error(f"Default waypoints file disappeared: {default_file_path}")
        except json.JSONDecodeError as e:
            self.get_logger().error(f"Error decoding JSON from {default_file_path}: {e}")
        except Exception as e:
            self.get_logger().error(f"Error loading default waypoints from {default_file_path}: {e}")

    def format_feedback_text(self, text):
        item = QListWidgetItem(text)
        if "[SUCCESS]" in text:
            item.setForeground(QColor("green"))
        elif "[FATAL]" in text or "[ERROR]" in text:
            item.setForeground(QColor("red"))
        elif "[WARN]" in text:
            item.setForeground(QColor("orange"))
        return item

    def closeEvent(self, event):
        self.close_flag = True
        self.stop_task()
        self.ros2_thread.stop()
        self.ros2_thread.wait()
        event.accept()

    def update_button_states(self):
        task_running = (
            self.goal_handle is not None
            and self.goal_handle.status == GoalStatus.STATUS_EXECUTING
        )
        self.start_button.setEnabled(not task_running and len(self.waypoints) > 0)
        self.stop_button.setEnabled(task_running)
        self.save_button.setEnabled(len(self.waypoints) > 0)  # True if >0, False if 0
        self.preview_button.setEnabled(len(self.waypoints) > 0)

    def open_add_waypoint_dialog(self):
        self.get_logger().info("Adding waypoint...")
        dialog = WaypointDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            waypoint_data = dialog.get_waypoint_data()
            if waypoint_data:
                self.waypoints.append(waypoint_data)
                self.update_waypoint_list()
        self.update_button_states()

    def open_edit_waypoint_dialog(self):
        self.get_logger().info("Editing waypoint...")
        selected_item = self.waypoint_list.currentItem()
        if selected_item:
            index = self.waypoint_list.row(selected_item)
            waypoint_data = self.waypoints[index]
            dialog = WaypointDialog(self)
            dialog.name_edit.setText(waypoint_data["name"])
            dialog.type_combo.setCurrentText(waypoint_data["type"])
            dialog.latitude_edit.setText(str(waypoint_data["latitude"]))
            dialog.longitude_edit.setText(str(waypoint_data["longitude"]))
            if waypoint_data["type"] == "aruco":
                dialog.tag_id_combo.setCurrentText(str(waypoint_data.get("tag_id", 0)))
            elif waypoint_data["type"] == "obj":
                dialog.object_combo.setCurrentText(waypoint_data.get("object", ""))

            dialog.update_fields_visibility()

            if dialog.exec_() == QDialog.Accepted:
                updated_waypoint_data = dialog.get_waypoint_data()
                if updated_waypoint_data:
                    self.waypoints[index] = updated_waypoint_data
                    self.update_waypoint_list()
                    self.waypoint_list.setCurrentRow(index)
        self.update_button_states()

    def duplicate_waypoint(self):
        self.get_logger().info("Duplicating waypoint...")
        selected_item = self.waypoint_list.currentItem()
        if selected_item:
            index = self.waypoint_list.row(selected_item)
            waypoint_data = self.waypoints[index]
            new_waypoint_data = waypoint_data.copy()
            new_waypoint_data["name"] += "_copy"
            self.waypoints.insert(index + 1, new_waypoint_data)
            self.update_waypoint_list()
            self.waypoint_list.setCurrentRow(
                index + 1
            )
        self.update_button_states()

    def remove_waypoint(self):
        self.get_logger().info("Removing waypoint...")
        selected_item = self.waypoint_list.currentItem()
        if selected_item:
            index = self.waypoint_list.row(selected_item)
            del self.waypoints[index]
            self.update_waypoint_list()
            if index < len(self.waypoints):
                self.waypoint_list.setCurrentRow(index)
            elif len(self.waypoints) > 0:
                self.waypoint_list.setCurrentRow(index - 1)
        self.update_button_states()

    def clear_waypoints(self):
        self.get_logger().info("Clearing waypoints...")
        reply = QMessageBox.question(
            self,
            "Clear Waypoints",
            "Are you sure you want to clear all waypoints?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.waypoints = []
            self.update_waypoint_list()
            self.update_button_states()

    def update_waypoint_list(self):
        current_row = self.waypoint_list.currentRow()
        self.waypoint_list.clear()
        for waypoint in self.waypoints:
            self.waypoint_list.addItem(str(waypoint))
        if (
            0 <= current_row < self.waypoint_list.count()
        ):
            self.waypoint_list.setCurrentRow(current_row)

    def save_waypoints_to_file(self):
        self.get_logger().info("Saving waypoints to file...")
        if not self.waypoints:
            QMessageBox.information(
                self, "No Waypoints", "There are no waypoints to save."
            )
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Save Waypoints File",
            self.default_waypoints_dir,
            "JSON Files (*.json);;All Files (*)",
            options=options,
        )
        if fileName:
            if not fileName.endswith(".json"):
                fileName += ".json"
            try:
                with open(fileName, "w") as f:
                    json.dump({"legs": self.waypoints}, f, indent=4)
                self.get_logger().info(f"Waypoints saved to {fileName}")
                # Update default_waypoints_dir to the directory where the file was saved
                self.default_waypoints_dir = os.path.dirname(fileName)
            except Exception as e:
                self.get_logger().error(f"Error saving waypoints: {e}")
                QMessageBox.critical(
                    self, "Error", f"Could not save waypoints to file: {e}"
                )

    def load_waypoints_from_file(self):
        self.get_logger().info("Loading waypoints from file...")
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Load Waypoints File",
            self.default_waypoints_dir,
            "JSON Files (*.json);;All Files (*)",
            options=options,
        )
        if fileName:
            try:
                with open(fileName, "r") as f:
                    data = json.load(f)
                if "legs" in data and isinstance(data["legs"], list):
                    self.waypoints = []
                    loaded_count = 0
                    for leg_data in data["legs"]:
                        if (
                            isinstance(leg_data, dict)
                            and "name" in leg_data
                            and "type" in leg_data
                        ):
                            self.waypoints.append(leg_data)
                            loaded_count += 1
                        else:
                            self.get_logger().warn(
                                f"Skipping invalid waypoint data: {leg_data}"
                            )
                    self.update_waypoint_list()
                    self.update_button_states()
                    self.get_logger().info(
                        f"Loaded {loaded_count} waypoints from {fileName}"
                    )
                    # Update default_waypoints_dir to the directory from where the file was loaded
                    self.default_waypoints_dir = os.path.dirname(fileName)
                else:
                    raise ValueError(
                        "Invalid waypoint file format. 'legs' array not found."
                    )
            except Exception as e:
                self.get_logger().error(f"Error loading waypoints: {e}")
                QMessageBox.critical(
                    self, "Error", f"Could not load waypoints from file: {e}"
                )

    def preview_waypoints(self):
        self.get_logger().info("Previewing waypoints...")
        marker_array_msg = MarkerArray()

        # Clear old markers
        clear_marker = Marker()
        clear_marker.header.frame_id = "map"
        clear_marker.header.stamp = self.get_clock().now().to_msg()
        clear_marker.ns = "waypoint_preview"
        clear_marker.id = 0  # ID 0 with DELETEALL action clears all markers in namespace
        clear_marker.action = Marker.DELETEALL
        marker_array_msg.markers.append(clear_marker)

        for i, wp_data in enumerate(self.waypoints):
            marker = Marker()
            marker.header.frame_id = "map"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "waypoint_preview"
            marker.id = i + 1  # Ensure unique IDs, starting from 1
            marker.type = Marker.TEXT_VIEW_FACING
            marker.action = Marker.ADD

            # Use longitude for X and latitude for Y as per common mapviz conventions
            marker.pose.position.x = float(wp_data.get("longitude", 0.0))
            marker.pose.position.y = float(wp_data.get("latitude", 0.0))
            marker.pose.position.z = 0.5  # Slight offset from the ground

            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0  # No rotation

            marker.scale.x = 0.0 # Not used for TEXT_VIEW_FACING
            marker.scale.y = 0.0 # Not used for TEXT_VIEW_FACING
            marker.scale.z = 0.5  # Text height

            marker.color.r = 1.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            marker.color.a = 1.0  # Opaque yellow

            marker.text = str(wp_data.get("name", f"WP {i+1}"))

            # Lifetime: 0 means permanent until deleted/updated
            marker.lifetime = rclpy.duration.Duration(seconds=0).to_msg()

            marker_array_msg.markers.append(marker)

        self.marker_publisher.publish(marker_array_msg)
        self.get_logger().info(f"Published {len(self.waypoints)} waypoint previews.")

    def start_task(self):
        self.get_logger().info("Starting task...")
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("Action server not available after 2 seconds!")
            QMessageBox.critical(self, "Error", "Action server not available!")
            return

        if not self.waypoints:
            QMessageBox.warning(self, "Warning", "No waypoints to send.")
            return

        goal_msg = AutonomyTask.Goal()
        goal_msg.legs = []
        for wp in self.waypoints:
            leg_msg = AutonomyLeg()
            leg_msg.name = wp.get("name", "")
            leg_msg.type = wp.get("type", "")
            leg_msg.latitude = float(wp.get("latitude", 0.0))
            leg_msg.longitude = float(wp.get("longitude", 0.0))

            if leg_msg.type == "aruco":
                leg_msg.tag_id = int(wp.get("tag_id", 0))
                leg_msg.object = ""
            elif leg_msg.type == "obj":
                leg_msg.object = wp.get("object", "")
                leg_msg.tag_id = 0
            else:
                leg_msg.tag_id = 0
                leg_msg.object = ""

            goal_msg.legs.append(leg_msg)

        self.feedback_display.clear()
        send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.goal_feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)
        self.update_button_states()

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.feedback_display.addItem(
                self.format_feedback_text(
                    "[ERROR] [gui] Goal rejected by action server"
                )
            )
        else:
            self.feedback_display.addItem(
                self.format_feedback_text("[gui] Goal accepted by action server:")
            )
            for wp in self.waypoints:
                self.feedback_display.addItem(" - " + str(wp))
            get_result_future = self.goal_handle.get_result_async()
            get_result_future.add_done_callback(self.get_result_callback)
            self.feedback_display.scrollToBottom()
        self.update_button_states()

    def goal_feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        formatted_text = self.format_feedback_text(f"{feedback.status}")
        self.feedback_display.addItem(formatted_text)
        self.feedback_display.scrollToBottom()
        self.update_button_states()

    def get_result_callback(self, future):
        result = future.result()
        formatted_text = self.format_feedback_text(f"[gui] {result.result.msg}")
        self.feedback_display.addItem(formatted_text)
        self.feedback_display.scrollToBottom()
        self.goal_handle = None
        self.update_button_states()

    def stop_task(self):
        self.get_logger().info("Stopping task...")
        client = self.create_client(
            CancelGoal,
            "/exec_autonomy_task/_action/cancel_goal",
            callback_group=self.callback_group,
        )

        if not client.wait_for_service(timeout_sec=2.0):
            if not self.close_flag:
                self.get_logger().error(
                    "CancelGoal service not available after 2 seconds!"
                )
                QMessageBox.critical(self, "Error", "CancelGoal service not available!")
            else:
                self.get_logger().warn(
                    "CancelGoal service not available after 2 seconds!"
                )
            return

        request = CancelGoal.Request()
        future = client.call_async(request)
        future.add_done_callback(self.cancel_response_callback)
        self.update_button_states()

    def cancel_response_callback(self, future):
        response = future.result()
        if response.return_code == CancelGoal.Response.ERROR_NONE:
            self.feedback_display.addItem(
                self.format_feedback_text("[gui] Cancel request sent successfully")
            )
            self.goal_handle = None
        else:
            self.feedback_display.addItem(
                self.format_feedback_text("[ERROR] [gui] Failed to send cancel request")
            )
        self.feedback_display.scrollToBottom()
        self.update_button_states()


def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    gui = AutonomyGUI()
    gui.show()
    exit_code = app.exec_()
    gui.destroy_node()
    rclpy.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()