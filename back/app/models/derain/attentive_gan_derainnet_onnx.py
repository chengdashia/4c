import time

import cv2
import numpy as np
import onnxruntime


class AttentiveGANDerainNetONNX:
    def __init__(self, model_path, providers=None, intra_op_num_threads=0, inter_op_num_threads=0):
        self.model_path = model_path
        self.providers = providers or ["CPUExecutionProvider"]
        self.intra_op_num_threads = intra_op_num_threads
        self.inter_op_num_threads = inter_op_num_threads
        self.net = self._create_session(self.providers)
        self.input_name = self.net.get_inputs()[0].name

        input_shape = self.net.get_inputs()[0].shape
        self.input_shape = input_shape
        self.input_height, self.input_width = input_shape[2:]

    def _create_session(self, providers):
        session_options = onnxruntime.SessionOptions()
        session_options.log_severity_level = 3
        if self.intra_op_num_threads > 0:
            session_options.intra_op_num_threads = self.intra_op_num_threads
        if self.inter_op_num_threads > 0:
            session_options.inter_op_num_threads = self.inter_op_num_threads
        return onnxruntime.InferenceSession(
            self.model_path,
            session_options,
            providers=providers,
        )

    def _fallback_to_cpu(self):
        if self.providers == ["CPUExecutionProvider"]:
            raise RuntimeError("CPU provider fallback unavailable")
        self.providers = ["CPUExecutionProvider"]
        self.net = self._create_session(self.providers)
        self.input_name = self.net.get_inputs()[0].name

    def _run_session(self, input_tensor):
        try:
            return self.net.run(None, {self.input_name: input_tensor})
        except Exception:
            provider_text = " ".join(self.providers)
            if "ExecutionProvider" not in provider_text:
                raise
            self._fallback_to_cpu()
            return self.net.run(None, {self.input_name: input_tensor})

    def prepare_input(self, image):
        input_image = cv2.resize(image, dsize=(self.input_width, self.input_height))
        input_image = input_image.astype(np.float32) / 127.5 - 1.0
        return input_image.transpose(2, 0, 1)[np.newaxis, ...]

    def postprocess(self, output_image, original_width, original_height):
        output_image = np.squeeze(output_image)
        if output_image.ndim == 3 and output_image.shape[0] == 3:
            output_image = output_image.transpose(1, 2, 0)

        for channel_index in range(output_image.shape[2]):
            channel = output_image[:, :, channel_index]
            min_val = np.min(channel)
            max_val = np.max(channel)
            if max_val > min_val:
                output_image[:, :, channel_index] = (channel - min_val) * 255.0 / (max_val - min_val)
            else:
                output_image[:, :, channel_index] = 0

        output_image = np.clip(output_image, 0, 255).astype(np.uint8)
        return cv2.resize(output_image, (original_width, original_height))

    def predict(self, image, return_timing=False):
        start_time = time.perf_counter()
        input_image = self.prepare_input(image)
        preprocess_time = time.perf_counter()

        result = self._run_session(input_image)
        inference_time = time.perf_counter()

        output_image = self.postprocess(result[0], image.shape[1], image.shape[0])
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
