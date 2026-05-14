#!/usr/bin/env python3
import rclpy
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import tkinter as tk

def main():
    rclpy.init()
    node = rclpy.create_node('mecanum_arm_dashboard')
    
    cmd_pub = node.create_publisher(Twist, '/mecanum_controller/reference_unstamped', 10)
    arm_pub = node.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
    pris_pub = node.create_publisher(JointTrajectory, '/prismatic_controller/joint_trajectory', 10)

    root = tk.Tk()
    root.title("Điều Khiển Mecanum")
    root.geometry("450x500")

    x_var = tk.DoubleVar()
    y_var = tk.DoubleVar()
    z_var = tk.DoubleVar()
    arm_var = tk.DoubleVar()
    pris_var = tk.DoubleVar()

    # VÒNG LẶP LIÊN TỤC: Tự động bơm tín hiệu di chuyển ở tần số 20Hz
    def publish_vel_loop():
        msg = Twist()
        msg.linear.x = x_var.get()
        msg.linear.y = y_var.get()
        msg.angular.z = z_var.get()
        cmd_pub.publish(msg)
        root.after(50, publish_vel_loop)

    publish_vel_loop()

    def publish_arm(val):
        msg = JointTrajectory()
        msg.joint_names = ['Arm_Joint']
        point = JointTrajectoryPoint()
        point.positions = [arm_var.get()]
        point.time_from_start = Duration(sec=0, nanosec=500000000)
        msg.points = [point]
        arm_pub.publish(msg)

    def publish_pris(val):
        msg = JointTrajectory()
        msg.joint_names = ['Prismatic_Joint']
        point = JointTrajectoryPoint()
        point.positions = [pris_var.get()]
        point.time_from_start = Duration(sec=0, nanosec=500000000)
        msg.points = [point]
        pris_pub.publish(msg)

    def reset(event=None):
        x_var.set(0.0)
        y_var.set(0.0)
        z_var.set(0.0)
        # Bơm ngay lệnh 0 không chờ vòng lặp 50ms
        msg = Twist()
        cmd_pub.publish(msg)

    # Bind phím Space để phanh khẩn cấp
    root.bind('<space>', reset)

    tk.Label(root, text="[ KHUNG GẦM MECANUM ]", font=("Arial", 12, "bold"), fg="blue").pack(pady=5)
    tk.Scale(root, variable=x_var, from_=1.0, to=-1.0, resolution=0.1, label="Tiến / Lùi", orient="horizontal").pack(fill="x", padx=20)
    tk.Scale(root, variable=y_var, from_=1.0, to=-1.0, resolution=0.1, label="Trượt Trái / Phải", orient="horizontal").pack(fill="x", padx=20)
    tk.Scale(root, variable=z_var, from_=1.0, to=-1.0, resolution=0.1, label="Xoay Tròn", orient="horizontal").pack(fill="x", padx=20)

    tk.Label(root, text="[ CÁNH TAY Robot]", font=("Arial", 12, "bold"), fg="green").pack(pady=10)
    tk.Scale(root, variable=arm_var, from_=0.0, to=1.396, resolution=0.01, label="Nâng / Hạ Cánh Tay (Rad)", orient="horizontal", command=publish_arm).pack(fill="x", padx=20)
    tk.Scale(root, variable=pris_var, from_=0.0, to=0.0167, resolution=0.001, label="Thò / Thụt Trục Đẩy (Meter)", orient="horizontal", command=publish_pris).pack(fill="x", padx=20)

    tk.Button(root, text="PHANH KHẨN CẤP XE  [SPACE]", command=reset, bg="red", fg="white", font=("Arial", 12, "bold")).pack(pady=20)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
