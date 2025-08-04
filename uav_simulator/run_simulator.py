#!/usr/bin/env python3
"""
HTTP视频流模拟器 - 完全不依赖GStreamer
使用Flask创建HTTP流服务器，OpenCV处理视频
"""

import cv2
import time
import threading
import argparse
import os
from flask import Flask, Response, render_template_string
from flask_cors import CORS
import sys
from typing import List
# FastAPI 相关导入已移除，统一使用 Flask
import json
from datetime import datetime

def clean_markdown_json(data_string):
    """
    清理包含 markdown 标记的 JSON 字符串
    与测试脚本中的逻辑完全一致
    """
    if not isinstance(data_string, str):
        return data_string
    
    # 移除 markdown 代码块标记
    clean_data = data_string.strip()
    
    # 移除开头的 ```json 或 ```
    if clean_data.startswith('```json'):
        clean_data = clean_data[7:]
    elif clean_data.startswith('```'):
        clean_data = clean_data[3:]
    
    # 移除结尾的 ```
    if clean_data.endswith('```'):
        clean_data = clean_data[:-3]
    
    # 清理首尾空白
    clean_data = clean_data.strip()
    
    return clean_data

app = Flask(__name__)
video_source = None

def load_uav_sim_data():
    """动态加载最新的仿真数据"""
    try:
        with open("DroneData/flight_data_all.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[DEBUG] 主路径加载失败: {e}")
        # 如果文件不存在，尝试相对路径
        try:
            with open("DroneData/flight_data_all.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                print("[DEBUG] 使用相对路径加载仿真数据成功")
                return data
        except Exception as e2:
            print(f"[ERROR] 两种路径都无法加载数据: {e2}")
            return {}

# 移除全局数据加载，改为动态加载

class HTTPVideoSimulator:
    def __init__(self, video_path, port=5000, video_type="test"):
        self.video_path = video_path
        self.port = port
        self.video_type = video_type  # "test", "label", 或 "ir"
        self.video_capture = None
        self.lock = threading.Lock()
        self.frame_count = 0
        self.start_time = None
        
    def validate_video(self):
        """验证视频文件"""
        if not os.path.exists(self.video_path):
            print(f"[ERROR] 视频文件不存在: {self.video_path}")
            return False
            
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"[ERROR] 无法打开视频文件: {self.video_path}")
            return False
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"[INFO] {self.video_type}视频信息:")
        print(f"  - 文件路径: {self.video_path}")
        print(f"  - 分辨率: {width}x{height}")
        print(f"  - FPS: {fps:.2f}")
        print(f"  - 总帧数: {total_frames}")
        
        cap.release()
        return True
        
    def generate_frames(self):
        """生成视频帧"""
        self.video_capture = cv2.VideoCapture(self.video_path)
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / fps
        
        self.start_time = time.time()
        
        while True:
            with self.lock:
                success, frame = self.video_capture.read()
                if not success:
                    # 循环播放
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                    
                # 根据视频类型进行不同处理
                processed_frame = self.process_frame(frame)
                
                # 编码为JPEG
                ret, buffer = cv2.imencode('.jpg', processed_frame, 
                    [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_data = buffer.tobytes()
                
                self.frame_count += 1
                
            # 生成HTTP流格式
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                   
            # 控制帧率
            time.sleep(frame_delay)
            
    def process_frame(self, frame):
        """根据视频类型处理帧"""
        if self.video_type == "ir":
            # 红外视频处理：转为灰度图并应用伪彩色映射
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            infrared_frame = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
            return infrared_frame
        else:
            # 默认情况（test 或 label）：返回原始帧
            return frame
            
    # def add_osd(self, frame):
    #     """添加OSD信息"""
    #     if self.start_time:
    #         elapsed = time.time() - self.start_time
    #         fps = self.frame_count / elapsed if elapsed > 0 else 0
            
    #         text = f"HTTP Stream | FPS: {fps:.2f} | Frame: {self.frame_count}"
    #         cv2.putText(frame, text, (10, 30), 
    #                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)


def create_app(video_path, port):
    app = Flask(__name__)
    
    # 添加CORS支持
    CORS(app, resources={
        r"/*": {
            "origins": "*",  # 允许所有来源，生产环境应该指定具体域名
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 创建三个视频源：test、label 和红外
    test_video_source = HTTPVideoSimulator(video_path, port, "test")
    
    # 构建label_video路径
    video_filename = os.path.basename(video_path)
    label_video_path = os.path.join("label_video", video_filename)
    label_video_source = HTTPVideoSimulator(label_video_path, port, "label")
    
    # 红外视频源使用原始test视频，但进行红外处理
    ir_video_source = HTTPVideoSimulator(video_path, port, "ir")

    if not test_video_source.validate_video():
        print(f"[ERROR] test视频文件无效: {video_path}")
        sys.exit(1)
        
    if not label_video_source.validate_video():
        print(f"[ERROR] label视频文件无效: {label_video_path}")
        sys.exit(1)
        
    if not ir_video_source.validate_video():
        print(f"[ERROR] 红外视频文件无效: {video_path}")
        sys.exit(1)

    @app.route('/')
    def index():
        return render_template_string('''
        <html>
        <head>
            <title>Ascend-Eye HTTP视频流</title>
            <style>body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; margin: 0; padding: 20px; } .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); } h1 { color: #333; } .video-container { margin: 20px 0; border: 2px solid #ddd; border-radius: 5px; overflow: hidden; display: inline-block; } img { max-width: 100%; height: auto; display: block; } .info { margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; text-align: left; } .status { color: #4CAF50; font-weight: bold; } code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; font-family: monospace; }</style>
        </head>
        <body>
            <div class="container">
                <h1>🚁 Ascend-Eye HTTP视频流模拟器</h1>
                <p class="status">✓ 服务器运行中</p>
                        <div class="video-container">
            <h3>原始视频流</h3>
            <img src="{{ url_for('video_feed') }}" alt="Video Stream">
        </div>
        <div class="video-container">
            <h3>标注视频流</h3>
            <img src="{{ url_for('label_video') }}" alt="Label Video Stream">
        </div>
        <div class="video-container">
            <h3>红外视频流</h3>
            <img src="{{ url_for('ir_feed') }}" alt="IR Video Stream">
        </div>
        <div class="info">
            <h3>连接信息：</h3>
            <p><strong>原始视频流地址：</strong> <code>http://{{ request.host }}/video_feed</code></p>
            <p><strong>标注视频流地址：</strong> <code>http://{{ request.host }}/label_video</code></p>
            <p><strong>红外视频流地址：</strong> <code>http://{{ request.host }}/IR_feed</code></p>
            <p><strong>协议：</strong> HTTP Motion JPEG</p>
                    <h3>Python客户端示例：</h3>
                    <pre><code>import cv2\ncap = cv2.VideoCapture('http://{{ request.host }}/video_feed')\nwhile True:\n    ret, frame = cap.read()\n    if ret:\n        cv2.imshow('Stream', frame)\n        if cv2.waitKey(1) & 0xFF == ord('q'):\n            break</code></pre>
                </div>
            </div>
        </body>
        </html>
        ''')

    @app.route('/video_feed')
    def video_feed():
        return Response(test_video_source.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
    @app.route('/label_video')
    def label_video():
        return Response(label_video_source.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
    @app.route('/IR_feed')
    def ir_feed():
        return Response(ir_video_source.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/uav_data')
    def uav_data():
        """
        获取无人机仿真数据
        默认返回当前端口的数据，也可通过 ?port=xxxx 查询其他端口
        """
        current_port = port
        print(f"[DEBUG] Flask /uav_data 默认端口: {current_port}")
        # 动态加载最新数据
        uav_sim_data = load_uav_sim_data()
        print(f"[DEBUG] 可用数据端口: {list(uav_sim_data.keys())}")
        
        # 数据文件中的键是字符串类型，需要转换
        data = uav_sim_data.get(str(current_port))
        if data is None:
            print(f"[ERROR] 端口 {current_port} 没有找到数据")
            return {"error": f"No UAV data for port {current_port}"}, 404
        
        # 处理包含markdown标记的JSON字符串
        try:
            # 使用统一的清理函数
            if isinstance(data, str):
                clean_data = clean_markdown_json(data)
                data_json = json.loads(clean_data)
            else:
                data_json = data
        except Exception as e:
            print(f"[ERROR] 解析端口 {current_port} 数据失败: {e}")
            print(f"[DEBUG] 原始数据: {data[:200] if isinstance(data, str) else str(data)[:200]}...")
            return {"error": f"Failed to parse data for port {current_port}: {str(e)}"}, 500
        
        return {
            "port": current_port,
            "data": data_json
        }
    return app


def run_multi_simulators(video_paths: List[str], ports: List[int]):
    threads = []
    for video_path, port in zip(video_paths, ports):
        def run_app(video_path=video_path, port=port):
            app = create_app(video_path, port)
            # 构建label_video路径
            video_filename = os.path.basename(video_path)
            label_video_path = os.path.join("label_video", video_filename)
            
            print(f"\n{'='*50}\nAscend-Eye HTTP视频流模拟器\n{'='*50}")
            print(f"[INFO] 视频源: {video_path}")
            print(f"[INFO] 标注视频源: {label_video_path}")
            print(f"[INFO] 服务器地址: http://localhost:{port}")
            print(f"[INFO] 原始视频流地址: http://localhost:{port}/video_feed")
            print(f"[INFO] 标注视频流地址: http://localhost:{port}/label_video")
            print(f"[INFO] 红外视频流地址: http://localhost:{port}/IR_feed")
            print(f"[INFO] 无人机数据: http://localhost:{port}/uav_data")
            print(f"[INFO] 端口列表: http://localhost:{port}/uav_ports")
            print(f"[INFO] 刷新数据: http://localhost:{port}/refresh_data")
            print(f"[INFO] 在浏览器中打开 http://localhost:{port} 查看视频流")
            print("[INFO] 按 Ctrl+C 停止服务器\n")
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        t = threading.Thread(target=run_app, daemon=True)
        t.start()
        threads.append(t)
    # 主线程等待所有子线程
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] 所有服务器已停止")


def main():
    parser = argparse.ArgumentParser(description='HTTP视频流模拟器')
    parser.add_argument('--videos', nargs='+', help='视频文件路径列表')
    parser.add_argument('--ports', nargs='+', type=int, help='HTTP端口列表')
    parser.add_argument('video', nargs='?', default='test_videos/test.mp4', help='单路视频文件路径（兼容旧用法）')
    parser.add_argument('--port', type=int, default=5000, help='单路HTTP端口（兼容旧用法）')
# --api 参数已移除，FastAPI接口已废弃
    args = parser.parse_args()

    # FastAPI接口已移除，统一使用Flask接口
    # 每个视频流端口都有独立的 /uav_data 接口

    # 优先命令行参数
    if args.videos and args.ports:
        if len(args.videos) != len(args.ports):
            print('[ERROR] 视频文件数量和端口数量必须一致')
            sys.exit(1)
        
        # 处理视频路径，如果只提供文件名，则自动添加test_videos前缀
        processed_videos = []
        for video_path in args.videos:
            if os.path.dirname(video_path) == '':
                # 只提供了文件名，添加test_videos前缀
                processed_videos.append(os.path.join('test_videos', video_path))
            else:
                # 提供了完整路径，直接使用
                processed_videos.append(video_path)
        
        run_multi_simulators(processed_videos, args.ports)
    # 默认支持4路流
    elif not (args.videos or args.ports) and not args.video:
        # 构建默认视频路径，确保包含test_videos文件夹
        default_videos = [f'test_videos/test.mp4'] * 4
        default_ports = [5000, 5001, 5002, 5003]
        run_multi_simulators(default_videos, default_ports)
    # 兼容原有单路用法
    else:
        # 处理单路视频路径，如果只提供文件名，则自动添加test_videos前缀
        video_path = args.video
        if os.path.dirname(video_path) == '':
            # 只提供了文件名，添加test_videos前缀
            video_path = os.path.join('test_videos', video_path)
        
        app = create_app(video_path, args.port)
        print(f"\n{'='*50}\nAscend-Eye HTTP视频流模拟器\n{'='*50}")
        # 构建label_video路径
        video_filename = os.path.basename(video_path)
        label_video_path = os.path.join("label_video", video_filename)
        
        print(f"[INFO] 视频源: {video_path}")
        print(f"[INFO] 标注视频源: {label_video_path}")
        print(f"[INFO] 服务器地址: http://localhost:{args.port}")
        print(f"[INFO] 原始视频流地址: http://localhost:{args.port}/video_feed")
        print(f"[INFO] 标注视频流地址: http://localhost:{args.port}/label_video")
        print(f"[INFO] 红外视频流地址: http://localhost:{args.port}/IR_feed")
        print(f"[INFO] 无人机数据: http://localhost:{args.port}/uav_data")
        print(f"[INFO] 端口列表: http://localhost:{args.port}/uav_ports")
        print(f"[INFO] 刷新数据: http://localhost:{args.port}/refresh_data")
        print(f"[INFO] 在浏览器中打开 http://localhost:{args.port} 查看视频流")
        print("[INFO] 按 Ctrl+C 停止服务器\n")
        try:
            app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)
        except KeyboardInterrupt:
            print("\n[INFO] 服务器已停止")
        except Exception as e:
            print(f"[ERROR] 运行失败: {e}")

if __name__ == '__main__':
    main()