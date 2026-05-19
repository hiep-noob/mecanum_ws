#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import psutil
import time

class Slam3DEvaluator(Node):
    def __init__(self):
        super().__init__('slam_3d_evaluator')
        
        self.target_process_name = 'rtabmap' 
        self.map_topic = '/cloud_map'
        #self.target_process_name = 'cartographer_node'
        #self.map_topic = '/scan_matched_points2' 
        
        self.pid = self.find_process_id(self.target_process_name)
        
        self.last_map_time = time.time()
        self.map_count = 0
        
        # Đăng ký theo dõi topic Đám mây điểm 3D (PointCloud2)
        self.subscription = self.create_subscription(
            PointCloud2,
            self.map_topic,
            self.map_callback,
            10)  
            
        self.timer = self.create_timer(2.0, self.print_metrics)

    def find_process_id(self, name):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any(name in cmd for cmd in proc.info['cmdline']):
                    self.get_logger().info(f'Đã khóa mục tiêu tiến trình {name} (PID: {proc.info["pid"]})')
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.get_logger().warn(f'Không tìm thấy tiến trình: {name}')
        return None

    def map_callback(self, msg):
        current_time = time.time()
        self.map_latency = current_time - self.last_map_time
        self.last_map_time = current_time
        self.map_count += 1

    def print_metrics(self):
        print("\n" + "="*45)
        print(" BÁO CÁO ĐÁNH GIÁ 3D SLAM")
        print("="*45)
        
        if self.map_count > 1:
            hz = 1.0 / self.map_latency if self.map_latency > 0 else 0.0
            print(f"[Map 3D] Topic: {self.map_topic}")
            print(f"[Map 3D] Tần số cập nhật: {hz:.2f} Hz")
            print(f"[Map 3D] Độ trễ Render (Latency): {self.map_latency:.4f} giây")
        else:
            print(f"[Map 3D] Đang chờ gói dữ liệu PointCloud2 từ topic '{self.map_topic}'...")

        if self.pid:
            try:
                proc = psutil.Process(self.pid)
                cpu_usage = proc.cpu_percent(interval=1.0)
                ram_usage_mb = proc.memory_info().rss / (1024 * 1024)
                
                print(f"[Tài nguyên] Tiến trình định vị: {self.target_process_name}")
                print(f"[Tài nguyên] Tải CPU: {cpu_usage:.1f} %")
                print(f"[Tài nguyên] RAM Chiếm dụng: {ram_usage_mb:.2f} MB")
            except psutil.NoSuchProcess:
                print(f"[Cảnh báo] Tiến trình PID {self.pid} đã bị ngắt.")
        print("="*45)

def main(args=None):
    rclpy.init(args=args)
    node = Slam3DEvaluator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
