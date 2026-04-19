# 复杂天气自动驾驶感知展示系统

## 项目简介

本项目是一个面向复杂道路天气场景的视觉处理展示系统，核心目标是把图片或视频输入统一接入后端模型推理，再在前端完成可视化对比与流程编排。系统当前支持低照度增强、轻量低照度增强、图像去雨、图像去雾和 YOLO26 目标检测，既可以单独调用某一个模型，也可以组合成“增强/复原 -> 检测”的完整链路。

项目由三部分组成：

- `front/`：Vue 3 + Vite 前端展示系统
- `back/`：FastAPI 后端服务、模型加载、媒体处理和接口层
- `Diffusion-Low-Light/`、`LYT-Net-main/`、`yolo26/`：模型源码、训练/评估资源和模型来源代码

## 已实现能力

- 直接检测：上传图片或视频后使用 YOLO26 BDD100K 模型输出目标框、类别、置信度和检测结果媒体。
- 低照度增强：使用 Diffusion Low Light ONNX 模型增强夜间、欠曝光场景。
- 轻量低照度增强：使用 LYT-Net ONNX 模型进行更轻量的低光增强。
- 图像/视频去雨：使用 Attentive GAN Derain 模型减弱雨线干扰。
- 图像/视频去雾：使用 C2PNet 模型恢复雾天道路可见度。
- 固定组合流程：低光增强后检测、轻量低光增强后检测、去雨后检测、去雾后检测。
- 自定义流程编排：前端 `/demo` 页面支持通过快捷模板、点击和拖拽自由组合处理模块。
- 视频逐帧处理：后端支持视频输入，逐帧执行增强/复原/检测，并导出结果视频。
- 首页示例视频：固定读取 `back/static/demo/` 下的三段展示视频，避免首页依赖临时运行结果。

## 仓库结构

```text
.
├── README.md
├── README.txt
├── back/
│   ├── app/
│   │   ├── __init__.py                  # FastAPI 应用工厂、路由注册、异常处理、静态资源挂载
│   │   ├── http.py                      # 统一响应、上传文件校验和 UploadFile 保存适配
│   │   ├── models/                      # ONNX 模型封装
│   │   ├── routes/                      # FastAPI 路由
│   │   └── utils/                       # 图片、视频、路径和模型加载工具
│   ├── static/
│   │   ├── demo/                        # 首页固定示例视频
│   │   ├── images/                      # 上传文件和推理结果
│   │   └── models/                      # 后端实际加载的 ONNX 模型文件
│   ├── config.py
│   ├── homepage_media.py
│   ├── requirements.txt
│   └── run.py
├── front/
│   ├── public/posters/                  # 示例视频缺失时的默认海报
│   ├── src/
│   │   ├── components/ComparisonViewer.vue
│   │   ├── services/api.js              # 前端接口封装
│   │   ├── views/HomeView.vue
│   │   └── views/DemoView.vue
│   ├── package.json
│   └── vite.config.js
├── Diffusion-Low-Light/                 # Diffusion 低照度增强相关源码
├── LYT-Net-main/                        # LYT-Net 轻量低光增强相关源码
├── yolo26/                              # YOLO26 相关源码、配置和资源
└── test/                                # 单模型测试脚本与接口测试
```

## 系统流程

```text
用户上传图片或视频
  -> 前端根据用户选择生成处理流程
  -> FastAPI 接收 multipart/form-data 文件
  -> 校验扩展名、MIME 类型和上传大小
  -> 根据接口调用对应 ONNX 模型
  -> 图片直接推理，视频逐帧推理并导出 MP4
  -> 保存上传文件、中间结果和最终结果到 back/static/images
  -> 返回媒体地址、检测框、耗时、视频信息和场景分析
  -> Vue 前端展示每一步结果
```

## 前端说明

前端技术栈：

- Vue 3
- Vue Router
- Vite

页面：

- `/`：首页，展示系统介绍、功能覆盖、可搭配流程和三阶段媒体对比。
- `/demo`：自定义流程编排页，支持上传图片/视频、选择快捷流程、拖拽模块、运行并查看每一步结果。

前端默认请求地址：

```bash
http://127.0.0.1:5001/api
```

可通过环境变量覆盖：

```bash
VITE_API_ORIGIN=http://127.0.0.1:5001
VITE_API_BASE_URL=http://127.0.0.1:5001/api
```

前端模块与接口映射：

| 前端模块 | 说明 | 后端接口 |
| --- | --- | --- |
| `DET` | 目标检测 | `POST /api/detections/yolo26` |
| `FOG` | 图像/视频去雾 | `POST /api/enhancements/dehaze` |
| `RAIN` | 图像/视频去雨 | `POST /api/enhancements/derain` |
| `LUX` | Diffusion 低光增强 | `POST /api/enhancements/low-light` |
| `FAST` | LYT-Net 轻量低光增强 | `POST /api/enhancements/low-light/lightweight` |

## 后端说明

后端技术栈：

- FastAPI
- Uvicorn
- OpenCV
- ONNX Runtime / ONNX Runtime DirectML
- Pillow
- NumPy
- Ultralytics
- imageio-ffmpeg

后端入口为 `back/run.py`，默认监听 `0.0.0.0:5001`。FastAPI 会自动提供接口文档：

- Swagger UI：`http://127.0.0.1:5001/docs`
- OpenAPI JSON：`http://127.0.0.1:5001/openapi.json`

上传限制由 `back/config.py` 中的 `MAX_CONTENT_LENGTH` 控制，当前为 `256MB`。

支持的媒体格式：

- 图片：`png`、`jpg`、`jpeg`
- 视频：`mp4`、`mov`、`avi`、`m4v`、`webm`

## API 列表

### 状态接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查，包含模型状态和加速状态 |
| `GET` | `/api/models` | 返回模型文件是否存在、是否已加载、模型路径和 ONNX Runtime providers |
| `GET` | `/api/homepage-media` | 返回首页三阶段展示媒体 |
| `GET` | `/` | 后端根路径状态信息 |

### 单模型接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/detections/yolo26` | YOLO26 BDD100K 目标检测 |
| `POST` | `/api/enhancements/low-light` | Diffusion Low Light 低照度增强 |
| `POST` | `/api/enhancements/low-light/lightweight` | LYT-Net 轻量低照度增强 |
| `POST` | `/api/enhancements/dehaze` | C2PNet 去雾 |
| `POST` | `/api/enhancements/derain` | Attentive GAN 去雨 |

### 组合流程接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/pipelines/low-light-detect` | Diffusion 低光增强 -> YOLO26 检测 |
| `POST` | `/api/pipelines/lightweight-low-light-detect` | LYT-Net 轻量低光增强 -> YOLO26 检测 |
| `POST` | `/api/pipelines/dehaze-detect` | C2PNet 去雾 -> YOLO26 检测 |
| `POST` | `/api/pipelines/derain-detect` | Attentive GAN 去雨 -> YOLO26 检测 |

### 请求字段

所有推理接口都使用 `multipart/form-data`：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `file` | 是 | 上传图片或视频 |
| `conf_thres` | 否 | 检测置信度阈值，默认 `0.25`，检测和组合流程使用 |
| `iou_thres` | 否 | NMS IoU 阈值，默认 `0.45`，检测和组合流程使用 |

## 返回数据说明

后端成功响应统一包含：

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
| `enhanced_image` / `enhanced_media` | 组合流程中的增强或复原结果地址 |
| `result_image` / `result_media` | 单模型结果或最终检测结果地址 |
| `detections` | YOLO26 检测框列表 |
| `count` | 检测目标数量 |
| `thresholds` | 检测阈值 |
| `timing_ms` | 模型推理耗时、视频逐帧耗时和墙钟耗时 |
| `image_shape` | 输出图像尺寸 |
| `video_meta` | 视频宽高、FPS、总帧数、时长、编码器和已处理帧数 |
| `summary` | 目标数、平均置信度、总时延等摘要 |
| `scene_analysis` | 基于检测类别生成的简单中文场景分析 |

检测框示例：

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

后端实际从 `back/static/models/` 加载模型文件：

| 能力 | 模型文件 |
| --- | --- |
| Diffusion Low Light | `back/static/models/low_light/diffusion_low_light_1x3x384x640.onnx` |
| LYT-Net 轻量低光 | `back/static/models/low_light/lyt_net_lolv2_real_640x360.onnx` |
| C2PNet 去雾 | `back/static/models/c2p/c2pnet_outdoor_360x640.onnx` |
| Attentive GAN 去雨 | `back/static/models/derain/attentive_gan_derainnet_360x640.onnx` |
| YOLO26 BDD100K | `back/static/models/yolo26_bdd100k/my_yolo26.onnx` |

模型文件体积较大，仓库中可不直接携带完整 ONNX 权重。ONNX 模型文件放在百度网盘：

```text
链接：https://pan.baidu.com/s/
提取码：
```

下载后请按下面目录放置，文件名需要与表格一致，否则后端会在首次推理时提示“模型文件不存在”：

```text
back/static/models/
├── low_light/
│   ├── diffusion_low_light_1x3x384x640.onnx
│   └── lyt_net_lolv2_real_640x360.onnx
├── c2p/
│   └── c2pnet_outdoor_360x640.onnx
├── derain/
│   └── attentive_gan_derainnet_360x640.onnx
└── yolo26_bdd100k/
    └── my_yolo26.onnx
```

如果下载包中的文件名不同，请改名为上面的目标文件名，或同步修改 `back/app/utils/model_loader.py` 中对应的加载路径。

模型采用懒加载机制：首次调用某个能力时才会加载对应模型。可通过 `GET /api/models` 查看 `ready` 和 `loaded` 状态。

## 加速与视频处理

ONNX Runtime provider 选择逻辑：

- macOS 默认优先尝试 `CoreMLExecutionProvider`，可设置 `ENABLE_COREML=0` 禁用。
- Windows 优先尝试 `CUDAExecutionProvider`、`DmlExecutionProvider`、`CPUExecutionProvider`。
- 其他环境优先尝试 `CUDAExecutionProvider`，否则回退到 `CPUExecutionProvider`。

`GET /api/health` 会返回：

- `acceleration.onnxruntime_providers`
- `acceleration.torch_device`

视频处理使用共享线程池逐帧处理。可通过环境变量控制线程数：

```bash
VIDEO_PROCESS_WORKERS=4
```

无 GPU 加速时，每个 ONNX Runtime session 会限制为单线程，避免视频并行处理时 CPU 线程过度竞争。

## 首页示例媒体

首页不再从历史推理结果目录中自动取最新文件，而是固定读取：

- `back/static/demo/raw.mp4`
- `back/static/demo/enhanced.mp4`
- `back/static/demo/detected.mp4`

如果这些文件不存在，后端会让前端回退到默认海报：

- `front/public/posters/raw-scene.svg`
- `front/public/posters/enhanced-scene.svg`
- `front/public/posters/detected-scene.svg`

## 运行方式

### 1. 启动后端

```bash
cd /Users/dong/Documents/4c/back
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

后端地址：

- API：`http://127.0.0.1:5001/api`
- 文档：`http://127.0.0.1:5001/docs`
- 静态资源：`http://127.0.0.1:5001/static/...`

### 2. 启动前端

```bash
cd /Users/dong/Documents/4c/front
npm install
npm run dev
```

前端地址：

```text
http://127.0.0.1:5173
```

### 3. 构建前端

```bash
cd /Users/dong/Documents/4c/front
npm run build
npm run preview
```

## 示例调用

直接检测：

```bash
curl -X POST http://127.0.0.1:5001/api/detections/yolo26 \
  -F "file=@/path/to/image.jpg" \
  -F "conf_thres=0.25" \
  -F "iou_thres=0.45"
```

低光增强：

```bash
curl -X POST http://127.0.0.1:5001/api/enhancements/low-light \
  -F "file=@/path/to/night-road.jpg"
```

低光增强后检测：

```bash
curl -X POST http://127.0.0.1:5001/api/pipelines/low-light-detect \
  -F "file=@/path/to/night-road.jpg" \
  -F "conf_thres=0.25" \
  -F "iou_thres=0.45"
```

去雨后检测：

```bash
curl -X POST http://127.0.0.1:5001/api/pipelines/derain-detect \
  -F "file=@/path/to/rain.mp4"
```

## 输出目录

接口处理过程中会写入以下目录：

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

后端日志写入：

```text
back/logs/showcase-backend.log
```

## 开发注意事项

- 根目录 README 面向整个项目，`back/README.md` 是后端简版说明，`front/README.md` 是前端说明。
- `front/src/views/ApiView.vue` 是早期接口说明页面，当前未注册到路由，实际演示入口以 `/demo` 为准。
- `Diffusion-Low-Light/`、`LYT-Net-main/` 和 `yolo26/` 主要用于模型来源、训练、评估和后续替换；Web Demo 运行时主要依赖 `back/static/models/` 下的 ONNX 文件。
- 当前工作区可能存在生成的上传结果、日志、虚拟环境、前端依赖和系统文件，这些不影响主流程代码。
