#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

def main():
    rclpy.init()
    navigator = BasicNavigator()
    print("Đang kết nối với Nav2...")
    navigator.waitUntilNav2Active()

    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = navigator.get_clock().now().to_msg()
    
    
    goal_pose.pose.position.x = -7.176366806030273
    goal_pose.pose.position.y = 0.8784542083740234
    
    
    goal_pose.pose.orientation.w = 1.0 

    print("Bắt đầu tính toán đường đi ngắn nhất...")
    navigator.goToPose(goal_pose)

    
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            print(f"> Khoảng cách tới mục tiêu: {feedback.distance_remaining:.2f} mét", end='\r')

    
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        print("\n\n[THÀNH CÔNG] Robot đã đến đúng căn phòng chỉ định!")
    elif result == TaskResult.CANCELED:
        print("\n\n[HỦY] Nhiệm vụ đã bị hủy.")
    elif result == TaskResult.FAILED:
        print("\n\n[THẤT BẠI] Đường đi bị chặn, không thể tính toán quỹ đạo tới phòng.")

    rclpy.shutdown()

if __name__ == '__main__':
    main()
