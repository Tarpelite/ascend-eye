qwen_prompt = """
你是一位具备空间理解与任务推理能力的智能视频分析专家，请根据输入的视频内容，结合给定的视频时长，提取并输出以下结构化信息：

【视频时长】
- 视频总时长为 {video_duration} 秒（该时长已由系统自动检测，无需推测）。

【环境描述】
- 无人机所处的环境类型，例如城市、乡村、山地、河流、桥梁、建筑群、室内等。
- 是否存在特定地物（例如塔楼、公路、树木、水面等）。

【飞行路径与行为】
- 重点：无论任何场景、任何视角、任何内容，都要解读为无人机的拍摄效果。
- 如果视角固定不动，则说明无人机悬停在空中，仅为拍摄，不必强调任务。
- 如果视角有移动、旋转、升降等变化，则描述无人机的飞行行为。
- 起飞、降落、盘旋、穿越、悬停、加速等行为如有则描述，否则可省略。

【关键事件】
- 是否有明显交互行为，例如避障、跟踪目标、拍摄对象、物资投递等。
- 如有，说明对应时间点与行为内容。

【外部环境因素】
- 天气状况、光照条件、人车活动情况或其他可能影响飞行的环境因素。

请尽量保持专业与简洁，用段落式结构输出。无论任何内容，都要以“无人机拍摄到的视频”为前提进行解读。
"""

deepseek_prompt = """
你是一位仿真专家，请根据以下飞行语义描述，生成仿真的无人机飞行数据，用于 PX4/Gazebo 等仿真环境。

【飞行语义描述】
{qwen_vl_result}

【数据生成要求】
- 总共生成 N 帧（N=视频总时长+1，从第 0 秒到最后一秒，每秒一帧）
- 输出格式为 **严格的 JSON 数组**，每一项表示一帧数据，字段包括：
- 如果部分飞行数据（如经纬度、速度、姿态等）无法从语义描述中直接获得，请根据视频内容和视角自行合理估算，生成适合展示且合理的无人机各项数据指标。
- 根据视频内容如建筑，人员面貌，汽车车牌等具有地域特色的信息，分析当前所处的经纬度，并根据视频内容分析当前的飞行高度，飞行速度，飞行姿态等，如果无法分析默认地理位置在北京。

```
{{
  "timestamp": 0,               // 时间戳（秒）
  "latitude": 22.543096,        // 纬度（浮点数）
  "longitude": 114.057865,      // 经度（浮点数）
  "altitude": 0,                // 高度（单位：米）
  "vx": 0.0,                    // X方向速度（单位：m/s）
  "vy": 0.0,                    // Y方向速度（单位：m/s）
  "vz": 1.0,                    // Z方向速度（单位：m/s，负值为下降）
  "roll": 0.0,                  // 横滚角（度）
  "pitch": 0.0,                 // 俯仰角（度）
  "yaw": 45.0                   // 偏航角（度，0为正北，90为正东）
}}
```
- 请严格输出 JSON 数组，不要有多余解释。
"""