import os
import cv2
import numpy as np
import torch
import onnxruntime as rt
import argparse
import math


class Model:
    def __init__(
        self, model_pth="model_64.onnx", topk=128, conf_thres=0.7, nms_thres=0.1
    ):
        self.model_path = model_pth
        self.topk = topk
        self.conf_thres = conf_thres
        self.nms_thres = nms_thres
        self.model = rt.InferenceSession(
            model_pth, providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        self.input = self.model.get_inputs()[0]
        self.output = self.model.get_outputs()[0]

    def resize(self, img, size):
        height_src, width_src = img.shape[:2]  # origin hw
        resize_factor_x = size[3] / width_src  # resize image to img_size
        resize_factor_y = size[2] / height_src  # resize image to img_size
        resize_factor = min(resize_factor_x, resize_factor_y)
        dst = cv2.resize(
            img,
            (int(width_src * resize_factor), int(height_src * resize_factor)),
            interpolation=cv2.INTER_LINEAR,
        )
        padding_top = round(height_src * (resize_factor_y - resize_factor) * 0.5)
        padding_bottom = size[2] - dst.shape[0] - padding_top
        padding_left = round(width_src * (resize_factor_x - resize_factor) * 0.5)
        padding_right = size[3] - dst.shape[1] - padding_left
        dst = cv2.copyMakeBorder(
            dst,
            padding_top,
            padding_bottom,
            padding_left,
            padding_right,
            cv2.BORDER_CONSTANT,
            (0, 0, 0),
        )
        # print(f"dst.shape: {dst.shape}")
        
        self.resize_matrix = np.array([[1 / resize_factor, 0], [0, 1 / resize_factor]])
        self.resize_vector = np.array([padding_left, padding_top])
        return self.resize_matrix, self.resize_vector, dst

    def is_overlapped(self, bbox_1, bbox_2, iou_thres):
        box_1 = cv2.boundingRect(bbox_1)
        box_2 = cv2.boundingRect(bbox_2)
        intersect_tl = [max(box_1[0], box_2[0]), max(box_1[1], box_2[1])]
        intersect_br = [
            min(box_1[0] + box_1[2], box_2[0] + box_2[2]),
            min(box_1[1] + box_1[3], box_2[1] + box_2[3]),
        ]

        if (intersect_br[0] - intersect_tl[0]) > 0 and (
            intersect_br[1] - intersect_tl[1]
        ) > 0:
            intersect = (intersect_br[0] - intersect_tl[0]) * (
                intersect_br[1] - intersect_tl[1]
            )
            union = box_1[2] * box_1[3] + box_2[2] * box_2[3] - intersect
            iou = intersect / union
            if iou > iou_thres:
                return True
            else:
                return False
        else:
            # print("Fine")
            return False

    def preprocess(self, img):
        """
        brief:形状为 (1, C, H, W) 的 float32 张量，可直接输入模型。
        """
        size = self.input.shape
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # print(img.shape)
        self.resize_matrix, self.resize_vector, img_pre = self.resize(img, size)
        # cv2.imshow("?",img_pre)
        # 模型通常接受批处理输入（即使单张图像）
        img_pre = np.expand_dims(img_pre, axis=0)
        # print(img_pre.shape)

        # 将通道维度从最后移到第二维，适配 PyTorch 的 NCHW 格式或 ONNX 模型输入。
        img_pre = np.transpose(img_pre, (0, 3, 1, 2))
        # 作用：将 uint8 像素值（0-255）转换为 float32，通常用于归一化
        img_pre = img_pre.astype(np.float32)
        return img_pre

    def postprocess(self, final_pred):
        target_list = []
        removed_index = np.zeros([self.topk])
        for i in range(self.topk):
            pred = final_pred[i]
            tmp_bbox = BBox()
            # print(pred)
            tmp_bbox.conf = pred[8]
            # print(tmp_bbox.conf)
            if tmp_bbox.conf < self.conf_thres:
                break
            if removed_index[i] == 1:
                continue
            # Setting boundingbox
            tmp_bbox.pts[0] = np.array(
                np.matmul((pred[0:2] - self.resize_vector), self.resize_matrix),
                dtype=np.int32,
            )
            tmp_bbox.pts[1] = np.array(
                np.matmul((pred[2:4] - self.resize_vector), self.resize_matrix),
                dtype=np.int32,
            )
            tmp_bbox.pts[2] = np.array(
                np.matmul((pred[4:6] - self.resize_vector), self.resize_matrix),
                dtype=np.int32,
            )
            tmp_bbox.pts[3] = np.array(
                np.matmul((pred[6:8] - self.resize_vector), self.resize_matrix),
                dtype=np.int32,
            )

            tmp_bbox.color = int(torch.argmax(pred[9:17]))
            tmp_bbox.id = int(torch.argmax(pred[17:]))

            for j in range(i + 1, self.topk):
                tmp_bbox_j = BBox()
                pred_j = final_pred[j]
                tmp_bbox_j.conf = pred_j[8]

                if tmp_bbox_j.conf < self.conf_thres:
                    break
                if removed_index[j] == 1:
                    continue
                tmp_bbox_j.pts[0] = np.array(
                    np.matmul((pred_j[0:2] - self.resize_vector), self.resize_matrix),
                    dtype=np.int32,
                )
                tmp_bbox_j.pts[1] = np.array(
                    np.matmul((pred_j[2:4] - self.resize_vector), self.resize_matrix),
                    dtype=np.int32,
                )
                tmp_bbox_j.pts[2] = np.array(
                    np.matmul((pred_j[4:6] - self.resize_vector), self.resize_matrix),
                    dtype=np.int32,
                )
                tmp_bbox_j.pts[3] = np.array(
                    np.matmul((pred_j[6:8] - self.resize_vector), self.resize_matrix),
                    dtype=np.int32,
                )
                if self.is_overlapped(tmp_bbox.pts, tmp_bbox_j.pts, self.nms_thres):
                    removed_index[j] = 1
                    continue

            target_list.append(tmp_bbox)
            # print("add")
        # print(len(target_list))
        return target_list

    def infer(self, img):
        img_pre = self.preprocess(img)
        pred = self.model.run([self.output.name], {self.input.name: img_pre})
        pred_tensor = torch.as_tensor(pred[0][0])
        # print(pred_tensor.shape)
        pred_conf = pred_tensor[:, 8]
        pred_topk_index = torch.topk(pred_conf, k=self.topk, sorted=True).indices
        # dim=0：按行（预测结果维度）提取
        final_pred = torch.index_select(pred_tensor, dim=0, index=pred_topk_index)
        return self.postprocess(final_pred)


class BBox:
    def __init__(self):
        self.pts = np.array([[0, 0], [0, 0], [0, 0], [0, 0]])
        self.conf = 0
        self.color = 0
        self.id = 0
