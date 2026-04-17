# Backend

这里是复杂天气自动驾驶检测展示系统的 FastAPI 后端，负责接收前端上传的图片或视频，调用本地模型推理，并返回结果媒体路径、检测框、耗时统计和场景分析。

当前接口：

- `GET /api/health`
- `GET /api/models`
- `GET /api/homepage-media`
- `POST /api/detections/yolo26`
- `POST /api/enhancements/low-light`
- `POST /api/enhancements/low-light/lightweight`
- `POST /api/enhancements/dehaze`
- `POST /api/enhancements/derain`
- `POST /api/pipelines/low-light-detect`
- `POST /api/pipelines/lightweight-low-light-detect`
- `POST /api/pipelines/dehaze-detect`
- `POST /api/pipelines/derain-detect`

本地启动：

```bash
cd back
pip install -r requirements.txt
python run.py
```
