# Showcase System

## 项目结构

- `front`：Vue 3 + Vite 前端
- `back`：Flask 后端，提供低照度增强、目标检测和串联处理接口

## 已完成能力

- `POST /api/low_light_file/enhance`：图片增强
- `POST /api/yolo26_bdd100k_file/detect`：目标检测
- `POST /api/pipeline_file/process`：上传一张图片后，先增强，再检测
- `GET /api/health`：后端健康检查
- `GET /api/models`：模型状态检查

## 启动方式

### 1. 启动后端

当前本机环境下，后端虚拟环境需要使用 `arm64` 启动：

```bash
cd /Users/dong/Documents/code/4c/showcase-system/back
arch -arm64 .venv/bin/python run.py
```

后端默认地址：

- `http://127.0.0.1:5001`
- Swagger 文档：`http://127.0.0.1:5001/docs`

### 2. 启动前端

```bash
cd /Users/dong/Documents/code/4c/showcase-system/front
npm run dev
```

前端默认地址：

- `http://127.0.0.1:5173`

前端会默认请求：

- `http://127.0.0.1:5001/api`

如需修改后端地址，可在前端环境变量中设置：

```bash
VITE_API_ORIGIN=http://127.0.0.1:5001
```
