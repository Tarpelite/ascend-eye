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
import sys
from typing import List
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn
import json

app = Flask(__name__)
video_source = None

# 加载本地仿真数据
uav_sim_data = {}
try:
    with open("uav_simulator/DroneData/flight_data_all.json", "r", encoding="utf-8") as f:
        uav_sim_data = json.load(f)
except Exception as e:
    print(f"[WARN] 无法加载本地仿真数据: {e}")

fastapi_app = FastAPI()

@fastapi_app.get("/uav_data")
def get_uav_data(port: int = Query(..., description="HTTP端口号")):
    """
    获取指定端口的无人机仿真数据
    返回格式：
    {
        "port": 5000,
        "data": [ {...}, {...}, ... ]  # 严格的JSON数组，每项为一帧仿真数据
    }
    """
    data = uav_sim_data.get(port)
    if data is None:
        return JSONResponse(status_code=404, content={"error": f"No UAV data for port {port}"})
    # 若data为字符串，转为json
    try:
        data_json = json.loads(data)
    except Exception:
        data_json = data
    return {"port": port, "data": data_json}

class HTTPVideoSimulator:
    def __init__(self, video_path, port=5000):
        self.video_path = video_path
        self.port = port
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
        
        print(f"[INFO] 视频信息:")
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
                    
                # 添加OSD信息
                self.add_osd(frame)
                
                # 编码为JPEG
                ret, buffer = cv2.imencode('.jpg', frame, 
                    [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_data = buffer.tobytes()
                
                self.frame_count += 1
                
            # 生成HTTP流格式
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                   
            # 控制帧率
            time.sleep(frame_delay)
            
    def add_osd(self, frame):
        """添加OSD信息"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            fps = self.frame_count / elapsed if elapsed > 0 else 0
            
            text = f"HTTP Stream | FPS: {fps:.2f} | Frame: {self.frame_count}"
            cv2.putText(frame, text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)


def create_app(video_path, port):
    app = Flask(__name__)
    video_source = HTTPVideoSimulator(video_path, port)

    if not video_source.validate_video():
        print(f"[ERROR] 视频文件无效: {video_path}")
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
                    <img src="{{ url_for('video_feed') }}" alt="Video Stream">
                </div>
                <div class="info">
                    <h3>连接信息：</h3>
                    <p><strong>视频流地址：</strong> <code>http://{{ request.host }}/video_feed</code></p>
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
        return Response(video_source.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    return app


def run_multi_simulators(video_paths: List[str], ports: List[int]):
    threads = []
    for video_path, port in zip(video_paths, ports):
        def run_app(video_path=video_path, port=port):
            app = create_app(video_path, port)
            print(f"\n{'='*50}\nAscend-Eye HTTP视频流模拟器\n{'='*50}")
            print(f"[INFO] 视频源: {video_path}")
            print(f"[INFO] 服务器地址: http://localhost:{port}")
            print(f"[INFO] 视频流地址: http://localhost:{port}/video_feed")
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
    parser.add_argument('--api', action='store_true', help='是否启动FastAPI接口')
    args = parser.parse_args()

    # 启动FastAPI接口（默认5005端口）
    if args.api:
        def run_fastapi():
            uvicorn.run(fastapi_app, host="0.0.0.0", port=5005, log_level="info")
        t = threading.Thread(target=run_fastapi, daemon=True)
        t.start()
        print("[INFO] FastAPI接口已启动: http://localhost:5005/uav_data?port=5000")

    # 优先命令行参数
    if args.videos and args.ports:
        if len(args.videos) != len(args.ports):
            print('[ERROR] 视频文件数量和端口数量必须一致')
            sys.exit(1)
        run_multi_simulators(args.videos, args.ports)
    # 默认支持4路流
    elif not (args.videos or args.ports) and not args.video:
        default_videos = [f'test_videos/test.mp4'] * 4
        default_ports = [5000, 5001, 5002, 5003]
        run_multi_simulators(default_videos, default_ports)
    # 兼容原有单路用法
    else:
        app = create_app(args.video, args.port)
        print(f"\n{'='*50}\nAscend-Eye HTTP视频流模拟器\n{'='*50}")
        print(f"[INFO] 视频源: {args.video}")
        print(f"[INFO] 服务器地址: http://localhost:{args.port}")
        print(f"[INFO] 视频流地址: http://localhost:{args.port}/video_feed")
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