# Backend Placeholder

这里先放 Flask 后端占位代码，等模型训练完成后再接入真实推理逻辑。

当前预留接口：

- `GET /api/health`
- `GET /api/models`
- `POST /api/infer`

后续推荐接入方式：

1. 加载你训练好的 `YOLO` 或 `Faster R-CNN` 权重
2. 接收前端上传的图片或图片路径
3. 返回检测框、类别、置信度、风险等级和场景分析结果
