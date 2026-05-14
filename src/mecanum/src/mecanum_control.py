import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class RobotController(Node):
    def __init__(self):
        super().__init__('robot_controller_node')
        
        
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
       
        self.joint_pub = self.create_publisher(JointTrajectory, 'set_joint_trajectory', 10)
        
      
        self.timer = self.create_timer(0.1, self.execute_move)
        self.get_logger().info('Đang khởi động hệ thống điều khiển...')

    def execute_move(self):
       
        vel = Twist()
        vel.linear.x = 0.2  
        vel.linear.y = 0.5 
        self.cmd_pub.publish(vel)

       
        traj = JointTrajectory()
        traj.joint_names = ['Arm_Joint', 'Prismatic_Joint'] 
        
        point = JointTrajectoryPoint()
        point.positions = [0.8, 0.01] 
        point.time_from_start = Duration(sec=1)
        
        traj.points.append(point)
        self.joint_pub.publish(traj)

def main():
    rclpy.init()
    node = RobotController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
