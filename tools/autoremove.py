import os
import argparse

# 配置命令行参数
parser = argparse.ArgumentParser()
parser.add_argument("--dir", type=str, default="/home/xu/ACE/AutoLabel-master/labels_0.97", help="操作的文件夹.")
arg = parser.parse_args()

def process_txt_files(folder_path):
    # 获取文件夹中的所有文件
    all_files = os.listdir(folder_path)
    
    # 遍历所有文件
    for file in all_files:
        file_path = os.path.join(folder_path, file)
        
        # 检查是否为txt文件
        if file.endswith('.txt'):
            # 提取txt文件名（不包括扩展名）
            txt_filename = os.path.splitext(file)[0]
            
            # 构建对应的图像文件路径
            image_file = os.path.join(folder_path, txt_filename + '.jpg')
            
            # 检查图像文件是否存在，不存在则删除txt文件
            if not os.path.isfile(image_file):
                print(f"删除没有对应图片的txt文件: {file_path}")
                os.remove(file_path)

# 执行文件处理
folder_path = arg.dir  # 获取命令行传入的文件夹路径
process_txt_files(folder_path)
