#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import psutil
import time

class SlamEvaluator(Node):
    def __init__(self):
        super().__init__('slam_evaluator')
        
        self.target_process_name = 'slam_gmapping' 
        
        self.pid = self.find_process_id(self.target_process_name)
        
        # Khởi tạo biến cho Tần số Map
        self.last_map_time = time.time()
        self.map_count = 0
        
        # Đăng ký theo dõi topic /map
        self.subscription = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10)
            
        # Timer in kết quả mỗi 2 giây
        self.timer = self.create_timer(2.0, self.print_metrics)

    def find_process_id(self, name):
        """Tìm ID của tiến trình SLAM đang chạy"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                
                if proc.info['cmdline'] and any(name in cmd for cmd in proc.info['cmdline']):
                    self.get_logger().info(f'Đã tìm thấy tiến trình {name} (PID: {proc.info["pid"]})')
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.get_logger().warn(f'Không tìm thấy tiến trình: {name}')
        return None

    def map_callback(self, msg):
        """Tính toán độ trễ / tần số cập nhật bản đồ"""
        current_time = time.time()
        self.map_latency = current_time - self.last_map_time
        self.last_map_time = current_time
        self.map_count += 1

    def print_metrics(self):
        """In thông số ra terminal"""
        print("\n" + "="*40)
        print("="*40)
        
        # 1. Đo lường Map (Độ trễ)
        if self.map_count > 1:
            hz = 1.0 / self.map_latency if self.map_latency > 0 else 0.0
            print(f"[Bản đồ] Tần số cập nhật: {hz:.2f} Hz")
            print(f"[Bản đồ] Độ trễ (Latency): {self.map_latency:.4f} giây")
        else:
            print("[Bản đồ] Đang chờ dữ liệu /map...")

        # 2. Đo lường CPU & RAM
        if self.pid:
            try:
                proc = psutil.Process(self.pid)
                cpu_usage = proc.cpu_percent(interval=0.1)
                ram_usage_mb = proc.memory_info().rss / (1024 * 1024)
                
                print(f"[Tài nguyên] Tiến trình: {self.target_process_name}")
                print(f"[Tài nguyên] CPU Chiếm dụng: {cpu_usage:.1f} %")
                print(f"[Tài nguyên] RAM Chiếm dụng: {ram_usage_mb:.2f} MB")
            except psutil.NoSuchProcess:
                print(f"[Cảnh báo] Tiến trình {self.pid} đã chết.")
        print("="*40)

def main(args=None):
    rclpy.init(args=args)
    node = SlamEvaluator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
