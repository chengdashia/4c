import ast
import time

import cv2
import numpy as np
import onnxruntime


class YOLO26ONNX:
    def __init__(self, model_path, conf_thres=0.25, iou_thres=0.45, providers=None):
        session_options = onnxruntime.SessionOptions()
        session_options.log_severity_level = 3
        self.onnx_session = onnxruntime.InferenceSession(
            model_path,
            sess_options=session_options,
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
            return {int(key): value for key, value in names.items()}
        return {}

    def letterbox(self, image, color=(114, 114, 114)):
        height, width = image.shape[:2]
        ratio = min(self.input_width / width, self.input_height / height)
        new_width, new_height = int(round(width * ratio)), int(round(height * ratio))

        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((self.input_height, self.input_width, 3), color, dtype=np.uint8)

        dw = (self.input_width - new_width) / 2
        dh = (self.input_height - new_height) / 2
        left, top = int(round(dw - 0.1)), int(round(dh - 0.1))
        canvas[top : top + new_height, left : left + new_width] = resized
        return canvas, ratio, (left, top)

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
            index = order[0]
            keep.append(index)
            if order.size == 1:
                break

            rest = order[1:]
            same_class = class_ids[rest] == class_ids[index]
            ious = self.compute_iou(boxes[index], boxes[rest])
            rest = rest[~(same_class & (ious > self.iou_thres))]
            order = rest

        return np.array(keep, dtype=np.int64)

    def scale_boxes(self, boxes, image_shape, ratio, pad):
        left, top = pad
        boxes[:, [0, 2]] -= left
        boxes[:, [1, 3]] -= top
        boxes[:, :4] /= ratio

        height, width = image_shape[:2]
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, width)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, height)
        return boxes

    def postprocess(self, outputs, image_shape, ratio, pad):
        pred = np.asarray(outputs[0])

        if pred.ndim == 3 and pred.shape[0] == 1:
            pred = pred[0]

        if pred.ndim == 2 and pred.shape[-1] >= 6:
            pred = pred[pred[:, 4] > self.conf_thres]
            if pred.size == 0:
                return np.empty((0, 6), dtype=np.float32)
            pred[:, :4] = self.scale_boxes(pred[:, :4], image_shape, ratio, pad)
            return pred[:, :6].astype(np.float32)

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

    def predict(self, image, return_timing=False):
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
