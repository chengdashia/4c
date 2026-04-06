# Frontend

这是复杂天气自动驾驶检测展示系统的前端，基于 `Vue 3 + Vite + Vue Router`。

## 已实现内容

- 系统总览首页
- 检测演示页
- Flask 接口联调说明页
- 模拟推理数据和真实 API 切换结构
- 检测框叠加展示、场景分析、风险分布可视化

## 启动方式

```bash
cd /Users/dong/Documents/code/4c/showcase-system/front
npm install
npm run dev
```

## 环境变量

复制 `.env.example` 为 `.env` 后可修改：

- `VITE_API_BASE_URL`：后端 Flask 地址
- `VITE_USE_MOCK`：`true` 时使用前端模拟数据，`false` 时请求真实接口
