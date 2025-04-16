import cv2
import os
from datetime import datetime

###################################################
#         brief:将一个视频的每一帧都保存为照片         #
###################################################

# 设置输入视频路径和输出图片保存路径
video_path = '/home/xu/兑换站/蓝色方.avi'  # 替换为你的视频文件路径
output_folder = '/home/xu/兑换站/duihuanzhanpic'  # 替换为你希望保存图片的文件夹路径

# 创建输出文件夹（如果不存在）
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 打开视频文件
cap = cv2.VideoCapture(video_path)

# 获取视频的总帧数
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# 获取视频的帧率
fps = cap.get(cv2.CAP_PROP_FPS)

print(f"视频总帧数: {total_frames}, 帧率: {fps} fps")

frame_count = 0

# 循环遍历视频帧
while True:
    ret, frame = cap.read()

    # 如果没有读取到帧，表示视频结束
    if not ret:
        break

    # 获取当前时间，格式为 "YYYYMMDD_HHMMSS"
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 构建保存图片的文件名，精确到小时、分钟、秒
    frame_filename = os.path.join(output_folder, f"{current_time}_{frame_count:04d}.png")

    # 保存当前帧为图片
    cv2.imwrite(frame_filename, frame)

    print(f"保存帧 {frame_count}/{total_frames} 到 {frame_filename}")

    frame_count += 1

# 释放视频对象
cap.release()

print("视频切分完成！")
