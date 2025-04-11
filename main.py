# coding: utf-8
import os
import sys
import random
import time
import threading
import argparse
from datetime import datetime
from copy import deepcopy
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm
import gxipy as gx

# from model.model_28cls import Model
# from model.model_32cls import Model
# from model.model_36cls import Model
from model.model_64cls import Model
from distribution_analyzer import DistributionAnalyzer
from thirdparty.bilibili import BiliBili


class Target:
    __slots__ = ["cls", "pts"]

    def __init__(self):
        self.cls = 0
        self.pts = np.zeros((4, 2), dtype=np.int32)


class Annotator:
    def __init__(self):
        self.failed_files = []
        self.parser = self._init_parser()
        self.args = self.parser.parse_args()
        self._validate_args()

        self.model = Model(self.args.model)
        self.analyzer = DistributionAnalyzer()
        self.cap = None
        self.writer_lock = threading.Lock()
        self._prepare_output_dir()

    def _init_parser(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="Auto Labeling Tool for Object Detection Dataset v2.0",
        )
        parser.add_argument(
            "--type",
            "-t",
            type=str,
            choices=["daheng", "local_imgs", "local_video", "stream"],
            help="Input source type",
            default="local_video",
        )
        parser.add_argument(
            "--input",
            "-i",
            type=str,
            help="Input path (file/directory/stream URL)",
            default="/home/xu/视频/2024中部区域赛/2024RMUChero",
        )
        parser.add_argument(
            "--dst_dir",
            "-o",
            type=str,
            help="Output directory for labeled data",
            default="/home/xu/ACE/DATASET/2025_03_29_HERO_OUTPUT",
        )
        parser.add_argument(
            "--model",
            "-m",
            type=str,
            help="Path to ONNX model file",
            default="./model/model_64cls.onnx",
        )
        parser.add_argument(
            "--skip_frames",
            "-s",
            type=int,
            help="Number of frames to skip between processing",
            default=0,
        )
        parser.add_argument(
            "--min_confidence",
            "-c",
            type=float,
            help="Minimum detection confidence threshold",
            default=0.5,
        )
        parser.add_argument(
            "--skip_blank_frames",
            "-b",
            type=int,
            help="Number of blank frames to skip when black/white screen is detected",
            default=10,
        )
        return parser

    def _validate_args(self):
        if self.args.type in ["local_imgs", "local_video"] and not self.args.input:
            raise ValueError("Input path is required for local images/video")
        if self.args.type == "stream" and not self.args.input:
            raise ValueError("Stream URL is required for stream type")

    def _prepare_output_dir(self):
        Path(self.args.dst_dir).mkdir(parents=True, exist_ok=True)

    def _get_video_files(self):
        path = Path(self.args.input)
        if path.is_dir():
            video_files = []
            # 添加对.db3和.DB3扩展名的支持
            #其实并不支持DB3
            for ext in ("*.mp4", "*.avi", "*.MP4", "*.AVI", "*.db3", "*.DB3"):
                video_files.extend(path.glob(f"**/{ext}"))
            return sorted(list(set(video_files)))
        elif path.is_file():
            return [path]
        raise FileNotFoundError(f"Invalid input path: {self.args.input}")

    def _init_capture(self):
        src_map = {
            "daheng": self._init_daheng,
            "local_imgs": self._load_images,
            "local_video": self._get_video_files,
            "stream": lambda: cv2.VideoCapture(self._get_bilibili_stream()),
        }
        return src_map[self.args.type]()

    def _init_daheng(self):
        device_manager = gx.DeviceManager()
        dev_num, dev_info_list = device_manager.update_device_list()
        if dev_num == 0:
            raise RuntimeError("No Daheng devices found")

        cam = device_manager.open_device_by_index(1)
        cam.stream_on()
        cam.BalanceWhiteAuto.set(2)
        return cam

    def _load_images(self):
        valid_ext = {".jpg", ".png", ".jpeg", ".bmp", ".tiff"}
        img_files = [
            f
            for f in Path(self.args.input).rglob("*")
            if f.suffix.lower() in valid_ext and f.is_file()
        ]
        return [cv2.imread(str(p)) for p in tqdm(img_files, desc="Loading images")]

    def _process_frame(self, frame, frame_idx=0):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blank_cnt = 0

        # 检测黑白屏并跳过
        if np.mean(gray) < 10 and np.var(gray) < 10:
            blank_cnt += 1
            if blank_cnt % self.args.skip_blank_frames == 0:
                print(
                    f"[WARN] Blank screen detected, skipping next {self.args.skip_blank_frames} frames."
                )
            return None

        results = self.model.infer(frame)
        # if results:  
        #     print("1111111111111111111111111111")
        # 有效检测
        valid_detections = []
        labels = []

        for det in results:
            if det.conf < self.args.min_confidence:
                continue

            target = self._to_36cls(det)
            
            label_data = self._format_label(target, frame.shape)

            valid_detections.append(det)
            # if not valid_detections:
            #     print("No valid detections found.")
            # else:
            #     print(f"Found {len(valid_detections)} valid detections.")
            labels.append(label_data)

        self._visualize(frame, valid_detections)
        return labels

    @staticmethod
    def _to_36cls(det):
        target = Target()
        target.cls = 9 * (det.color // 2) + det.id
        # target.cls = 7 * (det.color) + det.id
        # print(f"target.cls: {target.cls}")
        target.pts = np.array(det.pts, dtype=np.int32)
        return target

    @staticmethod
    def _format_label(target, img_shape):
        h, w = img_shape[:2]
        label = [str(target.cls)]
        for x, y in target.pts:
            label.append(f"{x / w:.5f}")
            label.append(f"{y / h:.5f}")
        return " ".join(label)

    def _visualize(self, frame, detections):
        display_frame = deepcopy(frame)
        for det in detections:
            color = (0, 255, 0)  # BGR
            pts = det.pts.reshape((-1, 1, 2)).astype(np.int32)
            cv2.polylines(display_frame, [pts], True, color, 2)

            text = f"ID:{det.id} Conf:{det.conf:.2f}"
            cv2.putText(
                display_frame,
                text,
                (pts[0][0][0], pts[0][0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )
            # print(f"pts: {pts[0][0]}")
        cv2.imshow("Preview", display_frame)
        cv2.waitKey(1)

    def save_data(self, frame, labels, frame_idx, video_name):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base_name = f"{video_name}_{timestamp}_{frame_idx:08d}"

        img_path = Path(self.args.dst_dir) / f"{base_name}.jpg"
        cv2.imwrite(str(img_path), frame)

        label_path = img_path.with_suffix(".txt")
        with open(label_path, "w") as f:
            f.write("\n".join(labels))

    def _process_single_video(self, video_path):
        print(f"\nProcessing: {video_path}")
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"Failed to open video: {video_path}")
            self.failed_files.append(str(video_path))  # 记录失败文件
            return 0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = self.args.skip_frames + 1
        video_name = Path(video_path).stem
        saved_count = 0  # 新增保存计数器

        try:
            with tqdm(total=total_frames, unit="frame", desc=video_name) as pbar:
                frame_idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_idx % frame_interval == 0:
                        labels = self._process_frame(frame, frame_idx)
                        if labels:
                            with self.writer_lock:
                                self.save_data(frame, labels, frame_idx, video_name)
                                saved_count += 1  # 每次保存时增加计数

                    pbar.update(1)
                    frame_idx += 1
        except Exception as e:
            print(f"处理视频时发生异常: {str(e)}")
            self.failed_files.append(str(video_path))  # 记录异常视频
            return 0
        finally:
            cap.release()

        print(f"√ 完成处理: {video_name}")
        print(f"• 总处理帧数: {frame_idx}")
        print(f"• 保存有效帧数: {saved_count}")
        print(f"• 保存率: {saved_count / (frame_idx / frame_interval):.1%}")
        return saved_count

    def _process_image_batch(self):
        print(f"\nProcessing {len(self.cap)} images...")
        for idx, img in enumerate(tqdm(self.cap)):
            labels = self._process_frame(img)
            if labels:
                self.save_data(img, labels, idx, "image")

    def run(self):
        try:
            self.cap = self._init_capture()

            if self.args.type == "local_imgs":
                self._process_image_batch()
            elif self.args.type == "local_video":
                if isinstance(self.cap, list):
                    total_videos = len(self.cap)
                    for idx, video_path in enumerate(self.cap, 1):
                        print(f"\n{'=' * 40}")
                        print(f"正在处理视频 ({idx}/{total_videos}): {video_path}")
                        self._process_single_video(video_path)
                else:
                    print(f"\n{'=' * 40}")
                    print(f"正在处理视频 (1/1): {self.cap}")
                    self._process_single_video(self.cap)

        except KeyboardInterrupt:
            print("\nUser interrupted processing.")
        except Exception as e:
            print(f"\nCritical error: {str(e)}")
        finally:
            # 新增失败文件输出
            if hasattr(self.cap, "stream_off"):
                self.cap.stream_off()
            cv2.destroyAllWindows()

            if self.failed_files:
                print("\n\n" + "=" * 60)
                print(f"失效视频列表(共 {len(self.failed_files)} 个):")
                for idx, path in enumerate(self.failed_files, 1):
                    print(f"{idx}. {path}")

                # 保存到日志文件
                log_path = Path(self.args.dst_dir) / "failed_videos.log"
                with open(log_path, "w") as f:
                    f.write("\n".join(self.failed_files))
                print(f"\n失败列表已保存至: {log_path}")


if __name__ == "__main__":
    try:
        annotator = Annotator()
        annotator.run()
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)
