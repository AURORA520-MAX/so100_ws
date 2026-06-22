#!/usr/bin/env python3
"""Joint calibrator: find cmd_angle -> URDF rad mapping per joint"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
import math

JOINTS = ["shoulder_pan","shoulder_lift","elbow_flex","wrist_flex","wrist_roll","gripper"]

class JointCalibrator(Node):
    def __init__(self):
        super().__init__("joint_calibrator")
        self.declare_parameter("joint_id", 2)
        self.joint_id = self.get_parameter("joint_id").value
        self.joint_name = JOINTS[self.joint_id - 1]
        self.current_urdf_rad = 0.0
        self.sub = self.create_subscription(JointState, "/joint_states", self.js_cb, 10)
        self.pub = self.create_publisher(Float64MultiArray, "/joint_commands", 10)
        self.get_logger().info(f"Calibrating ID{self.joint_id} ({self.joint_name})")
        self.get_logger().info("Commands: m <deg> = move,  r = read URDF pos,  q = quit")
        self.run_cli()

    def js_cb(self, msg):
        try:
            idx = msg.name.index(self.joint_name)
            self.current_urdf_rad = msg.position[idx]
        except ValueError:
            pass

    def move_to(self, deg):
        cmd = [120.0] * 6
        cmd[self.joint_id - 1] = float(deg)
        self.pub.publish(Float64MultiArray(data=cmd))

    def show_state(self):
        urdf_deg = self.current_urdf_rad * 180.0 / math.pi
        self.get_logger().info(f"URDF position: {urdf_deg:.1f} deg ({self.current_urdf_rad:.3f} rad)")

    def run_cli(self):
        try:
            while rclpy.ok():
                line = input(f"\n[{self.joint_name}] > ").strip()
                if not line:
                    continue
                parts = line.split()
                if parts[0] == "q":
                    break
                elif parts[0] == "r":
                    self.show_state()
                elif parts[0] == "m" and len(parts) > 1:
                    self.move_to(parts[1])
                    self.get_logger().info(f"Moved to {parts[1]} deg")
                else:
                    self.get_logger().info("m <deg> | r | q")
        except (EOFError, KeyboardInterrupt):
            pass
        self.destroy_node()
        rclpy.shutdown()

def main():
    rclpy.init()
    JointCalibrator()

if __name__ == "__main__":
    main()
