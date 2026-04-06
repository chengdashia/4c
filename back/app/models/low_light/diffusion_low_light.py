import time

import cv2
import numpy as np
import onnxruntime


class DiffusionLowLight:
    def __init__(self, model_path):
        session_options = onnxruntime.SessionOptions()
        session_options.log_severity_level = 3
        self.onnx_session = onnxruntime.InferenceSession(model_path, session_options)
        self.input_name = self.onnx_session.get_inputs()[0].name

        input_shape = self.onnx_session.get_inputs()[0].shape
        self.input_height = input_shape[2]
        self.input_width = input_shape[3]

    def prepare_input(self, image):
        input_image = cv2.resize(
            cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
            dsize=(self.input_width, self.input_height),
        )
        input_image = input_image.astype(np.float32) / 255.0
        input_image = input_image.transpose(2, 0, 1)
        input_image = np.expand_dims(input_image, axis=0)
        return input_image

    def predict(self, image, return_timing=False):
        start_time = time.perf_counter()
        input_image = self.prepare_input(image)
        preprocess_time = time.perf_counter()

        result = self.onnx_session.run(None, {self.input_name: input_image})
        inference_time = time.perf_counter()

        output_image = np.squeeze(result[0])
        output_image = output_image.transpose(1, 2, 0)
        output_image = (output_image * 255).astype(np.uint8)
        output_image = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
        output_image = cv2.resize(output_image, (image.shape[1], image.shape[0]))
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
