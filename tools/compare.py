import os
import shutil
import argparse
from pathlib import Path
from imagededup.methods import CNN
import tempfile

def parse_arguments():
    parser = argparse.ArgumentParser(description="数据集去重工具")
    parser.add_argument("--src", type=str, help="原始数据集路径", default="/home/xu/ACE/DATASET/2025_03_29_HERO_OUTPUT")
    parser.add_argument("--dst", type=str, help="输出数据集路径", default="/home/xu/ACE/DATASET/2025_03_29_HERO_OUTPUT_0.97")
    parser.add_argument("--thres", type=float, default=0.97, help="相似度阈值 (0-1)")
    parser.add_argument("--chunk", type=int, default=10000, help="分块处理数量")
    parser.add_argument("--img-ext", nargs="+", default=[".jpg", ".png", ".jpeg"], 
                        help="支持的图片格式")
    return parser.parse_args()

def clean_output_directory(dst):
    """清空输出目录"""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)

def process_chunk(files_chunk, args, cnn_hasher, chunk_index, total_chunks):
    """处理单个数据块"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 创建临时文件结构
        tmp_map = {}
        for rel_path, img_file in files_chunk:
            tmp_path = Path(tmp_dir) / rel_path / img_file
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(Path(args.src) / rel_path / img_file, tmp_path)
            tmp_map[img_file] = str(tmp_path)

        # 计算哈希值（确保传递的是字符串路径）
        encodings = cnn_hasher.encode_images(image_dir=str(tmp_dir))

        # 获取需要删除的文件列表（确保传递的是 `encodings` 字典）
        duplicates = cnn_hasher.find_duplicates_to_remove(
            encoding_map=encodings, min_similarity_threshold=args.thres
        )

        kept_images = 0
        # 创建目标目录并复制文件
        for rel_path, img_file in files_chunk:
            if img_file not in duplicates:
                src_img = Path(args.src) / rel_path / img_file
                dst_img = Path(args.dst) / rel_path / img_file
                
                # 创建目标目录
                dst_img.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制图片文件（如果不存在）
                if not dst_img.exists():
                    shutil.copy(src_img, dst_img)
                    kept_images += 1
                
                # 处理对应的txt文件
                txt_file = src_img.with_suffix('.txt')
                if txt_file.exists():
                    dst_txt = dst_img.with_suffix('.txt')
                    if not dst_txt.exists():
                        shutil.copy(txt_file, dst_txt)
        
        print(f"块 {chunk_index}/{total_chunks} 处理完成，保留 {kept_images} 张图片。")

def main():
    args = parse_arguments()
    cnn_hasher = CNN()
    
    # 清空输出目录
    clean_output_directory(args.dst)
    
    # 获取所有图片文件（保留目录结构）
    all_files = []
    for root, _, files in os.walk(args.src):
        for f in files:
            if Path(f).suffix.lower() in args.img_ext:
                rel_path = os.path.relpath(root, args.src)
                all_files.append((rel_path, f))
    
    print(f"输入目录包含 {len(all_files)} 张图片。")
    
    total_chunks = (len(all_files) - 1) // args.chunk + 1
    
    # 分块处理
    for i in range(0, len(all_files), args.chunk):
        chunk = all_files[i:i+args.chunk]
        chunk_index = i // args.chunk + 1
        print(f"正在处理块 {chunk_index}/{total_chunks}，共 {len(chunk)} 张图像...")
        process_chunk(chunk, args, cnn_hasher, chunk_index, total_chunks)
    
    final_count = sum(1 for _ in Path(args.dst).rglob('*') if _.suffix.lower() in args.img_ext)
    print("处理完成！")
    print(f"原始数据量: {len(all_files)}")
    print(f"去重后数据量: {final_count}")

if __name__ == "__main__":
    main()
