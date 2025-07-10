#!/usr/bin/env python3
"""
HTTP视频流测试客户端
接收并显示HTTP Motion JPEG流
"""

import cv2
import time
import argparse
import numpy as np
from datetime import datetime

class HTTPTestClient:
    def __init__(self, stream_url, enable_ai=False, record=False):
        """
        初始化HTTP测试客户端
        
        Args:
            stream_url: HTTP流地址
            enable_ai: 是否启用AI检测（模拟）
            record: 是否录制视频
        """
        self.stream_url = stream_url
        self.enable_ai = enable_ai
        self.record = record
        
        # 视频捕获对象
        self.capture = None
        
        # 统计信息
        self.frames_received = 0
        self.start_time = None
        self.last_fps_time = None
        self.fps_counter = 0
        
        # 录制相关
        self.video_writer = None
        self.record_filename = None
        
        # AI检测相关
        self.detection_results = []
        
    def connect(self):
        """连接到HTTP流"""
        print(f"[INFO] 正在连接到 {self.stream_url}")
        
        self.capture = cv2.VideoCapture(self.stream_url)
        
        # 测试连接
        for i in range(5):
            ret, frame = self.capture.read()
            if ret:
                print("[INFO] 成功连接到HTTP流")
                
                # 获取帧信息
                height, width = frame.shape[:2]
                print(f"[INFO] 视频流信息:")
                print(f"  - 分辨率: {width}x{height}")
                
                # 初始化录制器
                if self.record:
                    self.init_recorder(width, height)
                    
                return True
                
            print(f"[WARN] 连接失败，重试 {i+1}/5...")
            time.sleep(1)
            
        print("[ERROR] 无法连接到HTTP流")
        return False
        
    def init_recorder(self, width, height):
        """初始化视频录制器"""
        self.record_filename = f"http_recorded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            self.record_filename, fourcc, 30.0, (width, height)
        )
        print(f"[INFO] 开始录制视频: {self.record_filename}")
        
    def simulate_ai_detection(self, frame):
        """模拟AI目标检测"""
        self.detection_results = []
        
        if np.random.random() > 0.5:  # 50%概率检测到目标
            h, w = frame.shape[:2]
            
            # 生成1-3个检测框
            for _ in range(np.random.randint(1, 4)):
                x1 = np.random.randint(w * 0.1, w * 0.6)
                y1 = np.random.randint(h * 0.1, h * 0.6)
                x2 = x1 + np.random.randint(80, 200)
                y2 = y1 + np.random.randint(80, 200)
                
                x2 = min(x2, w - 10)
                y2 = min(y2, h - 10)
                
                classes = ['person', 'vehicle', 'drone', 'building', 'animal']
                class_name = np.random.choice(classes)
                confidence = np.random.uniform(0.6, 0.95)
                
                self.detection_results.append({
                    'bbox': (x1, y1, x2, y2),
                    'class': class_name,
                    'confidence': confidence
                })
                
    def draw_detections(self, frame):
        """绘制检测结果"""
        for det in self.detection_results:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class']
            confidence = det['confidence']
            
            # 颜色映射
            colors = {
                'person': (0, 255, 0),
                'vehicle': (255, 0, 0),
                'drone': (0, 0, 255),
                'building': (255, 255, 0),
                'animal': (255, 0, 255)
            }
            color = colors.get(class_name, (255, 255, 255))
            
            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            cv2.rectangle(frame, (x1, y1-25), (x1+len(label)*10, y1), color, -1)
            cv2.putText(frame, label, (x1+5, y1-7),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                       
    def add_osd(self, frame):
        """添加OSD信息"""
        current_time = time.time()
        
        # 计算FPS
        if self.last_fps_time is None:
            self.last_fps_time = current_time
            
        time_diff = current_time - self.last_fps_time
        if time_diff >= 1.0:
            fps = self.fps_counter / time_diff
            self.fps_counter = 0
            self.last_fps_time = current_time
        else:
            fps = self.fps_counter / max(time_diff, 0.001)
            
        # 统计信息
        if self.start_time:
            elapsed = current_time - self.start_time
            avg_fps = self.frames_received / elapsed if elapsed > 0 else 0
        else:
            avg_fps = 0
            
        # 绘制信息
        info_text = [
            f"HTTP Client - Ascend-Eye",
            f"FPS: {fps:.2f} (avg: {avg_fps:.2f})",
            f"Frames: {self.frames_received}",
            f"Time: {elapsed:.1f}s" if self.start_time else "Time: 0.0s"
        ]
        
        if self.record:
            info_text.append(f"REC: {self.record_filename}")
            
        if self.enable_ai:
            info_text.append(f"AI: {len(self.detection_results)} objects")
            
        # 绘制背景和文字
        y_start = 10
        for i, text in enumerate(info_text):
            y = y_start + i * 25
            cv2.rectangle(frame, (5, y-20), (300, y+5), (0, 0, 0), -1)
            cv2.putText(frame, text, (10, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                       
    def run(self):
        """运行客户端"""
        if not self.connect():
            return
            
        print("\n[INFO] 开始接收视频流...")
        print("[INFO] 按 'q' 退出")
        print("[INFO] 按 's' 保存截图")
        print("[INFO] 按 'a' 切换AI检测")
        print("[INFO] 按 'r' 开始/停止录制\n")
        
        self.start_time = time.time()
        
        # 创建窗口
        window_name = 'HTTP Stream - Ascend-Eye'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 960, 540)
        
        screenshot_count = 0
        
        try:
            while True:
                ret, frame = self.capture.read()
                if not ret:
                    print("[WARN] 读取帧失败，尝试重连...")
                    time.sleep(1)
                    continue
                    
                # AI检测
                if self.enable_ai:
                    self.simulate_ai_detection(frame)
                    self.draw_detections(frame)
                    
                # 添加OSD
                self.add_osd(frame)
                
                # 录制
                if self.video_writer:
                    self.video_writer.write(frame)
                    
                # 显示
                cv2.imshow(window_name, frame)
                self.frames_received += 1
                self.fps_counter += 1
                
                # 键盘控制
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"screenshot_{screenshot_count}.png"
                    cv2.imwrite(filename, frame)
                    print(f"[INFO] 保存截图: {filename}")
                    screenshot_count += 1
                elif key == ord('a'):
                    self.enable_ai = not self.enable_ai
                    print(f"[INFO] AI检测: {'开启' if self.enable_ai else '关闭'}")
                elif key == ord('r'):
                    if self.video_writer:
                        self.video_writer.release()
                        self.video_writer = None
                        print(f"[INFO] 停止录制: {self.record_filename}")
                    else:
                        h, w = frame.shape[:2]
                        self.init_recorder(w, h)
                        
        except KeyboardInterrupt:
            print("\n[INFO] 收到中断信号")
        finally:
            self.shutdown()
            
    def shutdown(self):
        """关闭客户端"""
        print("\n[INFO] 正在关闭客户端...")
        
        if self.capture:
            self.capture.release()
            
        if self.video_writer:
            self.video_writer.release()
            print(f"[INFO] 视频已保存: {self.record_filename}")
            
        cv2.destroyAllWindows()
        
        # 打印统计
        if self.start_time:
            total_time = time.time() - self.start_time
            if total_time > 0:
                avg_fps = self.frames_received / total_time
                print(f"\n[INFO] 统计信息:")
                print(f"  - 运行时间: {total_time:.2f}秒")
                print(f"  - 接收帧数: {self.frames_received}")
                print(f"  - 平均FPS: {avg_fps:.2f}")


def main():
    parser = argparse.ArgumentParser(description='HTTP视频流测试客户端')
    parser.add_argument('--url', default='http://localhost:5000/video_feed',
                       help='HTTP流地址')
    parser.add_argument('--ai', action='store_true',
                       help='启用AI检测模拟')
    parser.add_argument('--record', action='store_true',
                       help='录制视频')
    
    args = parser.parse_args()
    
    print("="*50)
    print("Ascend-Eye HTTP视频流测试客户端")
    print("="*50)
    
    client = HTTPTestClient(
        stream_url=args.url,
        enable_ai=args.ai,
        record=args.record
    )
    
    try:
        client.run()
    except Exception as e:
        print(f"[ERROR] 运行失败: {e}")


if __name__ == '__main__':
    main()