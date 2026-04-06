<template>
  <section class="content-grid">
    <div class="card">
      <p class="section-tag">Backend Contract</p>
      <h3>Flask 接口联调说明</h3>
      <p class="hero-text">
        当前前端默认使用模拟数据工作。等你训练好模型后，只需要在 Flask 中实现下面这些接口，
        再把 `VITE_USE_MOCK` 设为 `false`，前端就能切换到真实推理模式。
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
          <strong>POST /api/infer</strong>
          <p>接收图像路径或上传文件、天气类型、算法名称、置信度阈值，返回检测框、统计信息和场景结论。</p>
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
