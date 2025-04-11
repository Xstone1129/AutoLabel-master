import os
from shutil import copy2

def split_images_into_folders(source_folder, target_folder, images_per_folder=100):
    # 确保目标文件夹存在
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    # 获取所有图片文件
    images = [f for f in os.listdir(source_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    total_images = len(images)
    
    # 分割图片到不同的文件夹
    for i in range(0, total_images, images_per_folder):
        folder_name = f"folder_{i//images_per_folder + 1}"
        folder_path = os.path.join(target_folder, folder_name)
        
        # 创建新的文件夹
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # 复制图片到新的文件夹
        for j in range(images_per_folder):
            if i + j < total_images:
                image_name = images[i + j]
                image_path = os.path.join(source_folder, image_name)
                destination_path = os.path.join(folder_path, image_name)
                copy2(image_path, destination_path)
            else:
                break

# 使用示例
source_folder = '/home/xu/ACE/AutoLabel-master/20240214(29w)/pratice'  # 替换为你的图片文件夹路径
target_folder = '/home/xu/ACE/AutoLabel-master/20240214(29w)/pratice_sort'  # 替换为你想要创建的目标文件夹路径
split_images_into_folders(source_folder, target_folder)