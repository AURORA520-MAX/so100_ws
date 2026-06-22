#!/usr/bin/env python3
"""SO-ARM100 重复动作演示脚本"""

import rclpy
import time
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray


class RepeatMotion(Node):
    def __init__(self):
        super().__init__("repeat_motion")
        self.pub = self.create_publisher(Float64MultiArray, "/joint_commands", 10)
        self.get_logger().info("重复动作节点已就绪")

    def move(self, angles, wait=1.0):
        """发送关节角度并等待"""
        msg = Float64MultiArray(data=angles)
        self.pub.publish(msg)
        self.get_logger().info(f"发送: {angles}")
        time.sleep(wait)


def main():
    rclpy.init()
    node = RepeatMotion()

    # ----------------------------------------------
    # 定义动作序列（你可修改这些关节角度）
    # [shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper]
    # ----------------------------------------------

    # 动作序列
    MOVE1 = [0,   120, 360, 120, 210, 360]   # 动作1
    MOVE2 = [120, 120, 120, 40,  30,  0  ]   # 动作2
    MOVE3 = [360, 120, 360, 120, 210, 360]   # 动作3

    count = 0
    while rclpy.ok():  # 无限循环，Ctrl+C 停止
        node.get_logger().info(f"===== 第 {count+1} 次循环 =====")

        node.move(MOVE1, wait=1.5)
        time.sleep(1.0)  # 动作间隔
        node.move(MOVE2, wait=1.5)
        time.sleep(1.0)
        node.move(MOVE3, wait=1.5)

        count += 1

    node.get_logger().info("演示完成！")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
