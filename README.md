# Showcase System

## 项目简介

这是一个面向低照度交通场景展示的视觉处理系统，核心目标是把一张夜间或弱光图片，依次经过：

1. 低照度增强
2. 目标检测
3. 前端可视化展示

最终输出一套可以直接演示的结果，包括原图、增强图、检测图、检测框信息、耗时统计和简单场景分析。

整个仓库不是单一前端或单一后端，而是一个完整的 Demo 系统，包含：

- `front`：Vue 3 + Vite 前端展示与交互
- `back`：Flask 后端接口层与模型调度层
- `Diffusion-Low-Light`：低照度增强相关模型与代码资源
- `yolo26`：YOLO26 检测模型代码与训练/推理资源

## 适用场景

本项目适合用于以下几类工作：

- 展示“低照度增强 + 目标检测”串联流程
- 作为课程作业、毕业设计或项目答辩的可运行 Demo
- 快速验证弱光图像增强对检测结果的帮助
- 为后续继续接入视频流、更多模型或业务逻辑提供基础框架

## 项目整体流程

系统的主流程如下：

```text
用户上传图片
  -> Flask 接收文件并校验格式
  -> 调用低照度增强 ONNX 模型
  -> 保存增强结果
  -> 调用 YOLO26 BDD100K 检测模型
  -> 保存检测结果
  -> 返回图片地址、检测结果、耗时和摘要信息
  -> Vue 前端展示处理结果和对比效果
```

其中，后端提供了单模型接口，也提供了完整串联接口，前端当前主要围绕串联流程进行演示。

## 仓库结构说明

### 根目录

- `README.md`：项目总说明
- `Diffusion-Low-Light/`：低照度增强模型与相关实现代码
- `yolo26/`：YOLO26 目标检测代码、配置、测试与训练资源
- `back/`：后端服务
- `front/`：前端页面

### `back` 后端目录

`back` 是整个系统的接口层和编排层，负责接收上传文件、调用模型、组织返回结果。

关键内容如下：

- `back/run.py`：后端启动入口，默认监听 `5001` 端口
- `back/config.py`：Flask 基础配置，例如上传大小限制、Swagger 行为、调试模式
- `back/homepage_media.py`：首页展示媒体配置，支持优先读取本地静态资源，缺失时回退到默认海报
- `back/requirements.txt`：后端依赖

#### `back/app`

- `back/app/__init__.py`
  负责创建 Flask 应用、初始化 CORS、Swagger 文档、日志系统、注册接口命名空间，以及统一错误处理。

- `back/app/routes/`
  定义具体接口：
  - `low_light.py`：低照度增强接口
  - `yolo26_bdd100k.py`：YOLO26 目标检测接口
  - `pipeline.py`：增强后再检测的串联接口

- `back/app/models/`
  对底层模型做了一层项目内封装：
  - `low_light/diffusion_low_light.py`：低照度增强模型封装
  - `yolo26_bdd100k/yolo26_onnx.py`：YOLO26 ONNX 推理封装

- `back/app/utils/`
  放置辅助工具：
  - `model_loader.py`：模型懒加载、模型状态检查、统一推理入口
  - `image_processing.py`：图片读写、格式校验、检测结果转换等
  - `image_codec.py`：Base64 与图像之间的编码解码
  - `path_utils.py`：本地路径转为前端可访问的 URL 路径

#### `back/static`

这里保存静态资源与模型文件，当前关键模型包括：

- `back/static/models/low_light/diffusion_low_light_1x3x384x640.onnx`
- `back/static/models/yolo26_bdd100k/yolo26s.onnx`
- `back/static/models/yolo26_bdd100k/yolo26s.pt`
- `back/static/models/yolo26_bdd100k/yolo26n.pt`

接口处理过程中生成的上传图、增强图、检测图，也会保存在 `back/static` 下对应目录，便于前端直接访问。

### `front` 前端目录

`front` 是面向展示的 Web 界面，基于 Vue 3 + Vite 实现。

关键内容如下：

- `front/src/router/index.js`：路由配置
- `front/src/services/api.js`：前端对后端接口的统一封装
- `front/src/views/HomeView.vue`：首页，展示三阶段流程海报或首页媒体资源
- `front/src/views/DemoView.vue`：交互演示页，支持上传图片并触发完整处理流程
- `front/src/components/ComparisonViewer.vue`：对比滑块组件，用于原图/增强图、增强图/检测图对比
- `front/public/posters/`：首页默认海报资源

当前前端主要包含两个页面：

- `/`：展示项目流程概览
- `/demo`：上传图片并查看处理结果

### `Diffusion-Low-Light`

这一部分保存低照度增强相关代码和模型资源，是后端低照度增强能力的来源之一。当前后端实际运行时使用的是已经导出的 ONNX 模型文件，但仓库中保留了原始模型代码，便于：

- 追溯模型来源
- 后续重新导出模型
- 替换或改进增强算法

### `yolo26`

这一部分保存 YOLO26 相关代码、配置、数据集说明、测试和训练资源。当前后端运行时主要依赖其中导出的权重/模型文件和项目内封装，但保留完整目录有两个作用：

- 可继续做训练、验证或模型替换
- 可追踪检测模型的配置、类别和推理逻辑

## 当前已实现能力

### 1. 低照度增强

接口：

- `POST /api/low_light_file/enhance`

能力说明：

- 接收一张图片文件
- 校验扩展名和 MIME 类型
- 调用低照度增强模型进行推理
- 保存增强结果图片
- 返回原图地址、增强图地址、耗时和图像尺寸

### 2. 目标检测

接口：

- `POST /api/yolo26_bdd100k_file/detect`

能力说明：

- 接收一张图片文件
- 支持 `conf_thres` 和 `iou_thres` 阈值参数
- 调用 YOLO26 BDD100K 检测模型
- 保存带框结果图
- 返回检测列表、目标数量、阈值和耗时信息

### 3. 串联处理 Pipeline

接口：

- `POST /api/pipeline_file/process`

这是当前项目最核心的接口，会按顺序完成：

1. 上传原图
2. 低照度增强
3. 检测增强后的图片
4. 汇总返回整体结果

返回数据除图片地址外，还包含：

- `detections`：检测目标列表
- `count`：目标数量
- `timing_ms`：增强、检测、总耗时
- `summary`：目标数、平均置信度、整体时延
- `scene_analysis`：基于检测结果生成的简单文字分析

### 4. 状态与辅助接口

- `GET /api/health`：健康检查，返回服务状态和模型加载状态
- `GET /api/models`：返回模型文件是否就绪、是否已加载
- `GET /api/homepage-media`：返回首页展示媒体配置
- `GET /docs`：Swagger 接口文档

## 主要技术栈

### 前端

- Vue 3
- Vue Router
- Vite

### 后端

- Flask
- Flask-Cors
- Flask-RESTX
- OpenCV
- ONNX Runtime
- Pillow
- NumPy

### 模型与算法

- Diffusion Low Light 低照度增强
- YOLO26 + BDD100K 目标检测

## 运行前提

在启动项目前，需要确认以下内容：

- 本机已安装 Python 3 环境
- 本机已安装 Node.js 和 npm
- 后端虚拟环境已准备完成
- `back/static/models/` 下的模型文件存在
- 如为 Apple Silicon 环境，后端虚拟环境可能需要使用 `arm64` 启动

后端默认限制上传大小为 `16MB`。

## 启动方式

### 1. 启动后端

当前本机环境下，后端虚拟环境需要使用 `arm64` 启动：

```bash
cd /Users/dong/Documents/code/4c/system/back
arch -arm64 .venv/bin/python run.py
```

后端默认地址：

- `http://127.0.0.1:5001`
- Swagger 文档：`http://127.0.0.1:5001/docs`

### 2. 启动前端

```bash
cd /Users/dong/Documents/code/4c/system/front
npm run dev
```

前端默认地址：

- `http://127.0.0.1:5173`

## 前后端联调说明

前端默认请求：

```bash
http://127.0.0.1:5001/api
```

如需修改后端地址，可在前端环境变量中设置：

```bash
VITE_API_ORIGIN=http://127.0.0.1:5001
```

前端内部会基于这个地址自动拼接：

```bash
${VITE_API_ORIGIN}/api
```

## 返回结果说明

以串联接口为例，前端最关心的返回内容包括：

- `upload_image`：原图静态资源地址
- `enhanced_image`：增强图地址
- `result_image`：检测结果图地址
- `detections`：检测框明细
- `count`：检测到的目标数量
- `timing_ms`：各阶段耗时统计
- `scene_analysis`：结果摘要说明

这使得前端不仅能显示图片，还可以展示处理性能和语义层面的结果摘要。

## 项目特点

- 不是单一模型演示，而是完整的端到端流程
- 同时支持独立增强、独立检测、增强后检测三种能力
- 结果图会落盘保存，方便展示与复用
- 接口文档可直接通过 Swagger 查看
- 前端已经具备基础演示页面和对比展示组件
- 后端已经包含模型状态检查、日志记录和统一异常处理

