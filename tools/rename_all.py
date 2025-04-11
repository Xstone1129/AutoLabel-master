import os
import shutil
from datetime import datetime

def rename_image_files(folder_path):
    # 获取文件夹中所有文件
    files = os.listdir(folder_path)
    
    # 筛选出所有的图片文件
    image_files = [f for f in files if is_image_file(f)]
    
    # 排序文件列表，确保按照顺序重命名
    image_files.sort()
    
    # 计数器，从 1 开始
    count = 1
    
    # 遍历每个图片文件并重命名
    for old_name in image_files:
        # 获取当前时间并格式化为'YYYYMMDD_HHMMSS'形式
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 在日期后面拼接上 'jdqsz'
        current_time_with_suffix = f"{current_time}"
        
        # 构建新的图片文件名，形如 'YYYYMMDD_HHMMSS_jdqsz_00001.png'
        extension = os.path.splitext(old_name)[1].lower()
        new_image_name = f"{current_time_with_suffix}_{count:05}{extension}"
        
        # 构建图片文件的完整路径
        old_image_path = os.path.join(folder_path, old_name)
        new_image_path = os.path.join(folder_path, new_image_name)
        
        try:
            # 重命名图片文件
            shutil.move(old_image_path, new_image_path)
            print(f"成功重命名图片: {old_name} -> {new_image_name}")
            
            # 检查是否存在对应的txt文件
            old_txt_name = os.path.splitext(old_name)[0] + '.txt'
            if os.path.isfile(os.path.join(folder_path, old_txt_name)):
                new_txt_name = f"{current_time_with_suffix}_{count:05}.txt"
                new_txt_path = os.path.join(folder_path, new_txt_name)
                # 重命名txt文件
                shutil.move(os.path.join(folder_path, old_txt_name), new_txt_path)
                print(f"成功重命名文本: {old_txt_name} -> {new_txt_name}")
        
        except Exception as e:
            print(f"重命名文件 {old_name} 时发生错误: {e}")
        
        # 更新计数器
        count += 1
    
    print(f"成功重命名 {count - 1} 个图片文件及其对应的txt文件。")

def is_image_file(filename):
    # 判断文件是否为图片文件
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
    ext = os.path.splitext(filename)[1].lower()
    return ext in image_extensions

# 主程序
if __name__ == "__main__":
    folder_path = '/home/xu/AutoLabel-master/labels'
    
    if not os.path.isdir(folder_path):
        print("错误: 输入的路径不是一个有效的文件夹路径。")
    else:
        rename_image_files(folder_path)
