使用qwenvl进行视频分析
使用deepseek生成json格式的飞行器数据
在run_simulator中使用，通过faspapi推送
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