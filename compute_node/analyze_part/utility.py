# -*- coding: utf-8 -*-
"""
Created on Tue Mar  4 10:50:52 2025

@author: 18523
"""
import base64
import requests
import cv2 
import time 
import numpy as np
import json
import httpx
import logging
from config import APIConfig, RAGConfig,VideoConfig
from prompt import ENTITY_TO_QWEN_PROMPT_SYSTEM

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def frames_to_base64(frames,fps,timestamps):
    print(len(frames))
    print(fps)
    width = frames[0].shape[1]
    height = frames[0].shape[0]    
    
    # 确保尺寸是偶数（H.264要求）
    width = width - (width % 2)
    height = height - (height % 2)
    
    # 尝试多种编码器，优先使用Web兼容格式
    fourcc_options = [
        cv2.VideoWriter_fourcc(*'avc1'),  # H.264编码器（最佳Web兼容性）
        cv2.VideoWriter_fourcc(*'mp4v'),  # MPEG-4 编码器
        cv2.VideoWriter_fourcc(*'XVID'),  # XVID 编码器
        cv2.VideoWriter_fourcc(*'MJPG'),  # Motion JPEG 编码器
    ]
    
    video_writer = None
    for fourcc in fourcc_options:
        try:
            video_writer = cv2.VideoWriter('./video_warning/output.mp4', fourcc, fps, (width, height))
            if video_writer.isOpened():
                logger.info(f"✅ 成功使用编码器: {fourcc}")
                break
            else:
                video_writer.release()
        except Exception as e:
            logger.warning(f"⚠️ 编码器 {fourcc} 失败: {e}")
            continue
    
    if video_writer is None or not video_writer.isOpened():
        logger.warning("❌ 所有视频编码器都失败，使用默认编码器")
        video_writer = cv2.VideoWriter('./video_warning/output.mp4', -1, fps, (width, height))  
    # 遍历所有帧，并将其写入视频文件
    for frame in frames:
        # 确保帧是正确的数据类型和形状
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
        if len(frame.shape) == 2:
            # 如果帧是灰度的，转换为BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        video_writer.write(frame)
    
    # 释放VideoWriter对象
    video_writer.release()

    
    with open('./video_warning/output.mp4', 'rb') as video_file:
        video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
    
    return video_base64


#强制抽取关键帧帧，每秒一帧率
async def video_chat_async_limit_frame(text, frames,timestamps,fps=20):

    video_base64 = frames_to_base64(frames,fps,timestamps)


    #url = "http://172.16.10.44:8085/v1/chat/completions"
    url = APIConfig.QWEN_API_URL + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {APIConfig.QWEN_API_KEY}"
    }
    model = APIConfig.QWEN_MODEL

    data_image = []
    frame_count = int(VideoConfig.BUFFER_DURATION)
    for i in range(frame_count):
        frame = frames[(len(frames)//frame_count)*i]
        image_path = 'output_frame.jpg'
        cv2.imwrite(image_path, frame)
        with open(image_path,'rb') as file:
            image_base64 = "data:image/jpeg;base64,"+ base64.b64encode(file.read()).decode('utf-8')
        data_image.append(image_base64)
        
    content =  [{"type": "text", "text": text}] + [{"type": "image_url","image_url": {"url":i}} for  i in data_image]
      

    # 构建API请求的URL和Headers

    # 构建请求体
    data = {
        "model": model,  # 模型名称
        "vl_high_resolution_images":False,
        "messages": [
            {
                "role": "user",

                "content": content,
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()  # 检查HTTP错误
            response_data = response.json()
            logger.info(f"✅ 通义千问API调用成功")
            return response_data['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ 通义千问API HTTP错误: {e.response.status_code} - {e.response.text}")
        return "视频分析暂时不可用，请检查API配置"
    except httpx.RequestError as e:
        logger.error(f"❌ 通义千问API请求错误: {e}")
        return "网络连接错误，请检查网络设置"
    except json.JSONDecodeError as e:
        logger.error(f"❌ 通义千问API响应解析错误: {e}")
        return "API响应格式错误"
    except Exception as e:
        logger.error(f"❌ 通义千问API未知错误: {e}")
        return "视频分析服务异常"

async def qwenvl_warning_img_detection(img_path, prompt, current_time):
    """
    使用千问VL对异常截图做目标检测，保存标注图片和json
    img_path: 图片路径
    prompt: 检测提示词
    current_time: 时间戳
    返回: (标注图片路径, json文件路径, 检测框列表)
    """
    import base64
    import cv2
    from PIL import Image, ImageDraw, ImageFont
    import ast
    import os
    # 1. 图片编码
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    # 目录准备
    os.makedirs("video_warning/label_img", exist_ok=True)
    os.makedirs("video_warning/label_json", exist_ok=True)
    # 2. 调用千问VL API
    base64_image = encode_image(img_path)
    url = APIConfig.QWEN_API_URL + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {APIConfig.QWEN_API_KEY}"
    }
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                },
                {"type": "text", "text": prompt}
            ]
        }
    ]
    data = {
        "model": APIConfig.QWEN_MODEL,
        "messages": messages
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            detect_result = response_data['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"千问VL检测失败: {e}")
        return None, None, []
    # 3. 解析检测结果
    def parse_json(json_output):
        lines = json_output.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "```json":
                json_output = "\n".join(lines[i+1:])
                json_output = json_output.split("```" )[0]
                break
        return json_output
    bboxes = []
    try:
        parsed_result = parse_json(detect_result)
        bboxes = json.loads(parsed_result)
    except Exception as e:
        # 尝试直接解析
        try:
            import re
            json_str = re.search(r'\[.*\]', detect_result, re.DOTALL).group(0)
            bboxes = json.loads(json_str)
        except:
            logger.error(f"解析检测结果失败: {e}")
            bboxes = []
    # 4. 绘制标注框并保存
    def get_system_font(size=14):
        font_candidates = ["msyh.ttc", "simhei.ttf", "arial.ttf", None]
        for font_file in font_candidates:
            try:
                return ImageFont.truetype(font_file, size=size) if font_file else ImageFont.load_default()
            except OSError:
                continue
        return ImageFont.load_default()
    # 打开图片
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    font = get_system_font(14)
    colors = ['red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'brown']
    # 绘制每个检测框
    for i, bbox_info in enumerate(bboxes):
        try:
            bbox = bbox_info.get('bbox', [])
            cls = bbox_info.get('class', '目标')
            if len(bbox) == 4:
                x1, y1, x2, y2 = map(int, bbox)
                color = colors[i % len(colors)]
                # 绘制矩形框
                draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=3)
                # 绘制标签
                draw.text((x1 + 5, y1 - 20), cls, fill=color, font=font)
        except Exception as e:
            logger.warning(f"绘制第{i}个检测框失败: {e}")
    # 5. 保存文件
    label_img_name = f"video_warning/label_img/labeled_warning_{current_time}.jpg"
    label_json_name = f"video_warning/label_json/warning_{current_time}.json"
    # 保存标注图片
    img.save(label_img_name)
    # 保存JSON
    json_data = {
        "filename": f"warning_{current_time}.jpg",
        "prompt": prompt,
        "response": detect_result,
        "bboxes": bboxes,
        "timestamp": current_time
    }
    with open(label_json_name, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 检测完成，保存到: {label_img_name}, {label_json_name}")
    return label_img_name, label_json_name, bboxes

async def video_chat_async(text, frames, timestamps, fps=20):
    video_base64 = frames_to_base64(frames, fps, timestamps)

    url = APIConfig.QWEN_API_URL + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {APIConfig.QWEN_API_KEY}"
    }
    model = APIConfig.QWEN_MODEL
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": f"data:video/mp4;base64,{video_base64}"
                        }
                    }
                ]
            }
        ],
        "stop_token_ids": [151645, 151643]
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(APIConfig.REQUEST_TIMEOUT)) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"❌ 视频分析API错误: {e}")
        return "视频分析服务暂时不可用"


async def chat_request(message,stream=False):
    url = APIConfig.MOONSHOT_API_URL + "/chat/completions"
    model = APIConfig.MOONSHOT_MODEL

    messages =[{"role" : "user", "content" :message}]
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : f"Bearer {APIConfig.MOONSHOT_API_KEY}"
    }
    data ={
        "messages" : messages,
        "model" : model,
        "repetition_penalty" : APIConfig.REPETITION_PENALTY,
        "temperature" : APIConfig.TEMPERATURE,
        "top_p": APIConfig.TOP_P,
        "top_k": APIConfig.TOP_K,
        "stream" : stream
    }
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(APIConfig.REQUEST_TIMEOUT)) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"✅ DeepSeek API调用成功")
            return response_data['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ DeepSeek API HTTP错误: {e.response.status_code} - {e.response.text}")
        return "文本分析暂时不可用，请检查API配置"
    except httpx.RequestError as e:
        logger.error(f"❌ DeepSeek API请求错误: {e}")
        return "网络连接错误，请检查网络设置"
    except json.JSONDecodeError as e:
        logger.error(f"❌ DeepSeek API响应解析错误: {e}")
        return "API响应格式错误"
    except Exception as e:
        logger.error(f"❌ DeepSeek API未知错误: {e}")
        return "文本分析服务异常"

async def generate_qwen_vl_prompt_with_deepseek(alert_text, description_text):
    """
    输入异常描述和视频内容描述，调用deepseek生成千问VL目标检测prompt
    """
    system_prompt = ENTITY_TO_QWEN_PROMPT_SYSTEM
    user_prompt = f"异常信息：{alert_text}\n视频内容描述：{description_text}"
    message = f"<|system|>{system_prompt}\n<|user|>{user_prompt}"
    prompt = await chat_request(message)
    print("生成的qwen目标检测提示词是",prompt)
    return prompt


def draw_and_save_boxes(img_path, bboxes, label_img_path, label_json_path, entity=None):
    """
    在图片上绘制目标框并保存，保存json
    img_path: 原图路径
    bboxes: [{"class":..., "bbox": [x1, y1, x2, y2]}, ...]
    label_img_path: 输出图片路径
    label_json_path: 输出json路径
    entity: 类别名（可选）
    """
    import cv2
    import json
    img = cv2.imread(img_path)
    for obj in bboxes:
        bbox = obj.get('bbox', [])
        cls = obj.get('class', entity if entity else '目标')
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            color = (0, 0, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, cls, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imwrite(label_img_path, img)
    with open(label_json_path, 'w', encoding='utf-8') as f:
        json.dump(bboxes, f, ensure_ascii=False, indent=2)


def insert_txt(docs,table_name):
    #插入文本，同时向量化
    url = RAGConfig.VECTOR_API_URL
    """docs = [
        "Artificial intelligence was founded as an academic discipline in 1956.",
        "The field of AI research was founded at a workshop held on the campus of Dartmouth College during the summer of 1956."
    ]"""
    data = {
        "docs": docs,
        "table_name": table_name
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"❌ RAG服务错误: {e}")
        return {"error": str(e)}
