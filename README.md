1. Clone toàn bộ dự án:**
```bash
git clone https://github.com/hiep-noob/mecanum_ws.git
cd mecanum_ws
```
2. Cài đặt các thư viện hệ thống
```
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```
3. Biên dịch
```
colcon build --symlink-install
source install/setup.bash
```
4. Các lệnh chạy trong file lệnh **[Bấm vào đây để xem toàn bộ lệnh chạy dự án](src/mecanum/Lệnh%20chạy)**
5. Thư mục chứa các bản đồ 2D đã quét: **[Bấm vào đây để xem thư mục maps](src/mecanum/maps)**
