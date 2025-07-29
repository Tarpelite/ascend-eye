import dashscope
import os
import httpx
import json
from prompt import qwen_prompt, deepseek_prompt
import asyncio
import cv2

# Qwen-VL分析函数
def qwen_vl_analyze(video_path, fps=2):
    # 用OpenCV读取视频时长
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频文件: {video_path}")
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    duration = int(frame_count / video_fps) if video_fps > 0 else 0
    print(f"视频时长: {duration}秒")
    cap.release()
    # 构造带时长的prompt
    prompt_with_duration = qwen_prompt.format(video_duration=duration)
    messages = [
        {"role": "system", "content": [{"text": prompt_with_duration}]},
        {"role": "user",
            "content": [
                {"video": f"file://{video_path}", "fps": fps},
                {"text": "请输出结构化飞行语义描述。"}
            ]
        }
    ]
    response = dashscope.MultiModalConversation.call(
        api_key=os.environ.get("DASHSCOPE_API_KEY", "sk-f0e683a01d464b0bb790f34524463fc5"),
        model='qwen-vl-max-latest',
        messages=messages
    )
    qwen_vl_result = response.output.choices[0].message.content[0]["text"]
    return qwen_vl_result

# DeepSeek生成仿真飞行数据
async def deepseek_generate_flight_data(qwen_vl_result):
    prompt = deepseek_prompt.format(qwen_vl_result=qwen_vl_result)
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('DEEPSEEK_API_KEY', 'sk-044f6ffb142f4470a11610e243920758')}"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(999999.0)) as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data['choices'][0]['message']['content']

if __name__ == "__main__":
    # 4个不同视频路径
    video_paths = [
        "DroneData/测试视频/test.mp4",
        "DroneData/测试视频/边防.mp4"
        # "uav_simulator/DroneData/测试视频/摔倒.mp4",
        # "uav_simulator/DroneData/测试视频/车祸.mp4",
        # "uav_simulator/DroneData/测试视频/长视频.mp4"
    ]
    
    for idx, video_path in enumerate(video_paths):
        print(f"\n==== 分析视频 {video_path} ====")
        qwen_vl_result = qwen_vl_analyze(video_path, fps=2)
        print("Qwen-VL结构化飞行语义描述：\n", qwen_vl_result)
        print("\n==== 生成仿真飞行数据 ====")
        flight_data_json = asyncio.run(deepseek_generate_flight_data(qwen_vl_result))
        print("仿真飞行数据(JSON)：\n", flight_data_json)
        
        # 以端口号为key保存，每次处理完一个就写入文件
        port = 5000 + idx
        
        # 读取现有文件内容（如果存在）
        file_path = "DroneData/flight_data_all.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                flight_data_json_list = json.load(f)
        except FileNotFoundError:
            flight_data_json_list = {}
        
        # 添加当前端口的数据
        flight_data_json_list[str(port)] = flight_data_json
        
        # 立即写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(flight_data_json_list, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 端口 {port} 数据已保存到文件")
    
    print("\n🎉 所有数据处理完成！")