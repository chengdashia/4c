import os
import torch
import torch.utils.data
import PIL
from PIL import Image
import re
from datasets.data_augment import PairCompose, PairRandomCrop, PairToTensor


def _resolve_data_root(config):
    configured_dir = config.data.data_dir
    candidates = []

    if os.path.isabs(configured_dir):
        candidates.append(configured_dir)
    else:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        candidates.append(os.path.abspath(os.path.join(project_root, configured_dir)))

    env_dir = os.environ.get("DIFFUSION_LL_DATA_DIR")
    if env_dir:
        candidates.insert(0, os.path.abspath(env_dir))

    # Common local layouts for this repository.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidates.extend([
        os.path.join(project_root, "data"),
        os.path.join(project_root, "data", "LL_dataset"),
    ])

    seen = set()
    unique_candidates = []
    for candidate in candidates:
        if candidate not in seen:
            unique_candidates.append(candidate)
            seen.add(candidate)

    for candidate in unique_candidates:
        train_dir = os.path.join(candidate, config.data.train_dataset, "train")
        val_dir = os.path.join(candidate, config.data.val_dataset, "val")
        if os.path.isdir(train_dir) and os.path.isdir(val_dir):
            return candidate

    return unique_candidates[0]


def _resolve_split_dir(config, split):
    data_root = _resolve_data_root(config)
    dataset_name = config.data.train_dataset if split == "train" else config.data.val_dataset
    standard_dir = os.path.join(data_root, dataset_name, split)
    if os.path.isdir(standard_dir):
        return standard_dir

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    lolv1_default = os.path.join(project_root, "datasets", "LOL-v1", "our485" if split == "train" else "eval15")
    if os.path.isdir(lolv1_default):
        return lolv1_default

    return standard_dir


class LLdataset:
    def __init__(self, config):
        self.config = config

    def get_loaders(self, parse_patches=True):
        train_dir = _resolve_split_dir(self.config, "train")
        val_dir = _resolve_split_dir(self.config, "val")

        train_dataset = AllWeatherDataset(train_dir,
                                          patch_size=self.config.data.patch_size,
                                          filelist='{}_train.txt'.format(self.config.data.train_dataset))
        val_dataset = AllWeatherDataset(val_dir,
                                        patch_size=self.config.data.patch_size,
                                        filelist='{}_val.txt'.format(self.config.data.val_dataset), train=False)

        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=self.config.training.batch_size,
                                                   shuffle=True, num_workers=self.config.data.num_workers,
                                                   pin_memory=True)
        val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=1, shuffle=False,
                                                 num_workers=self.config.data.num_workers,
                                                 pin_memory=True)

        return train_loader, val_loader


class AllWeatherDataset(torch.utils.data.Dataset):
    def __init__(self, dir, patch_size, filelist=None, train=True):
        super().__init__()

        self.dir = dir
        self.train = train
        self.file_list = filelist
        self.train_list = os.path.join(dir, self.file_list)
        if os.path.exists(self.train_list):
            with open(self.train_list) as f:
                contents = f.readlines()
                input_names = [i.strip() for i in contents]
                gt_names = [i.strip().replace('low', 'high') for i in input_names]
        else:
            low_dir = os.path.join(dir, "low")
            high_dir = os.path.join(dir, "high")
            if not (os.path.isdir(low_dir) and os.path.isdir(high_dir)):
                split_name = "train" if train else "val"
                raise FileNotFoundError(
                    "Dataset index file not found: {}. Also could not find paired 'low/' and 'high/' "
                    "folders under {}. Expected {} dataset under a path like 'data/{}/{}', or the "
                    "original LOL-v1 layout under 'datasets/LOL-v1/{}'. You can also set "
                    "DIFFUSION_LL_DATA_DIR=/absolute/path/to/dataset_root.".format(
                        self.train_list,
                        dir,
                        split_name,
                        os.path.basename(os.path.dirname(dir)),
                        split_name,
                        "our485" if train else "eval15",
                    )
                )
            input_names = [os.path.join("low", name) for name in sorted(os.listdir(low_dir))
                           if os.path.isfile(os.path.join(low_dir, name))]
            gt_names = []
            for input_name in input_names:
                gt_name = input_name.replace("low" + os.sep, "high" + os.sep)
                gt_path = os.path.join(dir, gt_name)
                gt_names.append(gt_name if os.path.isfile(gt_path) else None)

        self.input_names = input_names
        self.gt_names = gt_names
        self.patch_size = patch_size
        if self.train:
            self.transforms = PairCompose([
                PairRandomCrop(self.patch_size),
                PairToTensor()
            ])
        else:
            self.transforms = PairCompose([
                PairToTensor()
            ])

    def get_images(self, index):
        input_name = self.input_names[index].replace('\n', '')
        gt_name = self.gt_names[index]
        if isinstance(gt_name, str):
            gt_name = gt_name.replace('\n', '')
        img_id = re.split('/', input_name)[-1][:-4]
        input_img = Image.open(os.path.join(self.dir, input_name)) if self.dir else PIL.Image.open(input_name)
        if gt_name is None:
            # Evaluation can run without paired GT images; use the input image as a placeholder
            # so downstream code still receives the expected tensor shape.
            gt_img = input_img.copy()
        else:
            gt_img = Image.open(os.path.join(self.dir, gt_name)) if self.dir else PIL.Image.open(gt_name)

        input_img, gt_img = self.transforms(input_img, gt_img)

        return torch.cat([input_img, gt_img], dim=0), img_id

    def __getitem__(self, index):
        res = self.get_images(index)
        return res

    def __len__(self):
        return len(self.input_names)
