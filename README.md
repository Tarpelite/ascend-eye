# ascend-eye


> 长鹰昇瞳 - 基于昇腾国产算力的无人机载荷图像实时智能感知与推理系统

## 🏆 项目简介

Ascend-Eye是为"SH-12中国航空工业集团有限公司无人机载荷图像实时智能感知与推理系统"比赛开发的参赛作品。我们的目标是构建一个能在国产算力平台上实时处理无人机视频流，进行目标检测、追踪和意图分析的智能系统。

### 核心特性
- 🚁 支持1080P@30fps实时视频流处理
- 🎯 多目标检测：人员、车辆、船只、火源等
- 🧠 基于昇腾等国产AI芯片的高性能推理
- 📊 mAP ≥ 80%，单帧处理时间 ≤ 80ms
- 🌐 端边云协同的智能分析架构

## 🏗️ 系统架构

```
┌─────────────────┐     视频流      ┌─────────────────┐     检测结果     ┌─────────────────┐
│   无人机模拟器   │ ─────MAVLink───▶│    算力节点      │ ────WebSocket──▶│     地面站      │
│ (uav_simulator) │                 │ (compute_node)  │                 │(ground_station) │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
      模拟相机                          目标检测+追踪                      前端展示+大模型分析
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- CUDA 11.0+（用于GPU加速）
- 推荐使用 Ubuntu 20.04 或 Windows 10/11

### 1. 克隆项目
```bash
git clone https://github.com/your-username/ascend-eye.git
cd ascend-eye
```

### 2. 安装uv（Python环境管理工具）
```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. 创建虚拟环境并安装依赖
```bash
# 创建虚拟环境
uv venv

# 激活环境
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装所有依赖
uv pip install -r requirements.txt
```

### 4. 准备测试视频
```bash
# 方法1：使用我们提供的测试脚本
python scripts/download_test_video.py

# 方法2：手动下载并放置到指定目录
# 将你的测试视频命名为 test.mp4 并放到 uav_simulator/test_videos/ 目录下
```

### 5. 运行系统

**请按顺序在三个不同的终端窗口中运行：**

```bash
# 终端1：启动地面站后端
cd ground_station/backend
python run_backend.py

# 终端2：启动算力节点
cd compute_node
python run_compute.py

# 终端3：启动无人机模拟器
cd uav_simulator
python run_simulator.py
```

然后在浏览器中打开 http://localhost:8000 查看地面站界面。

## 📁 项目结构

```
ascend-eye/
├── uav_simulator/          # 无人机模拟器
│   ├── run_simulator.py    # 模拟器主程序
│   └── test_videos/        # 测试视频目录
├── compute_node/           # 算力节点（核心）
│   ├── run_compute.py      # 算力节点主程序
│   ├── models/             # AI模型文件
│   └── src/                # 核心算法代码
├── ground_station/         # 地面站
│   ├── backend/            # 后端API服务
│   └── frontend/           # 前端界面
└── docs/                   # 项目文档
```

## 🔧 开发指南

### 各模块职责

#### 1. 无人机模拟器 (uav_simulator)
- **负责同学**：[待分配]
- **主要任务**：
  - 读取视频文件，模拟无人机相机
  - 将视频帧通过MAVLink协议发送
  - 控制发送速率（30fps）

#### 2. 算力节点 (compute_node) ⭐核心模块
- **负责同学**：[待分配]
- **主要任务**：
  - 接收视频流
  - 运行目标检测模型（YOLO/Faster R-CNN等）
  - 实现目标追踪算法
  - 将结果推送到地面站

#### 3. 地面站 (ground_station)
- **负责同学**：[待分配]
- **主要任务**：
  - 后端：接收检测结果，调用大模型API
  - 前端：实时显示视频和分析结果

### 开发流程

1. **创建自己的分支**
   ```bash
   git checkout -b feature/你的功能名称
   ```

2. **编写代码并测试**
   - 请遵循Python PEP8编码规范
   - 添加必要的注释
   - 编写单元测试

3. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加了xxx功能"
   git push origin feature/你的功能名称
   ```

4. **创建Pull Request**
   - 在GitHub上创建PR
   - 等待代码审查
   - 合并到主分支

