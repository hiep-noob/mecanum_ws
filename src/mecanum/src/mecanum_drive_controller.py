import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64

class MecanumDriveController(Node):
    def __init__(self):
        super().__init__('mecanum_drive_controller')

        self.declare_parameter('drive_type', 'mecanum')
        self.declare_parameter('wheel_radius', 0.0325)
        self.declare_parameter('wheel_base_length', 0.12)
        self.declare_parameter('wheel_base_width', 0.18)
        self.declare_parameter('max_wheel_speed', 50.0)

        self.drive_type = self.get_parameter('drive_type').value
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_base_length = self.get_parameter('wheel_base_length').value
        self.wheel_base_width = self.get_parameter('wheel_base_width').value
        self.max_wheel_speed = self.get_parameter('max_wheel_speed').value

        self.cmd_vel_sub = self.create_subscription(
            Twist, 'cmd_vel', self.cmd_vel_callback, 10)

        self.wheel_pubs = {
            'fl': self.create_publisher(Float64, 'front_left_wheel_velocity_controller/velocity_command', 10),
            'fr': self.create_publisher(Float64, 'front_right_wheel_velocity_controller/velocity_command', 10),
            'rl': self.create_publisher(Float64, 'rear_left_wheel_velocity_controller/velocity_command', 10),
            'rr': self.create_publisher(Float64, 'rear_right_wheel_velocity_controller/velocity_command', 10),
        }

    def clamp_wheel(self, speed):
        if abs(speed) > self.max_wheel_speed:
            return math.copysign(self.max_wheel_speed, speed)
        return speed

    def cmd_vel_callback(self, msg):
        vx = msg.linear.x
        omega = msg.angular.z
        vy = msg.linear.y if self.drive_type == 'mecanum' else 0.0

        if self.drive_type == 'mecanum':
            # lx, ly là khoảng cách từ tâm đến trục bánh xe
            lx = self.wheel_base_length / 2.0
            ly = self.wheel_base_width / 2.0
            R = self.wheel_radius
            
            # Công thức động học Mecanum chuẩn hệ X
            w_fl = (vx - vy - (lx + ly) * omega) / R
            w_fr = (vx + vy + (lx + ly) * omega) / R
            w_rl = (vx + vy - (lx + ly) * omega) / R
            w_rr = (vx - vy + (lx + ly) * omega) / R

        elif self.drive_type in ['tracked', 'ackermann']:
            track_width = self.wheel_base_width
            left_speed = vx - omega * track_width / 2.0
            right_speed = vx + omega * track_width / 2.0
            w_fl = w_rl = left_speed / self.wheel_radius
            w_fr = w_rr = right_speed / self.wheel_radius
        else:
            self.get_logger().warn(f'Unknown drive_type "{self.drive_type}", defaulting to mecanum')
            lx = self.wheel_base_length / 2.0
            ly = self.wheel_base_width / 2.0
            R = self.wheel_radius
            w_fl = (vx - vy - (lx + ly) * omega) / R
            w_fr = (vx + vy + (lx + ly) * omega) / R
            w_rl = (vx + vy - (lx + ly) * omega) / R
            w_rr = (vx - vy + (lx + ly) * omega) / R

        # Giới hạn vận tốc
        w_fl = self.clamp_wheel(w_fl)
        w_fr = self.clamp_wheel(w_fr)
        w_rl = self.clamp_wheel(w_rl)
        w_rr = self.clamp_wheel(w_rr)

        # Publish lệnh xoay bánh xe
        self.wheel_pubs['fl'].publish(Float64(data=w_fl))
        self.wheel_pubs['fr'].publish(Float64(data=w_fr))
        self.wheel_pubs['rl'].publish(Float64(data=w_rl))
        self.wheel_pubs['rr'].publish(Float64(data=w_rr))

def main():
    rclpy.init()
    node = MecanumDriveController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
