# Ascend-Eye UAV Simulator & 智能监控 API 文档

## 目录

1. [GET /uav_data](#get-uav_data)
2. [GET /video_feed](#get-video_feed)
3. [WebSocket /alerts](#websocket-alerts)

---

## 1. GET /uav_data

- **功能**：根据端口号获取对应的无人机仿真数据（飞行轨迹、姿态等时序数据）。
- **请求方式**：GET
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明   | 示例   |
|--------|------|------|--------|--------|
| port   | int  | 是   | 端口号 | 5000   |

- **请求示例**：

```
GET http://localhost:5005/uav_data?port=5000
```

- **返回数据格式**（成功时）：

```json
{
  "port": 5000,
  "data": [
    {
      "timestamp": 0,
      "latitude": 39.9042,
      "longitude": 116.4074,
      "altitude": 10.0,
      "vx": 0.0,
      "vy": 0.0,
      "vz": 0.0,
      "roll": 0.0,
      "pitch": 0.0,
      "yaw": 0.0
    },
    // ... 其余每秒一帧的仿真数据
  ]
}
```

- **返回数据格式**（失败时/无数据）：

```json
{
  "error": "No UAV data for port 5001"
}
```

- **字段说明**：
  - `port`：请求的端口号。
  - `data`：严格的 JSON 数组，每一项为一帧无人机仿真数据，字段含义如下：
    - `timestamp`：时间戳（秒）
    - `latitude`：纬度（浮点数）
    - `longitude`：经度（浮点数）
    - `altitude`：高度（米）
    - `vx`、`vy`、`vz`：速度分量（米/秒）
    - `roll`、`pitch`、`yaw`：姿态角（度）

---

## 2. GET /video_feed

- **功能**：获取指定视频流的 HTTP Motion JPEG 流（MJPEG）。
- **请求方式**：GET
- **请求参数**：无
- **返回内容**：HTTP MJPEG 视频流（`Content-Type: multipart/x-mixed-replace; boundary=frame`）
- **请求示例**：

```
GET http://localhost:5000/video_feed
```

- **说明**：
  - 可用 OpenCV、浏览器、VLC 等直接访问。
  - 示例代码：
    ```python
    import cv2
    cap = cv2.VideoCapture('http://localhost:5000/video_feed')
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    ```

---

## 3. WebSocket /alerts

- **功能**：推送智能视频监控系统的异常警报信息。
- **请求方式**：WebSocket 连接
- **请求参数**：无
- **返回内容**：JSON文本流，每条为一次异常警报。
- **请求示例**：

```
ws://localhost:8000/alerts
```

- **返回数据格式**：

```json
{
  "timestamp": "2024-06-01T12:34:56.789Z",
  "alert": "<span style=\"color:red;\">请注意，出现了xx的情况，需要即时处理或知晓。</span>",
  "description": " 当前10秒监控消息描述：\n...\n\n 历史监控内容:\n...",
  "video_file_name": "warning_video/waring_2024-06-01-12-34-56.mp4",
  "picture_file_name": "waring_img/waring_2024-06-01-12-34-56.jpg",
  "label_img_name": "label_img/labeled_warning_2024-06-01-12-34-56.jpg",
  "label_json_name": "video_warning/label_json/warning_2024-06-01-12-34-56.json",
  "bboxes": [
    {"class": "person", "bbox": [100, 200, 300, 400]},
    ...
  ],
  "mapping": {
    "person": ["画面中有三名person正在同一处区域聚集"],
    ...
  }
}
```

- **字段说明**：
  - `timestamp`：警报生成时间
  - `alert`：异常警报文本（HTML格式）
  - `description`：本时段视频内容描述及历史内容
  - `video_file_name`：异常视频文件路径
  - `picture_file_name`：异常截图路径
  - `label_img_name`：带标注框的图片路径
  - `label_json_name`：标注框json路径
  - `bboxes`：检测到的目标框数组，每个包含`class`和`bbox`
  - `mapping`：实体名到描述中相关句子的映射，便于前端高亮

--- 