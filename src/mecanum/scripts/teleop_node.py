#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import sys, tty, termios, threading

# ── Hằng số giới hạn khớp ──────────────────────────
ARM_LOWER, ARM_UPPER = 0.0, 1.396
PRIS_LOWER, PRIS_UPPER = 0.0, 0.01672
ARM_STEP, PRIS_STEP = 0.05, 0.001
LIN_SPEED, ANG_SPEED = 0.3, 1.0

class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('keyboard_teleop')
        
        # Khởi tạo chế độ điều khiển (Sửa lỗi thiếu mode)
        self.mode = 'holonomic' 
        
        # Topic cmd_vel cho mecanum_controller 
        # Dòng 20, đổi thành:
        self.cmd_pub = self.create_publisher(Twist, '/mecanum_controller/cmd_vel_unstamped', 10)
        
        # Topic cho cánh tay và khớp tịnh tiến 
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.pris_pub = self.create_publisher(JointTrajectory, '/prismatic_controller/joint_trajectory', 10)

        self.arm_pos = 0.0
        self.pris_pos = 0.0
        self._twist = Twist()
        
        # Tạo timer để gửi lệnh vận tốc liên tục giúp robot chạy mượt hơn 
        self.create_timer(0.05, self._publish_twist)
        
        self.get_logger().info("\nRobot Ready!")
        self.get_logger().info("Control: W/S (Forward/Back), A/D (Strafe), Q/E (Rotate)")
        self.get_logger().info("Arm: I/K (Up/Down), Prismatic: J/L (In/Out)")
        self.get_logger().info("Press Space to Stop, M to toggle Mode, Ctrl+C to Quit.")

    def _publish_twist(self):
        self.cmd_pub.publish(self._twist)

    def _send_trajectory(self, publisher, joint_name, position):
        """Gửi lệnh đến JointTrajectoryController """
        msg = JointTrajectory()
        msg.joint_names = [joint_name]
        point = JointTrajectoryPoint()
        point.positions = [float(position)]
        # Thời gian 0.1s giúp khớp chuyển động mượt mà, không bị giật vật lý 
        point.time_from_start = Duration(sec=0, nanosec=100000000) 
        msg.points = [point]
        publisher.publish(msg)

    def process_key(self, key: str):
        new_twist = Twist()
        
        # ── Điều khiển Di chuyển (Base) ──
        if key == 'w': 
            new_twist.linear.x = LIN_SPEED
        elif key == 's': 
            new_twist.linear.x = -LIN_SPEED
        elif key == 'a':
            if self.mode == 'holonomic': 
                new_twist.linear.y = LIN_SPEED
            else: 
                new_twist.angular.z = ANG_SPEED * 0.5
        elif key == 'd':
            if self.mode == 'holonomic': 
                new_twist.linear.y = -LIN_SPEED
            else: 
                new_twist.angular.z = -ANG_SPEED * 0.5
        elif key == 'q': 
            new_twist.angular.z = ANG_SPEED
        elif key == 'e': 
            new_twist.angular.z = -ANG_SPEED
        
        # ── Điều khiển Cánh tay (Arm) ──
        elif key == 'i':
            self.arm_pos = min(self.arm_pos + ARM_STEP, ARM_UPPER)
            self._send_trajectory(self.arm_pub, 'Arm_Joint', self.arm_pos)
        elif key == 'k':
            self.arm_pos = max(self.arm_pos - ARM_STEP, ARM_LOWER)
            self._send_trajectory(self.arm_pub, 'Arm_Joint', self.arm_pos)
            
        # ── Điều khiển Khớp tịnh tiến (Prismatic) ──
        elif key == 'j':
            self.pris_pos = min(self.pris_pos + PRIS_STEP, PRIS_UPPER)
            self._send_trajectory(self.pris_pub, 'Prismatic_Joint', self.pris_pos)
        elif key == 'l':
            self.pris_pos = max(self.pris_pos - PRIS_STEP, PRIS_LOWER)
            self._send_trajectory(self.pris_pub, 'Prismatic_Joint', self.pris_pos)
            
        elif key == 'm':
            self.mode = 'ackermann' if self.mode == 'holonomic' else 'holonomic'
            print(f"\nMode changed to: {self.mode.upper()}")
        elif key == ' ':
            new_twist = Twist() # Dừng khẩn cấp

        self._twist = new_twist

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main():
    rclpy.init()
    node = KeyboardTeleop()
    settings = termios.tcgetattr(sys.stdin)
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()

    try:
        while True:
            key = get_key(settings)
            if key == '\x03': 
                break 
            node.process_key(key.lower())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        node.cmd_pub.publish(Twist())
        rclpy.shutdown()

if __name__ == '__main__':
    main()
