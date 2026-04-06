#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import time
import cv2
import numpy as np
import onnxruntime
import matplotlib.pyplot as plt


class Diffusion_Low_Light:
    def __init__(self, modelpath):
        so = onnxruntime.SessionOptions()
        so.log_severity_level = 3
        # Initialize model
        # net = cv2.dnn.readNet(modelpath)  ###读取失败
        self.onnx_session = onnxruntime.InferenceSession(modelpath, so)
        self.input_name = self.onnx_session.get_inputs()[0].name

        input_shape = self.onnx_session.get_inputs()[0].shape
        self.input_height = input_shape[2]
        self.input_width = input_shape[3]

    def prepare_input(self, image):
        input_image = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), dsize=(
            self.input_width, self.input_height))
        input_image = input_image.astype(np.float32) / 255.0
        input_image = input_image.transpose(2, 0, 1)
        input_image = np.expand_dims(input_image, axis=0)
        return input_image

    def detect(self, image, return_timing=False):
        start_time = time.perf_counter()
        input_image = self.prepare_input(image)
        preprocess_time = time.perf_counter()

        # Perform inference on the image
        result = self.onnx_session.run(None, {self.input_name: input_image})
        inference_time = time.perf_counter()

        # Post process:squeeze, RGB->BGR, Transpose, uint8 cast
        output_image = np.squeeze(result[0])
        output_image = output_image.transpose(1, 2, 0)
        output_image = output_image * 255
        output_image = output_image.astype(np.uint8)
        output_image = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
        output_image = cv2.resize(output_image, (image.shape[1], image.shape[0]))
        end_time = time.perf_counter()

        if not return_timing:
            return output_image

        timing = {
            'preprocess_ms': (preprocess_time - start_time) * 1000,
            'inference_ms': (inference_time - preprocess_time) * 1000,
            'postprocess_ms': (end_time - inference_time) * 1000,
            'total_ms': (end_time - start_time) * 1000,
        }
        return output_image, timing


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgpath', type=str,
                        default='imgs/22.png', help="image path")
    parser.add_argument('--modelpath', type=str,
                        default='weights/diffusion_low_light_1x3x384x640.onnx', help="image path")
    args = parser.parse_args()

    mynet = Diffusion_Low_Light(args.modelpath)
    srcimg = cv2.imread(args.imgpath)
    dstimg, timing = mynet.detect(srcimg, return_timing=True)
    print('Low-light timing for one image:')
    print(f"  preprocess: {timing['preprocess_ms']:.2f} ms")
    print(f"  inference : {timing['inference_ms']:.2f} ms")
    print(f"  postprocess: {timing['postprocess_ms']:.2f} ms")
    print(f"  total     : {timing['total_ms']:.2f} ms")

    # cv2.namedWindow('srcimg', cv2.WINDOW_NORMAL)
    # cv2.imshow('srcimg', srcimg)
    # cv2.namedWindow('dstimg', cv2.WINDOW_NORMAL)
    # cv2.imshow('dstimg', dstimg)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.title('srcimg', color='red')

    plt.subplot(1, 2, 2)
    plt.imshow(cv2.cvtColor(dstimg, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.title('dstimg', color='red')

    plt.show()
    # plt.savefig('result.jpg', dpi=700, bbox_inches='tight') ###保存高清图
    plt.close()
