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
    endpoint: `${API_BASE}/pipelines/low-light-detect`,
    file,
    confidence,
    iou,
    fallbackMessage: '处理接口调用失败',
    invalidMessage: '处理接口返回了无效数据',
  })
}

export async function runDirectDetect({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/detections/yolo26`,
    file,
    confidence,
    iou,
    fallbackMessage: '直接识别接口调用失败',
    invalidMessage: '直接识别接口返回了无效数据',
  })
}

export async function runLowLightEnhance({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/enhancements/low-light`,
    file,
    confidence,
    iou,
    fallbackMessage: '增强接口调用失败',
    invalidMessage: '增强接口返回了无效数据',
  })
}

export async function runLightweightLowLightEnhance({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/enhancements/low-light/lightweight`,
    file,
    confidence,
    iou,
    fallbackMessage: '轻量低光增强接口调用失败',
    invalidMessage: '轻量低光增强接口返回了无效数据',
  })
}

export async function runDerainOnly({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/enhancements/derain`,
    file,
    confidence,
    iou,
    fallbackMessage: '去雨接口调用失败',
    invalidMessage: '去雨接口返回了无效数据',
  })
}

export async function runDehazeOnly({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/enhancements/dehaze`,
    file,
    confidence,
    iou,
    fallbackMessage: '去雾接口调用失败',
    invalidMessage: '去雾接口返回了无效数据',
  })
}

export async function runDehazePipeline({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/pipelines/dehaze-detect`,
    file,
    confidence,
    iou,
    fallbackMessage: '去雾识别接口调用失败',
    invalidMessage: '去雾识别接口返回了无效数据',
  })
}

export async function runDerainPipeline({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/pipelines/derain-detect`,
    file,
    confidence,
    iou,
    fallbackMessage: '去雨识别接口调用失败',
    invalidMessage: '去雨识别接口返回了无效数据',
  })
}

export async function runLightweightPipeline({ file, confidence = 0.25, iou = 0.45 }) {
  return runPipelineRequest({
    endpoint: `${API_BASE}/pipelines/lightweight-low-light-detect`,
    file,
    confidence,
    iou,
    fallbackMessage: '轻量化增强识别接口调用失败',
    invalidMessage: '轻量化增强识别接口返回了无效数据',
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

export async function fileFromAssetUrl(path, filename, fallbackType = 'image/jpeg') {
  const response = await fetch(resolveAssetUrl(path))
  if (!response.ok) {
    throw new Error('中间结果读取失败，无法继续组合流程。')
  }

  const blob = await response.blob()
  const type = blob.type || fallbackType
  return new File([blob], filename, { type })
}

export { API_BASE, API_ORIGIN }
