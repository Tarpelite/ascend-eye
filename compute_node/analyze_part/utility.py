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
