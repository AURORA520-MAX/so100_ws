#!/usr/bin/env python3
"""SO-ARM100 驱动 — 每舵机校准 + URDF映射 + MoveIt2轨迹执行"""

import serial, struct, math, rclpy, time, threading
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from control_msgs.action import FollowJointTrajectory

FRAME_HEADER = 0x55
CMD_SERVO_MOVE = 0x03

SERVO_CALIB = {
    1: (0,   500, 1000),
    2: (4,   500,  966),
    3: (104, 496,  917),
    4: (85,  497,  977),
    5: (0,   500, 1000),
    6: (14,  500,  560),
}

CMD_RANGE = 240.0
CMD_HALF = 120.0

JOINT_ADJUST = {
    1: (120,  1),
    2: (224, -1),
    3: (30,  -1),
    4: (153,  1),
    5: (210, -1),
    6: (130, -1),
}

URDF_LIMITS = {
    1: (-2.0, 2.0),
    2: (0.0, 3.5),
    3: (-3.1416, 0.0),
    4: (-2.5, 1.2),
    5: (-3.1416, 3.1416),
    6: (-0.2, 2.0),
}

JOINT_NAMES = ["shoulder_pan","shoulder_lift","elbow_flex","wrist_flex","wrist_roll","gripper"]
JOINT_IDS = [1,2,3,4,5,6]


class So100ArmDriver(Node):
    def __init__(self):
        super().__init__("so100_arm_driver")
        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baudrate", 9600)
        port = self.get_parameter("port").value
        baud = self.get_parameter("baudrate").value
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.get_logger().info(f"OK serial: {port} @ {baud}")

        self.cmd = [120.0, 120.0, 120.0, 120.0, 60.0, 60.0]
        self._executing = False
        self._traj_lock = threading.Lock()

        # 直接角度命令
        self.sub = self.create_subscription(
            Float64MultiArray, "/joint_commands", self.on_cmd, 10)

        # MoveIt2 轨迹执行 Action Server
        self._action_server = ActionServer(
            self, FollowJointTrajectory,
            'arm_controller/follow_joint_trajectory',
            execute_callback=self.on_traj_execute,
            goal_callback=self.on_traj_goal,
            callback_group=ReentrantCallbackGroup(),
        )

        # 关节状态发布
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.timer = self.create_timer(0.05, self.pub_state)
        self.get_logger().info("Driver ready. MoveIt2 action server: arm_controller/follow_joint_trajectory")

    def on_traj_goal(self, goal_handle):
        """Accept all trajectory goals"""
        traj = goal_handle.trajectory  # Humble: goal_handle IS the Goal msg
        self.get_logger().info(f"Received trajectory goal: {len(traj.points)} points")
        return GoalResponse.ACCEPT

    def on_traj_execute(self, goal_handle):
        """Execute a FollowJointTrajectory goal"""
        traj = goal_handle.request.trajectory  # execute_callback: ServerGoalHandle
        joint_names = traj.joint_names

        with self._traj_lock:
            self._executing = True

        result = FollowJointTrajectory.Result()
        feedback = FollowJointTrajectory.Feedback()

        start_time = self.get_clock().now()

        for point_idx, point in enumerate(traj.points):
            # 检查是否被取消
            if goal_handle.is_cancel_requested:
                result.error_code = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                goal_handle.canceled()
                self.get_logger().info("Trajectory cancelled")
                with self._traj_lock:
                    self._executing = False
                return result

            # MoveIt2输出URDF弧度 → 反向应用JOINT_ADJUST转舵机角度
            targets = []
            for jname, pos_rad in zip(joint_names, point.positions):
                if jname in JOINT_NAMES:
                    i = JOINT_NAMES.index(jname)
                    sid = JOINT_IDS[i]
                    offset, direction = JOINT_ADJUST[sid]
                    # 逆变换: urdf_rad = (cmd_deg - offset) * direction * pi/180
                    #        → cmd_deg = urdf_rad * 180/pi / direction + offset
                    cmd_deg = pos_rad * 180.0 / math.pi / direction + offset
                    self.cmd[i] = cmd_deg
                    pulse = self._deg2pulse(sid, cmd_deg)
                    targets.append((sid, pulse))

            # 计算运动时间（秒→毫秒）
            t_from_start = point.time_from_start.sec + point.time_from_start.nanosec * 1e-9
            if point_idx < len(traj.points) - 1:
                next_t = traj.points[point_idx + 1].time_from_start.sec + \
                         traj.points[point_idx + 1].time_from_start.nanosec * 1e-9
                dt = next_t - t_from_start
            else:
                dt = 0.5  # 最后一个点用500ms

            time_ms = max(50, min(30000, int(dt * 1000)))
            self._send(targets, time_ms)

            # 发布反馈
            feedback.joint_names = joint_names
            feedback.actual.positions = point.positions
            feedback.desired.positions = point.positions
            goal_handle.publish_feedback(feedback)

            self.get_logger().info(f'Traj point {point_idx+1}/{len(traj.points)}: {[round(x,1) for x in self.cmd]}')

            # 等待这个点的运动时间
            time.sleep(dt)
        
        goal_handle.succeed()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL

        with self._traj_lock:
            self._executing = False

        self.get_logger().info("Trajectory execution completed!")
        return result

    def on_cmd(self, msg):
        if len(msg.data) != 6:
            self.get_logger().warn(f"bad data len: {len(msg.data)}")
            return
        self.cmd = list(msg.data)
        targets = []
        for i, deg in enumerate(self.cmd):
            sid = JOINT_IDS[i]
            pulse = self._deg2pulse(sid, deg)
            targets.append((sid, pulse))
        self._send(targets)

    def _deg2pulse(self, sid, deg):
        mn, mid, mx = SERVO_CALIB[sid]
        deg = max(0.0, min(CMD_RANGE, deg))
        if deg <= CMD_HALF:
            span = mid - mn
            return int(mn + deg / CMD_HALF * span) if span else mn
        else:
            span = mx - mid
            return int(mid + (deg - CMD_HALF) / CMD_HALF * span) if span else mid

    def _send(self, targets, ms=1000):
        n = len(targets)
        buf = bytearray([0x55, 0x55, n*3+5, CMD_SERVO_MOVE, n])
        buf.extend(struct.pack("<H", ms))
        for sid, pulse in targets:
            mn, _, mx = SERVO_CALIB[sid]
            pulse = max(mn, min(mx, pulse))
            buf.extend([sid, pulse & 0xFF, pulse >> 8])
        self.ser.write(buf)

    def pub_state(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = []
        for i, (name, sid) in enumerate(zip(JOINT_NAMES, JOINT_IDS)):
            offset, direction = JOINT_ADJUST[sid]
            rad = (self.cmd[i] - offset) * direction * math.pi / 180.0
            lo, hi = URDF_LIMITS[sid]
            rad = max(lo, min(hi, rad))
            msg.position.append(rad)
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = So100ArmDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.ser.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
