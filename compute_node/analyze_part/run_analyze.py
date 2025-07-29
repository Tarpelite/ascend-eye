"""智能视频监控系统 (2025.02.26版)
核心功能：
1. 实时视频流采集与缓冲 
2. 智能多模态异常检测 
3. 视频分段存储与特征归档 
4. WebSocket实时警报推送 
"""
 
import cv2 
import asyncio 
import json 
import argparse
from datetime import datetime 
from concurrent.futures import ThreadPoolExecutor 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path, Query
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketState
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from collections import deque 
from typing import Optional, Dict, Any 
import numpy as np 
import logging 
from multi_modal_analyzer import MultiModalAnalyzer
import time
import uvicorn 
from multiprocessing import set_start_method 
from config import VideoConfig, ServerConfig, LOG_CONFIG, ARCHIVE_DIR, update_config

# 配置日志记录
logging.basicConfig(
    level=LOG_CONFIG['level'],
    format=LOG_CONFIG['format'],
    handlers=[logging.FileHandler(LOG_CONFIG['handlers'][0]['filename'], encoding='utf-8'), logging.StreamHandler()]
)

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='智能视频监控系统')
    parser.add_argument('--video_source', type=str, help='视频源路径')
    parser.add_argument('--video_sources', nargs='+', type=str, help='多路视频源路径')
    parser.add_argument('--uav_ids', nargs='+', type=str, help='多路无人机编号')
    parser.add_argument('--video_interval', type=int, help='视频分段时长(秒)')
    parser.add_argument('--analysis_interval', type=int, help='分析间隔(秒)')
    parser.add_argument('--buffer_duration', type=int, help='滑窗分析时长')
    parser.add_argument('--ws_retry_interval', type=int, help='WebSocket重连间隔(秒)')
    parser.add_argument('--max_ws_queue', type=int, help='消息队列最大容量')
    parser.add_argument('--jpeg_quality', type=int, help='JPEG压缩质量')
    parser.add_argument('--host', type=str, help='服务器主机地址')
    parser.add_argument('--port', type=int, help='服务器端口')
    parser.add_argument('--reload', type=bool, help='是否启用热重载')
    parser.add_argument('--workers', type=int, help='工作进程数')
    parser.add_argument('--api_only', action='store_true', help='仅启用API后端，不进行视频分析')
    
    args = parser.parse_args()
    return {k: v for k, v in vars(args).items() if v is not None}

# 更新配置
args = parse_args()
update_config(args)


from config import VIDEO_SOURCE

# 多路视频流和无人机编号
video_sources = args.get('video_sources')
uav_ids = args.get('uav_ids')
if video_sources and uav_ids:
    assert len(video_sources) == len(uav_ids), '视频流数量和无人机编号数量必须一致'
else:
    video_sources = [args.get('video_source') or VIDEO_SOURCE]
    uav_ids = ["1"]

# 视频流处理器 
class VideoProcessor:
    def __init__(self, video_source, uav_id):
        self.video_source = video_source
        self.uav_id = uav_id
        self.cap = cv2.VideoCapture(video_source)
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise ValueError(f"无法读取视频源: {video_source}")
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.buffer = deque(maxlen=int(self.fps * VideoConfig.BUFFER_DURATION))
        self.executor = ThreadPoolExecutor()
        self.analyzer = MultiModalAnalyzer()
        self.last_analysis = datetime.now().timestamp() 
        self._running = False 
        self.lock = asyncio.Lock()
        self.frame_queue = asyncio.Queue()  # 添加一个异步队列用于缓存帧
        self.start_push_queue = 0
 
    async def video_streamer(self, websocket: WebSocket):
        try:
            while True:
                #start_time = time.monotonic() 
                frame = await self.frame_queue.get()  # 从队列中获取帧
                # 压缩为JPEG格式（调整quality参数控制质量）
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), VideoConfig.JPEG_QUALITY])
                
                # 通过WebSocket发送二进制数据
                await websocket.send_bytes(buffer.tobytes())
                #elapsed = time.monotonic()  - start_time
                #await asyncio.sleep(1 / self.fps- elapsed-0.02)  # 发送的数度需要比生产的速度快，根据视频的fps来等待
                #if count%60==0:
                #    print("长度",self.frame_queue.qsize())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("停止直播")
    
    async def frame_generator(self):
        """异步视频帧生成器"""
        count = 0
        while self._running:
            start_time = time.monotonic() 
            ret, frame = self.cap.read() 
            count = count + 1
            if not ret:
                #logging.error(" 视频流中断，尝试重新连接...")
                break 
            
            # 转换颜色空间并缓冲 
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            self.buffer.append({ 
                "frame": frame,
                "timestamp": datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            })
            
            yield frame 
            
            
            if self.start_push_queue:
                await self.frame_queue.put(frame)  # 将帧放入队列

            # 控制帧生成速度

            elapsed = time.monotonic() - start_time
            await asyncio.sleep(max(0, 1/self.fps - elapsed))  # 控制帧生成速度

        #await self._reconnect()
 
    async def _reconnect(self):
        """视频流重连逻辑"""
        await asyncio.sleep(VideoConfig.WS_RETRY_INTERVAL) 
        self.cap.release() 
        self.cap = cv2.VideoCapture(self.video_source)
        ret, frame = self.cap.read()
 
    async def start_processing(self):
        """启动处理流水线"""
        self._running = True 
        count = 0
        start = time.time()
        async for frame in self.frame_generator(): 
            if archiver is not None:
                asyncio.create_task(archiver.write_frame(frame))
            count = count + 1
            
            # 定时触发分析 
            if (datetime.now().timestamp() - self.last_analysis) >= VideoConfig.ANALYSIS_INTERVAL and count >= self.fps * VideoConfig.ANALYSIS_INTERVAL:
                print("count", count)
                print("fps * interval", self.fps * VideoConfig.ANALYSIS_INTERVAL, self.fps)
                count = 0
                asyncio.create_task(self.trigger_analysis())
                self.last_analysis = datetime.now().timestamp() 
           
    async def trigger_analysis(self):
        """触发异步分析"""
        print("start")
        try: 
            async with self.lock:
                clip = list(self.buffer) 
                if not clip:
                    return 
                print("self.buffer:", len(clip))
                result = await self.analyzer.analyze([f["frame"] for f in clip], self.fps, (clip[0]['timestamp'], clip[-1]['timestamp']), uav_id=self.uav_id)
                print("响应结果为：",result)
                if result["alert"] != "无异常":
                    # 添加uav_id字段
                    result["uav_id"] = self.uav_id
                    await AlertService.notify(result) 
                # 不再在此写入历史和异常记录，统一在multi_modal_analyzer.py写入
        except Exception as e:
                logging.error(f" 分析失败: {str(e)}")
        
# 警报服务 
class AlertService:
    _connections = set()

    @classmethod
    async def register(cls, websocket: WebSocket):
        await websocket.accept()
        cls._connections.add(websocket)

    @classmethod
    async def notify(cls, data: Dict):
        """广播警报信息"""
        message = json.dumps({
            "timestamp": datetime.now().isoformat(),
            **data
        })

        for conn in list(cls._connections):
            try:
                if conn.client_state == WebSocketState.CONNECTED:
                    await conn.send_text(message)
                else:
                    cls._connections.remove(conn)
            except Exception as e:
                logging.warning(f"推送失败: {str(e)}")
                cls._connections.remove(conn)

# 视频存储服务 
class VideoArchiver:
    def __init__(self, width, height, fps):
        self.current_writer: Optional[cv2.VideoWriter] = None 
        self.last_split = datetime.now() 
        self.width = width
        self.height = height
        self.fps = fps
 
    async def write_frame(self, frame: np.ndarray): 
        """异步写入视频帧"""
        if self._should_split():
            self._create_new_file()
 
        if self.current_writer is not None:
            self.current_writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
 
    def _should_split(self) -> bool:
        return (datetime.now() - self.last_split).total_seconds() >= VideoConfig.VIDEO_INTERVAL 
 
    def _create_new_file(self):
        if self.current_writer is not None:
            self.current_writer.release() 
 
        filename = f"{ARCHIVE_DIR}/{datetime.now().strftime('%Y%m%d_%H%M')}.mp4" 
        self.current_writer = cv2.VideoWriter(
            filename, 
            cv2.VideoWriter_fourcc(*'avc1'), 
            self.fps, 
            (self.width, self.height)
        )
        self.last_split = datetime.now() 
 
# FastAPI应用配置 
app = FastAPI(title="Ascend-eye")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 挂载静态文件目录，让前端可以通过URL访问视频资源
import os
if os.path.exists("video_warning"):
    app.mount("/video_warning", StaticFiles(directory="video_warning"), name="video_warning")
    print("✅ 静态文件服务已启用: /video_warning")
else:
    print("⚠️ video_warning 目录不存在，静态文件服务未启用")
    # 创建目录结构
    os.makedirs("video_warning/warning_video", exist_ok=True)
    os.makedirs("video_warning/waring_img", exist_ok=True)
    os.makedirs("video_warning/label_img", exist_ok=True)
    os.makedirs("video_warning/label_json", exist_ok=True)
    app.mount("/video_warning", StaticFiles(directory="video_warning"), name="video_warning")
    print("✅ 已创建 video_warning 目录并启用静态文件服务")

# 根据命令行参数决定是否启动视频分析
api_only_mode = args.get('api_only', False)
if api_only_mode:
    print("🔧 API模式启动：仅提供后端接口服务，不进行视频分析")
    processors = []
else:
    print("🎥 完整模式启动：包含视频分析和后端接口服务")
    # 启动多路分析
    processors = [VideoProcessor(src, uav_id) for src, uav_id in zip(video_sources, uav_ids)]

# VideoArchiver类需要接收width/height/fps
class VideoArchiver:
    def __init__(self, width, height, fps):
        self.current_writer: Optional[cv2.VideoWriter] = None 
        self.last_split = datetime.now() 
        self.width = width
        self.height = height
        self.fps = fps
 
    async def write_frame(self, frame: np.ndarray): 
        """异步写入视频帧"""
        if self._should_split():
            self._create_new_file()
 
        if self.current_writer is not None:
            self.current_writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
 
    def _should_split(self) -> bool:
        return (datetime.now() - self.last_split).total_seconds() >= VideoConfig.VIDEO_INTERVAL 
 
    def _create_new_file(self):
        if self.current_writer is not None:
            self.current_writer.release() 
 
        filename = f"{ARCHIVE_DIR}/{datetime.now().strftime('%Y%m%d_%H%M')}.mp4" 
        self.current_writer = cv2.VideoWriter(
            filename, 
            cv2.VideoWriter_fourcc(*'avc1'), 
            self.fps, 
            (self.width, self.height)
        )
        self.last_split = datetime.now() 

# 初始化archiver时传入第一个视频流的参数（仅在非API模式下）
if processors:
    archiver = VideoArchiver(processors[0].width, processors[0].height, processors[0].fps)
else:
    archiver = None

async def start_all_processors():
    if processors:
        await asyncio.gather(*(p.start_processing() for p in processors))
    else:
        print("📡 API模式：无视频处理器需要启动")
 
@app.on_event("startup") 
async def startup():
    if processors:
        asyncio.create_task(start_all_processors())
    else:
        print("🚀 后端API服务已启动，等待前端连接...") 
 
@app.websocket("/alerts") 
async def alert_websocket(websocket: WebSocket):
    await AlertService.register(websocket) 
    try:
        while True:
            await websocket.receive_text()   # 维持连接 
    except Exception:
        pass 

@app.websocket("/video_feed")
async def video_feed(websocket: WebSocket, uav_id: int = Query(1, description="无人机编号")):
    try:
        await websocket.accept()
        
        # 检查是否在API模式下
        if api_only_mode:
            await websocket.send_text("⚠️ 当前为API模式，视频流功能不可用。请使用完整模式启动服务。")
            await websocket.close()
            return
            
        # 查找对应uav_id的processor
        processor = None
        for p in processors:
            if str(p.uav_id) == str(uav_id):
                processor = p
                break
        if processor is None:
            await websocket.send_text(f"未找到编号为{uav_id}的无人机视频流")
            await websocket.close()
            return
        processor.start_push_queue = 1
        await processor.video_streamer(websocket)
    except WebSocketDisconnect:
        print("Client disconnected from video feed")
        if processor:
            processor.start_push_queue = 0
            processor.frame_queue = asyncio.Queue()
    except Exception as e:
        print(f"An error occurred: {e}")
        if processor:
            processor.start_push_queue = 0
            processor.frame_queue = asyncio.Queue()
    finally:
        if processor:
            processor.start_push_queue = 0
            processor.frame_queue = asyncio.Queue()

# 新增接口：获取指定无人机编号的历史记录
def parse_history_file(filename, uav_id):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        history = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                # 尝试解析JSON格式
                record = json.loads(line)
                if record.get("uav_id") == str(uav_id):
                    history.append(record)
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试解析旧格式（兼容性）
                parts = line.split(":", 2)
                if len(parts) >= 3 and parts[0] == str(uav_id):
                    history.append({"uav_id": parts[0], "time": parts[1], "info": parts[2]})
        return history
    except Exception as e:
        return []

# 解析warning_history文件（包含完整JSON数据）
def parse_warning_history_file(filename, uav_id):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        warning_history = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                # 尝试解析JSON格式
                record = json.loads(line)
                if record.get("uav_id") == str(uav_id):
                    warning_history.append(record)
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试解析旧格式（兼容性）
                parts = line.split(":", 2)
                if len(parts) >= 3 and parts[0] == str(uav_id):
                    try:
                        # 尝试解析JSON数据
                        response_data = json.loads(parts[2])
                        response_data["time"] = parts[1]  # 添加时间字段
                        warning_history.append({"uav_id": parts[0], "time": parts[1], "info": response_data})
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，保持原有格式
                        warning_history.append({"uav_id": parts[0], "time": parts[1], "info": parts[2]})
        return warning_history
    except Exception as e:
        return []

@app.get("/history/{uav_id}")
def get_history_by_uav(uav_id: int = Path(..., description="无人机编号")):
    history = parse_history_file("video_histroy_info.json", uav_id)
    return {"history": history}

@app.get("/warning_history/{uav_id}")
def get_warning_history_by_uav(uav_id: int = Path(..., description="无人机编号")):
    warning_history = parse_warning_history_file("warning_history.json", uav_id)
    return {"warning_history": warning_history}

@app.get("/status")
def get_system_status():
    """获取系统运行状态"""
    return {
        "mode": "API模式" if api_only_mode else "完整模式",
        "api_only": api_only_mode,
        "video_analysis_enabled": not api_only_mode,
        "active_processors": len(processors),
        "uav_ids": [p.uav_id for p in processors] if processors else [],
        "archiver_enabled": archiver is not None,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run( 
        app="run_analyze:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=ServerConfig.RELOAD,
        workers=ServerConfig.WORKERS
    )

# python video_server.py --video_source "./测试视频/小猫开门.mp4"