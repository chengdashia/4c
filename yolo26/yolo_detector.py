#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import ast
import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
import onnxruntime


class YOLO26_ONNX:
    def __init__(self, modelpath, conf_thres=0.25, iou_thres=0.45, providers=None):
        so = onnxruntime.SessionOptions()
        so.log_severity_level = 3
        self.onnx_session = onnxruntime.InferenceSession(
            modelpath,
            sess_options=so,
            providers=providers or ["CPUExecutionProvider"],
        )
        self.input_name = self.onnx_session.get_inputs()[0].name
        self.output_names = [output.name for output in self.onnx_session.get_outputs()]

        input_shape = self.onnx_session.get_inputs()[0].shape
        self.input_height = input_shape[2] if isinstance(input_shape[2], int) else 640
        self.input_width = input_shape[3] if isinstance(input_shape[3], int) else 640

        metadata = self.onnx_session.get_modelmeta().custom_metadata_map
        self.names = self._parse_names(metadata.get("names"))
        self.end2end = self._parse_bool(metadata.get("end2end", "False"))
        args = self._parse_literal(metadata.get("args", "{}"))
        self.end2end = self.end2end or bool(args.get("nms", False))

        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

    @staticmethod
    def _parse_literal(value, default=None):
        if value is None:
            return default
        try:
            return ast.literal_eval(value) if isinstance(value, str) else value
        except (ValueError, SyntaxError):
            return default

    @staticmethod
    def _parse_bool(value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes"}

    def _parse_names(self, names_value):
        names = self._parse_literal(names_value, default={})
        if isinstance(names, list):
            return {i: name for i, name in enumerate(names)}
        if isinstance(names, dict):
            return {int(k): v for k, v in names.items()}
        return {}

    def letterbox(self, image, color=(114, 114, 114)):
        h, w = image.shape[:2]
        r = min(self.input_width / w, self.input_height / h)
        new_w, new_h = int(round(w * r)), int(round(h * r))

        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((self.input_height, self.input_width, 3), color, dtype=np.uint8)

        dw = (self.input_width - new_w) / 2
        dh = (self.input_height - new_h) / 2
        left, top = int(round(dw - 0.1)), int(round(dh - 0.1))
        canvas[top : top + new_h, left : left + new_w] = resized
        return canvas, r, (left, top)

    def prepare_input(self, image):
        input_image, ratio, pad = self.letterbox(image)
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
        input_image = input_image.astype(np.float32) / 255.0
        input_image = input_image.transpose(2, 0, 1)
        input_image = np.expand_dims(input_image, axis=0)
        return input_image, ratio, pad

    @staticmethod
    def xywh2xyxy(boxes):
        converted = boxes.copy()
        converted[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
        converted[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
        converted[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
        converted[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
        return converted

    @staticmethod
    def compute_iou(box, boxes):
        x1 = np.maximum(box[0], boxes[:, 0])
        y1 = np.maximum(box[1], boxes[:, 1])
        x2 = np.minimum(box[2], boxes[:, 2])
        y2 = np.minimum(box[3], boxes[:, 3])

        inter = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
        area1 = np.maximum(0.0, box[2] - box[0]) * np.maximum(0.0, box[3] - box[1])
        area2 = np.maximum(0.0, boxes[:, 2] - boxes[:, 0]) * np.maximum(0.0, boxes[:, 3] - boxes[:, 1])
        union = area1 + area2 - inter + 1e-7
        return inter / union

    def nms(self, boxes, scores, class_ids):
        keep = []
        order = scores.argsort()[::-1]

        while order.size > 0:
            i = order[0]
            keep.append(i)
            if order.size == 1:
                break

            rest = order[1:]
            same_class = class_ids[rest] == class_ids[i]
            ious = self.compute_iou(boxes[i], boxes[rest])
            rest = rest[~(same_class & (ious > self.iou_thres))]
            order = rest

        return np.array(keep, dtype=np.int64)

    def scale_boxes(self, boxes, image_shape, ratio, pad):
        left, top = pad
        boxes[:, [0, 2]] -= left
        boxes[:, [1, 3]] -= top
        boxes[:, :4] /= ratio

        h, w = image_shape[:2]
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, w)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, h)
        return boxes

    def postprocess(self, outputs, image_shape, ratio, pad):
        pred = outputs[0]
        pred = np.asarray(pred)

        if pred.ndim == 3 and pred.shape[0] == 1:
            pred = pred[0]

        # End-to-end export usually returns Nx6 => [x1, y1, x2, y2, conf, cls]
        if pred.ndim == 2 and pred.shape[-1] >= 6:
            pred = pred[pred[:, 4] > self.conf_thres]
            if pred.size == 0:
                return np.empty((0, 6), dtype=np.float32)
            pred[:, :4] = self.scale_boxes(pred[:, :4], image_shape, ratio, pad)
            return pred[:, :6].astype(np.float32)

        # Raw export usually returns CxN or NxC, convert to NxC
        if pred.ndim != 2:
            raise ValueError(f"Unexpected output shape: {pred.shape}")
        if pred.shape[0] < pred.shape[1]:
            pred = pred.transpose(1, 0)

        boxes = pred[:, :4]
        class_scores = pred[:, 4:]
        scores = class_scores.max(axis=1)
        class_ids = class_scores.argmax(axis=1)

        mask = scores > self.conf_thres
        boxes = boxes[mask]
        scores = scores[mask]
        class_ids = class_ids[mask]

        if boxes.size == 0:
            return np.empty((0, 6), dtype=np.float32)

        boxes = self.xywh2xyxy(boxes)
        boxes = self.scale_boxes(boxes, image_shape, ratio, pad)
        keep = self.nms(boxes, scores, class_ids)

        detections = np.concatenate(
            [
                boxes[keep],
                scores[keep, None],
                class_ids[keep, None].astype(np.float32),
            ],
            axis=1,
        )
        return detections.astype(np.float32)

    def draw_detections(self, image, detections):
        output_image = image.copy()
        for x1, y1, x2, y2, score, class_id in detections:
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            class_id = int(class_id)
            label = self.names.get(class_id, str(class_id))
            text = f"{label} {score:.2f}"

            cv2.rectangle(output_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                output_image,
                text,
                (x1, max(y1 - 10, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
        return output_image

    def detect(self, image, return_timing=False):
        start_time = time.perf_counter()
        input_image, ratio, pad = self.prepare_input(image)
        preprocess_time = time.perf_counter()

        outputs = self.onnx_session.run(self.output_names, {self.input_name: input_image})
        inference_time = time.perf_counter()

        detections = self.postprocess(outputs, image.shape, ratio, pad)
        output_image = self.draw_detections(image, detections)
        end_time = time.perf_counter()

        if not return_timing:
            return output_image, detections

        timing = {
            "preprocess_ms": (preprocess_time - start_time) * 1000,
            "inference_ms": (inference_time - preprocess_time) * 1000,
            "postprocess_ms": (end_time - inference_time) * 1000,
            "total_ms": (end_time - start_time) * 1000,
        }
        return output_image, detections, timing


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--imgpath", type=str, default="imgs/22.png", help="image path")
    parser.add_argument("--modelpath", type=str, default="yolo26s.onnx", help="onnx model path")
    parser.add_argument("--conf", type=float, default=0.25, help="confidence threshold")
    parser.add_argument("--iou", type=float, default=0.45, help="iou threshold")
    args = parser.parse_args()

    detector = YOLO26_ONNX(args.modelpath, conf_thres=args.conf, iou_thres=args.iou)
    srcimg = cv2.imread(args.imgpath)
    dstimg, detections, timing = detector.detect(srcimg, return_timing=True)

    print("YOLO26 ONNX timing for one image:")
    print(f"  preprocess : {timing['preprocess_ms']:.2f} ms")
    print(f"  inference  : {timing['inference_ms']:.2f} ms")
    print(f"  postprocess: {timing['postprocess_ms']:.2f} ms")
    print(f"  total      : {timing['total_ms']:.2f} ms")
    print(f"  detections : {len(detections)}")

    for x1, y1, x2, y2, score, class_id in detections:
        print(
            f"class={detector.names.get(int(class_id), int(class_id))}, "
            f"score={score:.3f}, box=({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})"
        )

    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.title("srcimg", color="red")

    plt.subplot(1, 2, 2)
    plt.imshow(cv2.cvtColor(dstimg, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.title("dstimg", color="red")

    plt.show()
    plt.close()
