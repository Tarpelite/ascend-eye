# Ascend-Eye 项目 API 文档

本项目后端分为两大部分：
- **分析后端**（智能视频分析与告警，FastAPI，默认端口8000）
- **无人机模拟后端**（视频流与仿真数据，Flask+FastAPI，默认端口5000/5005）

---

## 一、分析后端（compute_node/analyze_part/run_analyze.py）

> 地址示例：`http://localhost:8000`

### 1. WebSocket /alerts
- **URL**：`ws://localhost:8000/alerts`
- **功能**：推送所有无人机的异常警报信息（实时）。
- **请求方式**：WebSocket 连接
- **参数**：无
- **返回内容**：JSON文本流，每条为一次异常警报。
- **返回示例**：
```json
{
  "uav_id": 2,
  "timestamp": "2024-06-01T12:34:56.789Z",
  "alert": "<span style=\"color:red;\">请注意，出现了人员聚集的情况，需要即时处理或知晓。</span>",
  "description": " 当前10秒监控消息描述：\n画面中有三名工人正在同一处区域聚集，旁边有一辆黄色工程车停靠。\n\n 历史监控内容:\n上一个时段无异常。",
  "video_file_name": "warning_video/warning_video/waring_2024-06-01-12-34-56.mp4",
  "picture_file_name": "waring_img/waring_img/waring_2024-06-01-12-34-56.jpg",
  "label_img_name": "video_warning/label_img/labeled_warning_2024-06-01-12-34-56.jpg",
  "label_json_name": "video_warning/label_json/warning_2024-06-01-12-34-56.json",
  "bboxes": [
    {"class": "工人", "bbox": [120, 200, 180, 320]},
    {"class": "工程车", "bbox": [400, 250, 520, 380]}
  ],
  "mapping": {
    "工人": ["画面中有三名工人正在同一处区域聚集，旁边有一辆黄色工程车停靠"],
    "工程车": ["画面中有三名工人正在同一处区域聚集，旁边有一辆黄色工程车停靠"]
  }
}
```
- **字段说明**：
  - `uav_id`：无人机编号
  - 其余字段见下方说明

### 2. GET /history/{uav_id}
- **URL**：`http://localhost:8000/history/{uav_id}`
- **功能**：获取指定无人机的历史记录（所有分析结果，包括无异常）。
- **参数**：`uav_id`（路径参数，无人机编号，int）
- **返回示例**：
```json
{
  "history": [
    {"uav_id": "1", "time": "2024-06-01-12-00-00", "info": "无异常"},
    {"uav_id": "1", "time": "2024-06-01-12-10-00", "info": "<span style=\"color:red;\">请注意，出现了人员聚集的情况，需要即时处理或知晓。</span>"}
  ]
}
```

### 3. GET /warning_history/{uav_id}
- **URL**：`http://localhost:8000/warning_history/{uav_id}`
- **功能**：获取指定无人机的历史异常信息（包含完整的异常分析结果和所有字段）。
- **参数**：`uav_id`（路径参数，无人机编号，int）
- **返回示例**：
```json
{
  "warning_history": [
    {
      "time": "2024-06-01-12-34-56",
      "uav_id": 2,
      "alert": "<span style=\"color:red;\">请注意，出现了人员聚集的情况，需要即时处理或知晓。</span>",
      "description": " 当前10秒监控消息描述：\n画面中有三名工人正在同一处区域聚集，旁边有一辆黄色工程车停靠。\n\n 历史监控内容:\n上一个时段无异常。",
      "video_file_name": "warning_video/warning_video/uav2_waring_2024-06-01-12-34-56.mp4",
      "picture_file_name": "waring_img/warning_img/uav2_waring_2024-06-01-12-34-56.jpg",
      "label_img_name": "video_warning/label_img/labeled_warning_2024-06-01-12-34-56.jpg",
      "label_json_name": "video_warning/label_json/warning_2024-06-01-12-34-56.json",
      "bboxes": [
        {"class": "工人", "bbox": [120, 200, 180, 320]},
        {"class": "工程车", "bbox": [400, 250, 520, 380]}
      ],
      "mapping": {
        "工人": ["画面中有三名工人正在同一处区域聚集，旁边有一辆黄色工程车停靠"],
        "工程车": ["画面中有三名工人正在同一处区域聚集，旁边有一辆黄色工程车停靠"]
      }
    }
  ]
}
```

### 4. WebSocket /video_feed
- **URL**：`ws://localhost:8000/video_feed?uav_id=1`
- **功能**：获取指定无人机编号的视频流（MJPEG流，WebSocket二进制帧）。
- **参数**：`uav_id`（查询参数，无人机编号，int，默认1）
- **返回内容**：二进制JPEG帧流，适合前端canvas或OpenCV解码。

---

## 二、无人机模拟后端（uav_simulator/run_simulator.py）

> 地址示例：
> - 视频流：`http://localhost:5000`（Flask）
> - 仿真数据API：`http://localhost:5005`（FastAPI）

### 1. GET /video_feed（修改端口获取不同的视频流）
- **URL**：`http://localhost:5000/video_feed`
- **功能**：获取指定端口的视频流（HTTP MJPEG流）。
- **参数**：无
- **返回内容**：HTTP MJPEG 视频流
- **前端用法**：
  - `<img src="http://localhost:5000/video_feed">`
  - 或用OpenCV、VLC等直接访问

### 2. GET /uav_data
- **URL**：`http://localhost:5005/uav_data?port=5005`
- **功能**：获取指定端口的无人机仿真数据（如飞行轨迹、姿态等时序数据）。
- **参数**：`port`（查询参数，int，端口号）
- **返回示例**：
```json
{
  "port": 5000,
  "data": [
    {"timestamp": 0, "latitude": 39.9042, "longitude": 116.4074, "altitude": 10.0, "vx": 0.0, "vy": 0.0, "vz": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
    ...
  ]
}
```

---

## 字段说明（通用）
- `uav_id`：无人机编号
- `timestamp`/`time`：时间戳
- `alert`/`info`：异常信息或分析结果
- `description`：视频内容描述
- `bboxes`：目标检测框数组
- `mapping`：实体名到描述中相关句子的映射
- 其它见各接口示例

---

## 使用说明
- 分析后端和模拟后端可分别独立部署，端口可自定义。
- 前端可通过 WebSocket/HTTP 方式实时获取多路无人机视频流、仿真数据和异常告警。
- 所有接口均支持多无人机编号，便于多路联动和数据溯源。 

---

## 多无人机模拟与分析说明

### 1. 端口与无人机编号的关系

- **无人机模拟端（uav_simulator）**：
  - 每一路视频流服务监听一个独立端口（如5000、5001、5002、5003），每个端口对应一台“虚拟无人机”。
  - 例如：
    - `http://localhost:5000/video_feed` → 无人机1
    - `http://localhost:5001/video_feed` → 无人机2
    - `http://localhost:5002/video_feed` → 无人机3
    - `http://localhost:5003/video_feed` → 无人机4
  - 这些端口是**真实开放的HTTP端口**，前端/分析端可直接访问。

- **分析后端（compute_node/analyze_part）**：
  - 启动时通过命令行参数 `--video_sources` 和 `--uav_ids` 指定要分析的多路视频流及其编号：
    ```bash
    python run_analyze.py \
      --video_sources http://localhost:5000/video_feed http://localhost:5001/video_feed ... \
      --uav_ids 1 2 ...
    ```
  - `--video_sources` 是参数，指定要分析的每一路视频流的URL。
  - `--uav_ids` 是参数，指定每一路流对应的无人机编号（自定义，通常与端口一一对应）。
  - 分析后端会为每一路流创建独立分析任务，所有告警、历史、异常等数据都带有 `uav_id` 字段。

### 2. 多无人机端到端流程举例

1. **启动模拟端**：
   - 启动4个端口的视频流服务（如5000~5003），每个端口推送不同视频。
2. **启动分析端**：
   - 用如下命令行指定4路流和编号：
     ```bash
     python run_analyze.py \
       --video_sources http://localhost:5000/video_feed http://localhost:5001/video_feed http://localhost:5002/video_feed http://localhost:5003/video_feed \
       --uav_ids 1 2 3 4
     ```
3. **前端/客户端使用**：
   - 通过 `/alerts` WebSocket 实时获取所有无人机的异常告警（每条带uav_id）。
   - 通过 `/video_feed?uav_id=2` 获取指定无人机的视频流。
   - 通过 `/history/{uav_id}`、`/warning_history/{uav_id}` 获取指定无人机的历史/异常信息。
   - 通过 `/uav_data?port=5000` 获取指定端口的仿真数据。

### 3. 参数与真实端口说明

- `--video_sources`、`--uav_ids` 是分析端的**命令行参数**，用于配置多路分析。
- `/uav_data?port=5000`、`/video_feed` 等接口中的 `port`、`uav_id` 是**请求参数**，用于前端/客户端指定要访问哪台无人机的数据。
- `5000`、`5001` 等是**真实开放的HTTP端口**，由模拟端实际监听。
- `uav_id` 是逻辑编号，可与端口一一对应，也可自定义。

--- 