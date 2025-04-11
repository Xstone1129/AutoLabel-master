import os
import shutil
import argparse

def split_folder(input_dir, output_dir, split_size):
    # 检查输入目录
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")
    
    # 创建输出目录（若不存在）
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    total_files = len(files)

    folder_index = 1
    for i in range(0, total_files, split_size):
        folder_name = os.path.join(output_dir, f"split_{folder_index}")
        os.makedirs(folder_name, exist_ok=True)

        for file in files[i:i + split_size]:
            src = os.path.join(input_dir, file)
            dst = os.path.join(folder_name, file)
            shutil.copy(src, dst)  # 使用复制而不是移动

        print(f"Created folder '{folder_name}' with {len(files[i:i + split_size])} files.")
        folder_index += 1

def main():
    parser = argparse.ArgumentParser(description="Split a large folder into smaller folders.")
    parser.add_argument("--type", "-t", type=str, choices=["split"], default="split", help="Operation type")
    parser.add_argument("--input", "-i", type=str, default="/home/xu/ACE/AutoLabel-master/20240214(2w)", help="Input folder path")
    parser.add_argument("--output", "-o", type=str, default="/home/xu/ACE/AutoLabel-master/20240214(2w)_spilt", help="Output folder path")
    parser.add_argument("--size", "-s", type=int, default=50000, help="Number of files per split folder")

    args = parser.parse_args()

    if args.type == "split":
        split_folder(args.input, args.output, args.size)
    else:
        print("Unsupported operation type.")

if __name__ == "__main__":
    main()
