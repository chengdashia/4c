# Showcase Vision System

## 项目简介

这是一个面向复杂道路天气场景的视觉处理展示系统。项目把图像/视频复原、低照度增强和目标检测封装成可组合的前后端 Demo，适合展示“输入媒体 -> 视觉增强/复原 -> YOLO26 识别 -> 结果对比”的完整流程。

当前代码已经覆盖以下能力：

- 直接目标检测：YOLO26 BDD100K
- 低照度增强：Diffusion Low Light
- 轻量低照度增强：LYT-Net ONNX
- 图像/视频去雨：Attentive GAN Derain
- 图像/视频去雾：C2PNet
- 组合流程：低光增强后检测、轻量增强后检测、去雨后检测、去雾后检测
- 前端自定义编排：可按模块自由组合“识别、去雾、去雨、低光增强、轻量低光增强”

## 仓库结构

```text
.
├── README.md
├── back/                         # Flask 后端服务、接口、模型封装和静态资源
│   ├── app/
│   │   ├── __init__.py            # Flask 应用工厂、Swagger、CORS、路由注册、错误处理
│   │   ├── models/                # ONNX 模型推理封装
│   │   ├── routes/                # REST API 路由
│   │   └── utils/                 # 图片/视频处理、模型加载、路径转换等工具
│   ├── static/                    # 模型文件、上传文件、处理结果文件
│   ├── config.py                  # Flask 配置
│   ├── homepage_media.py          # 首页展示媒体解析
│   ├── requirements.txt
│   └── run.py                     # 后端启动入口
├── front/                         # Vue 3 + Vite 前端
│   ├── public/posters/            # 首页默认海报
│   ├── src/
│   │   ├── components/            # 对比查看组件
│   │   ├── services/api.js        # 后端接口封装
│   │   ├── views/HomeView.vue     # 首页展示
│   │   └── views/DemoView.vue     # 自定义流程编排与演示页
│   ├── package.json
│   └── vite.config.js
├── Diffusion-Low-Light/           # 低照度增强模型源码与训练/评估资源
├── yolo26/                        # YOLO26 相关源码、配置和训练资源
└── test/                          # 单模型测试脚本与 ONNX 样例资源
```

## 系统流程

后端提供单模型接口和组合流程接口。前端的 `/demo` 页面采用更灵活的逐步编排方式：每执行一个模块，就把上一步输出转换成下一步输入。

```text
上传图片或视频
  -> 可选：低照度增强 / 轻量低照度增强 / 去雨 / 去雾
  -> 可选：YOLO26 目标检测
  -> 保存中间结果和最终结果到 back/static
  -> 返回静态资源地址、检测框、耗时、视频元信息和场景摘要
  -> 前端展示每一步结果并支持原始/输出对比
```

对于视频，后端会逐帧处理并导出结果视频；代码中通过共享线程池并行处理帧，线程数可由环境变量 `VIDEO_PROCESS_WORKERS` 控制。

## 前端说明

前端基于 Vue 3、Vue Router 和 Vite。

主要页面：

- `/`：首页。展示复杂天气感知系统、功能覆盖、可搭配流程，以及首页媒体对比。首页会请求 `GET /api/homepage-media`，优先读取 `back/static/demo/` 下的示例视频，缺失时回退到 `front/public/posters/` 中的默认 SVG 海报。
- `/demo`：演示页。支持上传图片或视频，使用快捷模板或拖拽/点击模块来自定义流程，然后按顺序运行。

演示页内置模块：

- `DET`：直接识别，调用 `POST /api/yolo26_bdd100k_file/detect`
- `FOG`：图像去雾，调用 `POST /api/c2pnet_file/dehaze`
- `RAIN`：图像去雨，调用 `POST /api/derain_file/derain`
- `LUX`：低光增强，调用 `POST /api/low_light_file/enhance`
- `FAST`：轻量低光增强，调用 `POST /api/lightweight_low_light_file/enhance`

前端默认后端地址：

```bash
http://127.0.0.1:5001/api
```

可通过环境变量覆盖：

```bash
VITE_API_ORIGIN=http://127.0.0.1:5001
VITE_API_BASE_URL=http://127.0.0.1:5001/api
```

## 后端说明

后端基于 Flask、Flask-CORS、Flask-RESTX、OpenCV、ONNX Runtime、Pillow 和 NumPy。入口为 `back/run.py`，默认监听 `0.0.0.0:5001`，Swagger 文档位于 `/docs`。

`back/app/__init__.py` 会注册这些命名空间：

- `/api/low_light_file`
- `/api/lightweight_low_light_file`
- `/api/c2pnet_file`
- `/api/derain_file`
- `/api/yolo26_bdd100k_file`
- `/api/pipeline_file`
- `/api/lightweight_pipeline_file`
- `/api/dehaze_pipeline_file`
- `/api/derain_pipeline_file`

上传限制由 `back/config.py` 控制，当前最大为 `256MB`。

支持的媒体格式：

- 图片：`png`、`jpg`、`jpeg`
- 视频：`mp4`、`mov`、`avi`、`m4v`、`webm`

## API 列表

### 状态与文档

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查，返回服务状态和模型加载状态 |
| `GET` | `/api/models` | 返回模型文件是否存在、是否已加载、ONNX Runtime providers |
| `GET` | `/api/homepage-media` | 返回首页三阶段展示媒体 |
| `GET` | `/docs` | Swagger 接口文档 |

### 单模型接口

| 方法 | 路径 | 能力 |
| --- | --- | --- |
| `POST` | `/api/low_light_file/enhance` | Diffusion Low Light 低照度增强 |
| `POST` | `/api/lightweight_low_light_file/enhance` | LYT-Net 轻量低照度增强 |
| `POST` | `/api/c2pnet_file/dehaze` | C2PNet 去雾 |
| `POST` | `/api/derain_file/derain` | Attentive GAN 去雨 |
| `POST` | `/api/yolo26_bdd100k_file/detect` | YOLO26 BDD100K 目标检测 |

请求格式均为 `multipart/form-data`：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `file` | 是 | 上传图片或视频 |
| `conf_thres` | 否 | 检测置信度阈值，默认 `0.25`；检测接口和组合检测流程使用 |
| `iou_thres` | 否 | NMS IoU 阈值，默认 `0.45`；检测接口和组合检测流程使用 |

### 组合流程接口

| 方法 | 路径 | 流程 |
| --- | --- | --- |
| `POST` | `/api/pipeline_file/process` | Diffusion 低光增强 -> YOLO26 检测 |
| `POST` | `/api/lightweight_pipeline_file/process` | 轻量低光增强 -> YOLO26 检测 |
| `POST` | `/api/dehaze_pipeline_file/process` | C2PNet 去雾 -> YOLO26 检测 |
| `POST` | `/api/derain_pipeline_file/process` | Attentive GAN 去雨 -> YOLO26 检测 |

组合接口返回内容包括中间结果地址、最终检测结果地址、检测框、目标数量、阈值、各阶段耗时、汇总信息和简单场景分析。

## 返回数据重点字段

接口统一返回形态：

```json
{
  "code": 200,
  "message": "处理成功",
  "data": {}
}
```

常见 `data` 字段：

| 字段 | 说明 |
| --- | --- |
| `media_type` | `image` 或 `video` |
| `upload_image` / `upload_media` | 原始上传文件的静态资源地址 |
| `enhanced_image` / `enhanced_media` | 组合流程的中间增强/复原结果地址 |
| `result_image` / `result_media` | 单模型或最终检测结果地址 |
| `detections` | YOLO26 检测框列表 |
| `count` | 检测目标数量；视频检测接口中为最后一个有检测结果帧的目标数 |
| `thresholds` | `conf_thres` 和 `iou_thres` |
| `timing_ms` | 模型推理、逐帧处理、墙钟耗时等统计 |
| `image_shape` | 图像结果尺寸 |
| `video_meta` | 视频宽高、帧率、帧数、时长、编码器、已处理帧数 |
| `summary` | 目标数量、平均置信度、总时延、视频检测统计等摘要 |
| `scene_analysis` | 基于检测类别生成的简单中文场景分析 |

检测框结构：

```json
{
  "class_id": 2,
  "class_name": "car",
  "score": 0.91,
  "bbox": {
    "x1": 120.5,
    "y1": 80.0,
    "x2": 260.3,
    "y2": 190.8
  }
}
```

## 模型文件

后端会从 `back/static/models/` 下按固定路径加载模型：

| 能力 | 模型文件 |
| --- | --- |
| Diffusion Low Light | `back/static/models/low_light/diffusion_low_light_1x3x384x640.onnx` |
| LYT-Net 轻量低光 | `back/static/models/low_light/lyt_net_lolv2_real_640x360.onnx` |
| C2PNet 去雾 | `back/static/models/c2p/c2pnet_outdoor_360x640.onnx` |
| Attentive GAN 去雨 | `back/static/models/derain/attentive_gan_derainnet_360x640.onnx` |
| YOLO26 BDD100K | `back/static/models/yolo26_bdd100k/yolo26s.onnx` |

`GET /api/models` 可检查模型文件是否存在、是否已经被懒加载，以及当前 ONNX Runtime 使用的执行 provider。

ONNX Runtime provider 选择逻辑：

- 默认按 `CUDAExecutionProvider`、`DmlExecutionProvider`、`CPUExecutionProvider` 优先级选择可用 provider
- 如需启用 CoreML，可设置 `ENABLE_COREML=1`
- 没有 GPU provider 时会回退到 `CPUExecutionProvider`

## 运行方式

### 1. 启动后端

```bash
cd /Users/dong/Documents/4c/back
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Apple Silicon 如果虚拟环境或 ONNX Runtime provider 对架构敏感，可使用：

```bash
arch -arm64 .venv/bin/python run.py
```

后端地址：

- API：`http://127.0.0.1:5001/api`
- Swagger：`http://127.0.0.1:5001/docs`
- 静态资源：`http://127.0.0.1:5001/static/...`

### 2. 启动前端

```bash
cd /Users/dong/Documents/4c/front
npm install
npm run dev
```

前端地址：

- `http://127.0.0.1:5173`

### 3. 构建前端

```bash
cd /Users/dong/Documents/4c/front
npm run build
npm run preview
```

## 示例调用

直接检测图片：

```bash
curl -X POST http://127.0.0.1:5001/api/yolo26_bdd100k_file/detect \
  -F "file=@/path/to/image.jpg" \
  -F "conf_thres=0.25" \
  -F "iou_thres=0.45"
```

低光增强后检测：

```bash
curl -X POST http://127.0.0.1:5001/api/pipeline_file/process \
  -F "file=@/path/to/night-road.jpg" \
  -F "conf_thres=0.25" \
  -F "iou_thres=0.45"
```

去雨处理：

```bash
curl -X POST http://127.0.0.1:5001/api/derain_file/derain \
  -F "file=@/path/to/rain.mp4"
```

## 生成文件与日志

上传文件和结果文件会写入 `back/static/images/` 下的不同子目录，例如：

- `back/static/images/low_light/uploads`
- `back/static/images/low_light/results`
- `back/static/images/lightweight_low_light/uploads`
- `back/static/images/lightweight_low_light/results`
- `back/static/images/c2pnet/uploads`
- `back/static/images/c2pnet/results`
- `back/static/images/derain/uploads`
- `back/static/images/derain/results`
- `back/static/images/yolo26_bdd100k/uploads`
- `back/static/images/yolo26_bdd100k/results`
- `back/static/images/*_pipeline/...`

首页固定示例视频单独放在：

- `back/static/demo/raw.mp4`
- `back/static/demo/enhanced.mp4`
- `back/static/demo/detected.mp4`

后端日志写入：

```text
back/logs/showcase-backend.log
```

## 开发注意事项

- 后端模型采用懒加载，首次调用某个能力时会加载对应 ONNX 模型。
- 视频处理会在输出目录中生成 `.mp4` 结果，编码器优先尝试 `avc1`、`H264`、`mp4v`，Windows 上优先 `mp4v`。
- 前端自定义编排逐步调用单模型接口；后端也保留了固定组合流程接口，便于直接联调和性能统计。
- `front/src/views/ApiView.vue` 是早期接口说明页面，目前未注册到路由，实际演示入口以 `/demo` 为准。
- `Diffusion-Low-Light/` 和 `yolo26/` 主要保留源码、训练/评估资源和模型溯源；当前 Web Demo 运行时主要依赖 `back/static/models/` 中导出的模型文件。
