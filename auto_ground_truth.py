import os, sys, time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from std_srvs.srv import Empty
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

OUTPUT_DIR = os.path.expanduser("~/mecanum_ws/src/mecanum/maps")
WORLD_FILE = os.path.expanduser("~/mecanum_ws/src/mecanum/worlds/hospital.world")

MAP_NAME = sys.argv[1] if len(sys.argv) > 1 else "hospital_ground_truth"

if len(sys.argv) >= 4:
    init_x = float(sys.argv[2])
    init_y = float(sys.argv[3])
    os.system(f"sed -i 's/<init_robot_x>.*<\\/init_robot_x>/<init_robot_x>{init_x}<\\/init_robot_x>/' {WORLD_FILE}")
    os.system(f"sed -i 's/<init_robot_y>.*<\\/init_robot_y>/<init_robot_y>{init_y}<\\/init_robot_y>/' {WORLD_FILE}")
    print(f"============================================================")
    print(f"[CẬP NHẬT] Đã sửa file world thành xuất phát tại: x={init_x}, y={init_y}")
    print(f"LƯU Ý: Vui lòng BẬT (hoặc TẮT BẬT LẠI) Gazebo ở Terminal khác ngay bây giờ!")
    print(f"============================================================\n")

class GroundTruthMapSaver(Node):
    def __init__(self):
        super().__init__('ground_truth_map_saver')
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.sub = self.create_subscription(OccupancyGrid, '/map_from_gazebo', self.cb, qos)
        self.cli = self.create_client(Empty, '/gazebo_2d_map_plugin/generate_map')
        self.latest_msg = None

    def cb(self, msg):
        self.latest_msg = msg

    def call_generate_map(self):
        self.get_logger().info('Đang đợi Service tạo bản đồ của Gazebo...')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            pass
        self.get_logger().info('Đã kết nối! Gọi service /gazebo_2d_map_plugin/generate_map ...')
        self.cli.call_async(Empty.Request())

    def wait_and_save(self):
        last_known = 0
        last_change_time = time.time()
        
        self.get_logger().info("Đang chờ dữ liệu bản đồ...")
        
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            
            if self.latest_msg is not None:
                known = sum(1 for v in self.latest_msg.data if v != -1)
                
                if known > last_known:
                    last_known = known
                    last_change_time = time.time()
                    self.get_logger().info(f"Đang loang sóng Wavefront: {known} ô...")
                
                elif time.time() - last_change_time > 15.0 and known > 0:
                    self.save_to_disk(self.latest_msg)
                    return

    def save_to_disk(self, msg):
        w, h = msg.info.width, msg.info.height
        img = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                val = msg.data[y * w + x]
                idx = (h - 1 - y) * w + x
                if val == -1: img[idx] = 205
                elif val == 0: img[idx] = 254
                elif val == 100: img[idx] = 0
                else: img[idx] = int(254 - (val / 100) * 254)
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, f"{MAP_NAME}.pgm"), "wb") as f:
            f.write(f"P5\n{w} {h}\n255\n".encode())
            f.write(img)
        with open(os.path.join(OUTPUT_DIR, f"{MAP_NAME}.yaml"), "w") as f:
            f.write(f"image: {MAP_NAME}.pgm\nresolution: {msg.info.resolution}\norigin: [{msg.info.origin.position.x}, {msg.info.origin.position.y}, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n")
        self.get_logger().info(f"Đã lưu bản đồ thành công tại: {OUTPUT_DIR}/{MAP_NAME}.pgm")

def main():
    rclpy.init()
    node = GroundTruthMapSaver()
    node.call_generate_map()
    node.wait_and_save()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
