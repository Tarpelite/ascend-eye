import cv2
import os

# 输入和输出路径
input_video_path = 'uav_simulator/test_videos/bp.mp4'
output_video_path = 'infrared_bp_video.mp4'

# 打开原视频
cap = cv2.VideoCapture(input_video_path)

# 获取原视频的帧率、宽高
fps = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 视频写入器（保存为 mp4，编码为 H.264）
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'XVID'
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 转为灰度图
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 应用伪彩色映射
    infrared_style = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

    # 写入新帧
    out.write(infrared_style)

    frame_count += 1
    if frame_count % 30 == 0:
        print(f'Processed {frame_count} frames...')

# 释放资源
cap.release()
out.release()
print(f"\n✅ 视频处理完成，已保存为：{output_video_path}")