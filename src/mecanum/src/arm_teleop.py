import argparse
import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

msg_template = """
Điều khiển Robot bằng bàn phím:
---------------------------
Chế độ điều khiển: {mode}

    w: tiến
    s: lùi
    q: quay trái
    e: quay phải
"""

mecanum_extra = """
    a: lùi trái / dịch trái
    d: tiến phải / dịch phải
"""

stop_help = "Space hoặc x : Dừng xe\nCTRL-C để thoát\n"

class TeleopMecanum(Node):
    def __init__(self, drive_type='mecanum', lin_speed=0.5, ang_speed=1.0):
        super().__init__('teleop_mecanum_node')
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.drive_type = drive_type
        self.lin_speed = lin_speed
        self.ang_speed = ang_speed
        self.settings = termios.tcgetattr(sys.stdin)

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def help_text(self):
        help_text = msg_template.format(mode=self.drive_type)
        if self.drive_type == 'mecanum':
            help_text += mecanum_extra
        help_text += '\n' + stop_help
        return help_text

    def run(self):
        print(self.help_text())
        try:
            while rclpy.ok():
                key = self.get_key()
                vel = Twist()

                if key == 'w':
                    vel.linear.x = self.lin_speed
                elif key == 's':
                    vel.linear.x = -self.lin_speed
                elif key == 'a' and self.drive_type == 'mecanum':
                    vel.linear.y = self.lin_speed
                elif key == 'd' and self.drive_type == 'mecanum':
                    vel.linear.y = -self.lin_speed
                elif key == 'q':
                    vel.angular.z = self.ang_speed
                elif key == 'e':
                    vel.angular.z = -self.ang_speed
                elif key == 'x' or key == ' ':
                    vel.linear.x = 0.0
                    vel.linear.y = 0.0
                    vel.angular.z = 0.0

                self.cmd_pub.publish(vel)

                if key == '\x03':
                    break
        except Exception as e:
            print(f"Error: {e}")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)


def main(args=None):
    parser = argparse.ArgumentParser(description='Teleop keyboard for mecanum/ackermann/tracked drive')
    parser.add_argument('--drive-type', choices=['mecanum', 'tracked', 'ackermann'], default='mecanum',
                        help='Chế độ điều khiển khi dùng cmd_vel')
    parser.add_argument('--lin-speed', type=float, default=0.5, help='Tốc độ tiến/lùi (m/s)')
    parser.add_argument('--ang-speed', type=float, default=1.0, help='Tốc độ quay (rad/s)')
    options, unknown = parser.parse_known_args()

    rclpy.init(args=unknown)
    node = TeleopMecanum(options.drive_type, options.lin_speed, options.ang_speed)
    node.run()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

