import torch
import numpy as np
import utils
import os
import time
import torch.nn.functional as F


def data_transform(X):
    return 2 * X - 1.0


def inverse_data_transform(X):
    return torch.clamp((X + 1.0) / 2.0, 0.0, 1.0)


class DiffusiveRestoration:
    def __init__(self, diffusion, args, config):
        super(DiffusiveRestoration, self).__init__()
        self.args = args
        self.config = config
        self.diffusion = diffusion

        if os.path.isfile(args.resume):
            self.diffusion.load_ddm_ckpt(args.resume, ema=True)
            self.diffusion.model.eval()
        else:
            print('Pre-trained diffusion model path is missing!')

    def restore(self, val_loader):
        image_folder = os.path.join(self.args.image_folder, self.config.data.val_dataset)
        total_inference_time = 0.0
        image_count = 0
        with torch.no_grad():
            for i, (x, y) in enumerate(val_loader):
                x_cond = x[:, :3, :, :].to(self.diffusion.device)
                b, c, h, w = x_cond.shape
                img_h_32 = int(32 * np.ceil(h / 32.0))
                img_w_32 = int(32 * np.ceil(w / 32.0))
                x_cond = F.pad(x_cond, (0, img_w_32 - w, 0, img_h_32 - h), 'reflect')

                self._synchronize_device()
                start_time = time.perf_counter()
                x_output = self.diffusive_restoration(x_cond)
                self._synchronize_device()
                elapsed_time = time.perf_counter() - start_time

                x_output = x_output[:, :, :h, :w]
                utils.logging.save_image(x_output, os.path.join(image_folder, f"{y[0]}.png"))
                total_inference_time += elapsed_time
                image_count += 1
                print(f"processing image {y[0]} | inference time: {elapsed_time:.4f}s")

        if image_count > 0:
            print("Average inference time: {:.4f}s per image".format(total_inference_time / image_count))

    def diffusive_restoration(self, x_cond):
        x_output = self.diffusion.model(x_cond)
        return x_output["pred_x"]

    def _synchronize_device(self):
        if self.diffusion.device.type == "cuda":
            torch.cuda.synchronize()
        elif self.diffusion.device.type == "mps":
            torch.mps.synchronize()
