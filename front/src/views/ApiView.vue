<template>
  <section class="content-grid">
    <div class="card">
      <p class="section-tag">Backend Contract</p>
      <h3>FastAPI 接口联调说明</h3>
      <p class="hero-text">
        后端通过 FastAPI 提供模型推理接口。保持后端服务运行后，前端会把上传媒体发送到对应流程，
        并使用返回的结果媒体、检测框和场景分析更新演示页面。
      </p>

      <div class="api-state">
        <button class="ghost-button" @click="checkHealth">检查接口状态</button>
        <span>{{ healthMessage }}</span>
      </div>
    </div>

    <div class="card">
      <p class="section-tag">API Endpoints</p>
      <h3>建议接口</h3>
      <div class="endpoint-list">
        <article class="endpoint-item">
          <strong>GET /api/health</strong>
          <p>用于前端判断服务是否启动、模型是否加载成功。</p>
        </article>
        <article class="endpoint-item">
          <strong>POST /api/pipelines/low-light-detect</strong>
          <p>接收上传图片或视频、置信度阈值和 IoU 阈值，返回增强结果、检测结果、统计信息和场景结论。</p>
        </article>
        <article class="endpoint-item">
          <strong>GET /api/models</strong>
          <p>返回当前可用模型列表，如 improved-yolo、faster-rcnn、night-enhanced-yolo。</p>
        </article>
      </div>
    </div>
  </section>

  <section class="content-grid">
    <div class="card">
      <p class="section-tag">Infer Response</p>
      <h3>推荐返回结构</h3>
      <pre class="code-block">{{ sampleResponse }}</pre>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { fetchHealth } from '../services/api'

const healthMessage = ref('尚未检测')

const sampleResponse = `{
  "detections": [
    {
      "id": 1,
      "label": "vehicle",
      "score": 0.94,
      "bbox": [120, 280, 390, 430],
      "risk": "medium"
    }
  ],
  "summary": {
    "weather": "fog",
    "algorithm": "improved-yolo",
    "target_count": 3,
    "avg_confidence": 0.88,
    "latency_ms": 126,
    "risk_level": "high"
  },
  "risk_distribution": [
    { "label": "高风险", "value": 2, "accent": "#ff6b6b" }
  ],
  "scene_analysis": [
    "前方车辆密集，建议降低速度并增大制动余量。"
  ]
}`

async function checkHealth() {
  try {
    const health = await fetchHealth()
    healthMessage.value = `${health.status} / ${health.message || 'service ready'}`
  } catch (error) {
    healthMessage.value = error.message
  }
}
</script>
