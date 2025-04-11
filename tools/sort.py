import os
import argparse
import shutil
from pathlib import Path


"""
1是哨兵
2是2号
3是3号
4是
"""
def parse_args():
    parser = argparse.ArgumentParser(description="数据集分类工具")
    parser.add_argument("--input", "-i", type=str,help="输入数据集路径(包含图片和txt文件的文件夹)",default="/home/xu/ACE/DATASET/2025_03_29_HERO_OUTPUT_0.97")
    parser.add_argument("--output", "-o", type=str,help="输出根目录路径（自动创建分类文件夹）",default="/home/xu/ACE/DATASET/2025_03_29_HERO_OUTPUT_0.97_sort")
    parser.add_argument("--img-ext", type=str, nargs="+",help="支持的图片扩展名(默认：.jpg .png .jpeg)", default=[".jpg", ".png", ".jpeg"])
    return parser.parse_args()

def validate_folder_structure(output_root):
    """创建分类文件夹结构"""
    # 创建数字分类文件夹（1-20）
    for i in range(0, 65):
        Path(output_root, str(i)).mkdir(parents=True, exist_ok=True)
    # 创建多目标文件夹（100）
    Path(output_root, "100").mkdir(parents=True, exist_ok=True)
    
    print(f"已创建分类文件夹结构：{output_root}/[1-20, 100]")

def process_dataset(input_dir, output_root, img_extensions):
    """处理数据集主逻辑"""
    # 统计信息
    stats = {"total": 0, "success": 0, "multi_target": 0, "no_image": 0, "invalid_txt": 0}
    
    # 遍历所有txt文件
    for txt_path in Path(input_dir).glob("**/*.txt"):
        stats["total"] += 1
        
        # 查找对应的图片文件
        img_path = None
        for ext in img_extensions:
            candidate = txt_path.with_suffix(ext)
            if candidate.exists():
                img_path = candidate
                break
        
        # 处理txt文件内容
        target_dir, reason = process_txt_file(txt_path)
        
        # 分类处理
        if target_dir is None:
            stats["invalid_txt"] += 1
            print(f"跳过无效文件：{txt_path} ({reason})")
            continue
            
        if img_path is None:
            stats["no_image"] += 1
            print(f"找不到图片文件：{txt_path}")
            continue
            
        # 构建目标路径
        dest_folder = Path(output_root, str(target_dir))
        
        try:
            # 复制文件（保持同名）
            shutil.copy2(txt_path, dest_folder)
            shutil.copy2(img_path, dest_folder)
            stats["success"] += 1
            if target_dir == 100:
                stats["multi_target"] += 1
        except Exception as e:
            print(f"文件复制失败：{txt_path} -> {dest_folder} ({str(e)})")
    
    # 输出统计报告
    print("\n处理完成!统计结果：")
    print(f"总处理文件对：{stats['total']}")
    print(f"成功分类：{stats['success']}")
    print(f"多目标文件：{stats['multi_target']}")
    print(f"缺少图片文件：{stats['no_image']}")
    print(f"无效txt文件:{stats['invalid_txt']}")

def process_txt_file(txt_path):
    """解析txt文件并返回目标分类目录"""
    try:
        with open(txt_path, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            
        # 空文件处理
        if not lines:
            return None, "空文件"
            
        # 多目标处理
        if len(lines) > 1:
            return 100, "multi-target"
            
        # 单目标处理
        parts = lines[0].split()
        if not parts:
            return None, "空行"
            
        try:
            class_id = int(parts[0])
            if 0 <= class_id <= 64:
                return class_id, "valid"
            return 100, "invalid-class-id"
        except ValueError:
            return None, "非数字类别"
            
    except Exception as e:
        return None, f"读取失败：{str(e)}"

def remove_empty_folders(root_dir):
    """删除空文件夹"""
    for folder in Path(root_dir).iterdir():
        if folder.is_dir() and not any(folder.iterdir()):  # 文件夹为空
            folder.rmdir()
            print(f"删除空文件夹：{folder}")

if __name__ == "__main__":
    args = parse_args()
    
    # 验证路径有效性
    input_dir = Path(args.input)
    if not input_dir.is_dir():
        raise ValueError(f"输入路径不存在或不是目录：{args.input}")
    
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    
    # 创建分类文件夹结构
    validate_folder_structure(output_root)
    
    # 开始处理
    process_dataset(input_dir, output_root, args.img_ext)
    
    # 删除空文件夹
    remove_empty_folders(output_root)
    
    