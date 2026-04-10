import time

import cv2
import numpy as np
import onnxruntime


class DiffusionLowLight:
    def __init__(self, model_path, providers=None, intra_op_num_threads=0, inter_op_num_threads=0):
        self.model_path = model_path
        self.providers = providers or ["CPUExecutionProvider"]
        self.intra_op_num_threads = intra_op_num_threads
        self.inter_op_num_threads = inter_op_num_threads
        self.onnx_session = self._create_session(self.providers)
        self.input_name = self.onnx_session.get_inputs()[0].name

        input_shape = self.onnx_session.get_inputs()[0].shape
        self.input_shape = input_shape
        self.batch_size = input_shape[0] if isinstance(input_shape[0], int) else None
        self.input_height = input_shape[2]
        self.input_width = input_shape[3]

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
        self.onnx_session = self._create_session(self.providers)
        self.input_name = self.onnx_session.get_inputs()[0].name

    def prepare_input(self, image):
        input_image = cv2.resize(
            cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
            dsize=(self.input_width, self.input_height),
        )
        input_image = input_image.astype(np.float32) / 255.0
        input_image = input_image.transpose(2, 0, 1)
        input_image = np.expand_dims(input_image, axis=0)
        return input_image

    def supports_batch(self):
        return self.batch_size is None or self.batch_size > 1

    def max_batch_size(self):
        return self.batch_size

    def prepare_batch_input(self, images):
        batch = []
        original_sizes = []
        for image in images:
            original_sizes.append((image.shape[1], image.shape[0]))
            prepared = cv2.resize(
                cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
                dsize=(self.input_width, self.input_height),
            )
            prepared = prepared.astype(np.float32) / 255.0
            prepared = prepared.transpose(2, 0, 1)
            batch.append(prepared)
        return np.stack(batch, axis=0), original_sizes

    def _run_session(self, input_tensor):
        try:
            return self.onnx_session.run(None, {self.input_name: input_tensor})
        except Exception:
            provider_text = " ".join(self.providers)
            if "ExecutionProvider" not in provider_text:
                raise
            self._fallback_to_cpu()
            return self.onnx_session.run(None, {self.input_name: input_tensor})

    def predict(self, image, return_timing=False):
        start_time = time.perf_counter()
        input_image = self.prepare_input(image)
        preprocess_time = time.perf_counter()

        result = self._run_session(input_image)
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

    def predict_batch(self, images, return_timing=False):
        if not images:
            return [] if not return_timing else ([], {"batch_supported": self.supports_batch(), "batch_size": 0})

        if not self.supports_batch():
            results = []
            total_timing = {
                "preprocess_ms": 0.0,
                "inference_ms": 0.0,
                "postprocess_ms": 0.0,
                "total_ms": 0.0,
            }
            for image in images:
                output_image, timing = self.predict(image, return_timing=True)
                results.append(output_image)
                for key in total_timing:
                    total_timing[key] += float(timing.get(key, 0.0))
            total_timing["batch_supported"] = False
            total_timing["batch_size"] = len(images)
            if not return_timing:
                return results
            return results, total_timing

        if self.batch_size is not None and len(images) > self.batch_size:
            raise ValueError(f"batch size {len(images)} exceeds model limit {self.batch_size}")

        start_time = time.perf_counter()
        input_tensor, original_sizes = self.prepare_batch_input(images)
        preprocess_time = time.perf_counter()

        result = self._run_session(input_tensor)
        inference_time = time.perf_counter()

        output_batch = np.asarray(result[0])
        outputs = []
        for output_image, (original_width, original_height) in zip(output_batch, original_sizes):
            output_image = output_image.transpose(1, 2, 0)
            output_image = (output_image * 255).astype(np.uint8)
            output_image = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
            output_image = cv2.resize(output_image, (original_width, original_height))
            outputs.append(output_image)
        end_time = time.perf_counter()

        if not return_timing:
            return outputs

        timing = {
            "preprocess_ms": (preprocess_time - start_time) * 1000,
            "inference_ms": (inference_time - preprocess_time) * 1000,
            "postprocess_ms": (end_time - inference_time) * 1000,
            "total_ms": (end_time - start_time) * 1000,
            "batch_supported": True,
            "batch_size": len(images),
        }
        return outputs, timing
