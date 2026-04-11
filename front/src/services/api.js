const API_ORIGIN = import.meta.env.VITE_API_ORIGIN || 'http://127.0.0.1:5001'
const API_BASE = import.meta.env.VITE_API_BASE_URL || `${API_ORIGIN}/api`

function unwrapResponse(payload, fallbackMessage) {
  if (!payload || payload.code !== 200 || !payload.data) {
    throw new Error(payload?.message || fallbackMessage)
  }
  return payload.data
}

export function resolveAssetUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  return `${API_ORIGIN}${path}`
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error('健康检查失败')
  }
  return response.json()
}

export async function fetchHomepageMedia() {
  const response = await fetch(`${API_BASE}/homepage-media`)
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.message || '首页展示媒体获取失败')
  }
  return unwrapResponse(payload, '首页展示媒体返回了无效数据')
}

export async function runVisionPipeline({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/pipeline_file/process`,
    file,
    confidence,
    iou,
    fallbackMessage: '处理接口调用失败',
    invalidMessage: '处理接口返回了无效数据',
  })
}

export async function runDehazePipeline({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/dehaze_pipeline_file/process`,
    file,
    confidence,
    iou,
    fallbackMessage: '去雾识别接口调用失败',
    invalidMessage: '去雾识别接口返回了无效数据',
  })
}

async function runPipelineRequest({ endpoint, file, confidence, iou, fallbackMessage, invalidMessage }) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('conf_thres', confidence)
  formData.append('iou_thres', iou)

  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  })

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.message || fallbackMessage)
  }

  return unwrapResponse(payload, invalidMessage)
}

export { API_BASE, API_ORIGIN }
