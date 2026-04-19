import time

import cv2
import numpy as np
import onnxruntime


class AttentiveGANDerainNetONNX:
    def __init__(self, model_path, providers=None, intra_op_num_threads=0, inter_op_num_threads=0):
        self.model_path = model_path
        self.providers = ["CPUExecutionProvider"]
        self.intra_op_num_threads = intra_op_num_threads
        self.inter_op_num_threads = inter_op_num_threads
        self.net = self._create_session()
        self.input_name = self.net.get_inputs()[0].name

        input_shape = self.net.get_inputs()[0].shape
        self.input_shape = input_shape
        self.input_height, self.input_width = input_shape[2:]

    def _create_session(self):
        session_options = onnxruntime.SessionOptions()
        session_options.log_severity_level = 3
        if self.intra_op_num_threads > 0:
            session_options.intra_op_num_threads = self.intra_op_num_threads
        if self.inter_op_num_threads > 0:
            session_options.inter_op_num_threads = self.inter_op_num_threads
        return onnxruntime.InferenceSession(
            self.model_path,
            session_options,
            providers=self.providers,
        )

    def prepare_input(self, image):
        input_image = cv2.resize(image, dsize=(self.input_width, self.input_height))
        input_image = input_image.astype(np.float32) / 127.5 - 1.0
        return input_image.transpose(2, 0, 1)[np.newaxis, ...]

    def postprocess(self, output_image, original_width, original_height, original_image=None):
        output_image = np.squeeze(output_image).copy()

        for channel_index in range(output_image.shape[2]):
            channel = output_image[:, :, channel_index]
            min_val = np.min(channel)
            max_val = np.max(channel)
            if max_val > min_val:
                output_image[:, :, channel_index] = (channel - min_val) * 255.0 / (max_val - min_val)
            else:
                output_image[:, :, channel_index] = 0

        output_image = np.clip(output_image, 0, 255).astype(np.uint8)
        output_image = cv2.resize(output_image, (original_width, original_height))
        if original_image is None:
            return output_image
        if self._luminance_correlation(output_image, original_image) < 0:
            output_image = 255 - output_image
        return self._restore_original_chroma(output_image, original_image, original_width, original_height)

    def _luminance_correlation(self, output_image, original_image):
        original_image = cv2.resize(original_image, (output_image.shape[1], output_image.shape[0]))
        output_y = cv2.cvtColor(output_image, cv2.COLOR_BGR2YCrCb)[:, :, 0].astype(np.float32)
        original_y = cv2.cvtColor(original_image, cv2.COLOR_BGR2YCrCb)[:, :, 0].astype(np.float32)
        output_y -= output_y.mean()
        original_y -= original_y.mean()
        denominator = np.linalg.norm(output_y) * np.linalg.norm(original_y)
        if denominator < 1e-6:
            return 0.0
        return float(np.sum(output_y * original_y) / denominator)

    def _restore_original_chroma(self, output_image, original_image, original_width, original_height):
        original_image = cv2.resize(original_image, (original_width, original_height))
        output_ycrcb = cv2.cvtColor(output_image, cv2.COLOR_BGR2YCrCb)
        original_ycrcb = cv2.cvtColor(original_image, cv2.COLOR_BGR2YCrCb)
        output_ycrcb[:, :, 1:] = original_ycrcb[:, :, 1:]
        return cv2.cvtColor(output_ycrcb, cv2.COLOR_YCrCb2BGR)

    def predict(self, image, return_timing=False):
        start_time = time.perf_counter()
        input_image = self.prepare_input(image)
        preprocess_time = time.perf_counter()

        result = self.net.run(None, {self.input_name: input_image})
        inference_time = time.perf_counter()

        output_image = self.postprocess(result[0], image.shape[1], image.shape[0], image)
        end_time = time.perf_counter()

        if not return_timing:
            return output_image

        timing = {
            "preprocess_ms": (preprocess_time - start_time) * 1000,
            "inference_ms": (inference_time - preprocess_time) * 1000,
            "postprocess_ms": (end_time - inference_time) * 1000,
            "total_ms": (end_time - start_time) * 1000,
        }
        return output_image, timing
