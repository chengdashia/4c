import argparse
import torch
import shutil
import os
import torchvision.utils as tvu


def save_image(img, file_directory):
    if not os.path.exists(os.path.dirname(file_directory)):
        os.makedirs(os.path.dirname(file_directory))
    tvu.save_image(img, file_directory)


def save_checkpoint(state, filename):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    torch.save(state, filename + '.pth.tar')


def load_checkpoint(path, device):
    load_kwargs = {}
    if device is not None:
        load_kwargs["map_location"] = device

    try:
        # PyTorch 2.6 changed torch.load default to weights_only=True, which
        # breaks older checkpoints that store argparse.Namespace and optimizer state.
        return torch.load(path, weights_only=False, **load_kwargs)
    except TypeError:
        # Older PyTorch versions do not support the weights_only argument.
        return torch.load(path, **load_kwargs)
