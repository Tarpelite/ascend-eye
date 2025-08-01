# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 12:03:32 2025

@author: 18523
"""

import base64
import requests
import cv2 
import time 
import numpy as np
import time
import json
import httpx
import os
import datetime
import asyncio
import re

from utility import video_chat_async,chat_request,insert_txt,video_chat_async_limit_frame,generate_qwen_vl_prompt_with_deepseek, draw_and_save_boxes, qwenvl_warning_img_detection, extract_entity_mapping
from config import RAGConfig

# 从配置文件加载提示词
# with open('prompts.json', 'r', encoding='utf-8') as f:
#     prompts = json.load(f)

# prompt_detect = prompts['prompt_detect']
# prompt_summary = prompts['prompt_summary']
# prompt_vieo = prompts['prompt_video']

from prompt import prompt_detect,prompt_summary,prompt_vieo


class MultiModalAnalyzer:
    def __init__(self):
        self.message_queue = []
        self.time_step_story = []

    def trans_date(self,date_str):
        # Split the input string into components
        year, month, day, hour, minute, second = date_str.split('-')
        
        # Determine AM or PM
        am_pm = "上午" if int(hour) < 12 else "下午"
        
        # Convert 24-hour format to 12-hour format
        hour_12 = hour if hour == '12' else str(int(hour) % 12)
        
        # Return the formatted date and time string
        return f"{year}年{int(month)}月{int(day)}日{am_pm}{hour_12}点（{hour}时）{int(minute)}分{int(second)}秒"
    
    def clear_history(self):
        """清空历史队列，重新开始监控"""
        self.message_queue = []
        print("历史队列已清空，监控重新开始")
    
    async def analyze(self, frames, fps=20, timestamps=None, uav_id=None):
        start_time = time.time()
        
        # 构建历史信息用于总结
        Recursive_summary = "不存在历史监控记录"
        if self.message_queue:
            # 构建历史信息文本
            history_text = ""
            for i in self.message_queue:
                history_text += f"时间段：{i['start_time']} - {i['end_time']}\n描述：{i['description']}\n异常：{i['is_alert']}\n\n"
            
            # 只有当有历史记录时才调用AI进行总结
            time_temp = time.time()
            Recursive_summary = await chat_request(prompt_summary.format(histroy=history_text))
            summary_time = time.time() - time_temp
            print("历史总结用时:", summary_time)
        else:
            print("首次监控，无历史记录")
        
        time_temp = time.time()
        description = await video_chat_async_limit_frame(prompt_vieo,frames,timestamps,fps=fps,uav_id=uav_id)
        description_time = time.time()-time_temp
        description_time = time.time()-time_temp

        if timestamps==None:
            return description
        
        date_flag = self.trans_date(timestamps[0])+"："
        #保存监控视频描述到数据库
        if RAGConfig.ENABLE_RAG:
            insert_txt([date_flag+description],'table_test_table')
        else:
            print("RAG未开启,准备保存到本地")
            # 本地文件保存，使用JSON格式
            with open(RAGConfig.HISTORY_FILE, 'a', encoding='utf-8') as file:
                print("开始保存历史消息")
                # 将description中的换行符清理，避免JSON解析问题
                clean_description = description.replace('\n', '').replace('\r', '')
                # 构建JSON格式的记录
                history_record = {
                    "uav_id": str(uav_id) if uav_id is not None else "1",
                    "time": timestamps[0],
                    "info": f"{date_flag}{clean_description}"
                }
                # 写入JSON格式的记录
                file.write(json.dumps(history_record, ensure_ascii=False) + '\n')

        
        text = prompt_detect.format(Recursive_summary=Recursive_summary,current_time=timestamps[0]+"  - " + timestamps[-1],latest_description=description)
        
        time_temp = time.time()
        alert = await chat_request(text)
        alert_time = time.time() - time_temp
        
        print("警告内容：",alert)    

        print("\n\n下面是视频描述原文：")
        print(description)
        
        print("视频分析耗时",time.time() - start_time)
        print("视频描述用时,警告文本用时:",description_time,alert_time)
        
        # 先保存到历史队列，这样下次分析时就能使用正确的历史信息
        if timestamps:
            self.message_queue.append({ 
                'start_time': timestamps[0],
                'end_time': timestamps[1],
                'description': description, 
                'is_alert': alert
            })

            # 只保留最近15条消息用作历史信息总结
            self.message_queue = self.message_queue[-15:]
        
        if "无异常" not in alert:
            current_time = timestamps[0]
            import os
            os.makedirs("video_warning/warning_img", exist_ok=True)
            os.makedirs("video_warning/warning_video", exist_ok=True)
            
            # 文件名包含无人机编号
            if uav_id is not None:
                file_str = f"uav{uav_id}_warning_{current_time}"
            else:
                file_str = f"warning_{current_time}"
                
            new_file_name = f"video_warning/warning_video/{file_str}.mp4"
            
            # 根据uav_id选择对应的output文件
            if uav_id is not None:
                source_file = f"./video_warning/output_{uav_id}.mp4"
            else:
                source_file = "./video_warning/output.mp4"
            
            # 检查文件是否存在再移动
            if os.path.exists(source_file):
                os.rename(source_file, new_file_name)
            else:
                print(f"警告：源文件 {source_file} 不存在，无法移动到 {new_file_name}")
                
            frame = frames[0]
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) 
            img_path = f"video_warning/warning_img/{file_str}.jpg"
            cv2.imwrite(img_path, frame)

            # 1. 用deepseek生成千问VL目标检测prompt
            prompt4detect = await generate_qwen_vl_prompt_with_deepseek(alert, description)

            # 2. 用千问vl对异常截图做目标检测，保存标注图片和json
            label_img_name, label_json_name, bboxes = await qwenvl_warning_img_detection(img_path, prompt4detect, current_time, uav_id)
            # 生成mapping字段
            mapping = extract_entity_mapping(description, bboxes)
            # 将异常警告和完整response写入warning_history.txt
            response = {
                "uav_id":uav_id,
                "alert":f"{alert}",
                "description":f' 当前10秒监控消息描述：\n{description}\n\n 历史监控内容:\n{Recursive_summary}',
                "video_file_name":f"video_warning/warning_video/{file_str}.mp4",
                "picture_file_name":f"video_warning/warning_img/{file_str}.jpg",
                "label_img_name":label_img_name,
                "label_json_name":label_json_name,
                "bboxes":bboxes,
                "mapping":mapping
            }
            
            with open('warning_history.json', 'a', encoding='utf-8') as f:
                # 构建统一的JSON格式记录
                warning_record = {
                    "uav_id": str(uav_id) if uav_id is not None else "1",
                    "time": current_time,
                    "info": response  # 这里直接存储完整的response数据
                }
                # 写入JSON格式的记录
                f.write(json.dumps(warning_record, ensure_ascii=False) + '\n')
            # response已在上面构建并写入文件，这里直接返回
            print("alert接口返回的是",response)
            return response
        return {"alert":"无异常"}
        