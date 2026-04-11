<template>
  <section class="demo-studio">
    <header class="studio-header studio-header--compact">
      <div class="studio-header__row">
        <div class="studio-header__titles">
          <p class="eyebrow">Pipeline Studio</p>
          <h1>自定义流程编排</h1>
        </div>
        <p
          class="lede lede-one-line"
          title="在下方第一个画幅内上传图片或视频；于自定义编排中选择快捷模板，从功能区拖入或点击加入当前流程后运行。"
        >
          在下方第一个画幅内上传图片或视频；于自定义编排中选择快捷模板，从功能区拖入或点击加入当前流程后运行。
        </p>
      </div>
    </header>

    <div class="panel panel-orchestration">
      <div class="panel-head">
        <h2>自定义流程编排</h2>
      </div>

      <div class="preset-block">
        <div class="preset-block-head">
          <span class="preset-block-title">快捷模板</span>
          <span class="panel-hint">一键填入当前流程</span>
        </div>
        <div class="preset-scroll">
          <button
            v-for="preset in presetFlows"
            :key="preset.name"
            type="button"
            class="preset-pill"
            @click="applyPreset(preset.steps)"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>

      <div class="orchestration-split">
        <div class="split-column split-zone">
          <div class="split-column-head">
            <h3>功能区</h3>
            <span class="panel-hint">点击加入，或拖入右侧时间线</span>
          </div>
          <div class="palette">
            <button
              v-for="module in moduleCatalog"
              :key="module.key"
              type="button"
              class="palette-card"
              draggable="true"
              @click="addModule(module.key)"
              @dragstart="onCatalogDragStart(module.key)"
            >
              <span class="palette-code">{{ module.code }}</span>
              <span class="palette-label">{{ module.label }}</span>
              <span class="palette-short">{{ module.short }}</span>
            </button>
          </div>
        </div>

        <div class="split-column split-flow">
          <div class="timeline-head">
            <h3>当前流程</h3>
            <button type="button" class="btn-text" @click="clearFlow">清空流程</button>
          </div>
          <div class="timeline-scroll" @dragover.prevent @drop="onFlowDrop(flowModules.length)">
            <div class="timeline-rail">
              <div
                v-for="(segment, index) in timelineSegments"
                :key="`seg-${index}`"
                class="timeline-segment"
                :class="{ ghost: segment.ghost }"
              >
                <span
                  v-if="index > 0"
                  class="timeline-connector"
                  :class="{ 'is-faint': segment.ghost }"
                  aria-hidden="true"
                />
                <article
                  class="timeline-node"
                  :class="{
                    'is-input': segment.kind === 'input',
                    'is-module': segment.kind === 'module',
                    'is-ghost': segment.ghost,
                    'is-busy': loading && executingIndex === segment.flowIndex,
                  }"
                  :draggable="segment.kind === 'module'"
                  @dragstart="segment.kind === 'module' ? onFlowDragStart(segment.flowIndex) : undefined"
                  @dragover.prevent
                  @drop.stop="segment.flowIndex != null ? onFlowDrop(segment.flowIndex) : undefined"
                >
                  <span class="node-index">{{ segment.displayIndex }}</span>
                  <span class="node-title">{{ segment.title }}</span>
                  <span class="node-sub">{{ segment.sub }}</span>
                  <div v-if="segment.kind === 'module' && segment.flowIndex != null" class="node-ops">
                    <button type="button" :disabled="segment.flowIndex === 0" @click="moveModule(segment.flowIndex, -1)">
                      ↑
                    </button>
                    <button
                      type="button"
                      :disabled="segment.flowIndex === flowModules.length - 1"
                      @click="moveModule(segment.flowIndex, 1)"
                    >
                      ↓
                    </button>
                    <button type="button" @click="removeModule(segment.flowIndex)">×</button>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <section class="film-section">
      <div class="film-head">
        <div>
          <p class="eyebrow">Step comparison</p>
          <h2>步骤结果对比</h2>
        </div>
        <div v-if="summaryItems.length" class="film-stats">
          <span v-for="item in summaryItems" :key="item.label">
            <em>{{ item.value }}</em>
            {{ item.label }}
          </span>
        </div>
      </div>

      <div class="film-strip">
        <article
          v-for="(step, index) in displaySteps"
          :key="`${step.key}-film-${index}`"
          class="film-card"
          :class="{
            'is-ready': Boolean(step.src),
            'is-pending': loading && index === executingIndex,
          }"
        >
          <div class="film-card-top">
            <span class="film-idx">{{ String(index).padStart(2, '0') }}</span>
            <div class="film-titles">
              <strong>{{ step.label }}</strong>
              <span>{{ step.description }}</span>
            </div>
          </div>
          <div
            v-if="index === 0"
            class="film-viewport film-viewport-upload"
            :class="{ 'is-drag-over': dragOverUpload, 'has-media': Boolean(step.src) }"
            @dragenter.prevent="dragOverUpload = true"
            @dragleave.prevent="onUploadDragLeave"
            @dragover.prevent="dragOverUpload = true"
            @drop.prevent="onUploadDrop"
          >
            <input
              id="demo-film-upload-input"
              class="film-file-input"
              type="file"
              accept="image/*,video/*"
              @change="handleFileChange"
            />
            <div v-if="loading && index === executingIndex" class="film-shimmer" aria-hidden="true" />
            <video
              v-if="step.src && step.kind === 'video'"
              :key="step.src"
              :src="step.src"
              autoplay
              muted
              loop
              playsinline
              controls
              preload="auto"
            />
            <img v-else-if="step.src" :src="step.src" :alt="step.label" />
            <label v-else class="film-upload-hit" for="demo-film-upload-input">
              <span class="film-upload-title">点击或拖入文件</span>
              <span class="film-upload-sub">{{ mediaLabel }} · 支持识别、去雾、去雨与低光链路</span>
            </label>
            <label v-if="step.src" class="film-replace-btn" for="demo-film-upload-input">更换文件</label>
          </div>
          <div v-else class="film-viewport">
            <div v-if="loading && index === executingIndex" class="film-shimmer" aria-hidden="true" />
            <video
              v-if="step.src && step.kind === 'video'"
              :key="step.src"
              :src="step.src"
              autoplay
              muted
              loop
              playsinline
              controls
              preload="auto"
            />
            <img v-else-if="step.src" :src="step.src" :alt="step.label" />
            <span v-else class="film-placeholder">{{ step.empty }}</span>
          </div>
        </article>
      </div>

      <p v-if="errorMessage" class="film-error">{{ errorMessage }}</p>

      <footer class="studio-bottom-bar">
        <div class="bottom-bar-copy">
          <div class="flow-chip" :title="flowStatus">{{ flowStatus }}</div>
          <p class="status-line">{{ loading ? loadingMessage : '在首格完成上传并配置流程后，点击下方按钮运行。' }}</p>
        </div>
        <div class="bottom-bar-actions">
          <button
            type="button"
            class="btn-secondary btn-primary-bottom"
            :disabled="loading"
            @click="clearForRetest"
          >
            清空 · 再次测试
          </button>
          <button
            class="btn-primary btn-primary-bottom"
            type="button"
            :disabled="!selectedFile || !flowModules.length || loading"
            @click="submitPipeline"
          >
            {{ loading ? '执行中…' : '运行流程' }}
          </button>
        </div>
      </footer>
    </section>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import {
  fileFromAssetUrl,
  resolveAssetUrl,
  runDehazeOnly,
  runDerainOnly,
  runDirectDetect,
  runLightweightLowLightEnhance,
  runLowLightEnhance,
} from '../services/api'

const moduleCatalog = [
  {
    key: 'detect',
    code: 'DET',
    label: '识别',
    short: '目标检测',
    description: '输出目标框、类别与置信度。',
    empty: '待识别',
    runner: runDirectDetect,
    outputLabel: '识别结果',
  },
  {
    key: 'dehaze',
    code: 'FOG',
    label: '图像去雾',
    short: 'C2PNet',
    description: '恢复雾天道路可见度。',
    empty: '待去雾',
    runner: runDehazeOnly,
    outputLabel: '去雾结果',
  },
  {
    key: 'derain',
    code: 'RAIN',
    label: '图像去雨',
    short: 'Attentive GAN',
    description: '削弱雨线与雨天干扰。',
    empty: '待去雨',
    runner: runDerainOnly,
    outputLabel: '去雨结果',
  },
  {
    key: 'low-light',
    code: 'LUX',
    label: '低光增强',
    short: '高质量增强',
    description: '提升暗光细节与亮度。',
    empty: '待增强',
    runner: runLowLightEnhance,
    outputLabel: '低光增强结果',
  },
  {
    key: 'lightweight-low-light',
    code: 'FAST',
    label: '轻量低光增强',
    short: '轻量化',
    description: '更轻量的低光增强。',
    empty: '待轻量增强',
    runner: runLightweightLowLightEnhance,
    outputLabel: '轻量增强结果',
  },
]

const presetFlows = [
  { name: '直接识别', steps: ['detect'] },
  { name: '低光 → 识别', steps: ['low-light', 'detect'] },
  { name: '去雨 → 识别', steps: ['derain', 'detect'] },
  { name: '去雾 → 识别', steps: ['dehaze', 'detect'] },
  { name: '低光 → 去雨 → 识别', steps: ['low-light', 'derain', 'detect'] },
  { name: '轻量增强 → 识别', steps: ['lightweight-low-light', 'detect'] },
]

const moduleMap = Object.fromEntries(moduleCatalog.map((module) => [module.key, module]))

const loading = ref(false)
const executingIndex = ref(-1)
const selectedFile = ref(null)
const result = ref(null)
const errorMessage = ref('')
const localPreviewUrl = ref('')
const dragOverUpload = ref(false)
const flowModules = ref(['low-light', 'derain', 'detect'])
const dragPayload = ref(null)
const liveSteps = ref(null)

const isPreviewVideo = computed(() => (selectedFile.value?.type || '').startsWith('video/'))
const mediaKind = computed(() => (isPreviewVideo.value ? 'video' : 'image'))
const mediaLabel = computed(() => (isPreviewVideo.value ? '视频' : '图片'))
const flowStatus = computed(() => ['上传', ...flowModules.value.map((key) => moduleMap[key].label)].join(' → '))
const loadingMessage = computed(() => (isPreviewVideo.value ? '视频链路处理中，导出可能需要稍候。' : '正在按步骤处理…'))

const timelineSegments = computed(() => {
  const segments = [
    {
      kind: 'input',
      displayIndex: '00',
      title: '上传',
      sub: '原始输入',
      ghost: false,
      flowIndex: null,
    },
  ]

  flowModules.value.forEach((key, index) => {
    const mod = moduleMap[key]
    segments.push({
      kind: 'module',
      displayIndex: String(index + 1).padStart(2, '0'),
      title: mod.label,
      sub: mod.short,
      ghost: false,
      flowIndex: index,
    })
  })

  if (!flowModules.value.length) {
    segments.push({
      kind: 'placeholder',
      displayIndex: '—',
      title: '添加模块',
      sub: '从上方库拖入或点击',
      ghost: true,
      flowIndex: null,
    })
  }

  return segments
})

const displaySteps = computed(() => {
  if (liveSteps.value?.length) return liveSteps.value
  if (result.value?.steps?.length) return result.value.steps
  return buildEmptySteps()
})

const summaryItems = computed(() => {
  const data = result.value?.raw || {}
  const timing = result.value?.totalMs
  const items = []

  if (Number.isFinite(Number(data.count))) items.push({ label: '目标数', value: data.count })
  if (Number.isFinite(Number(data.summary?.avg_confidence))) {
    items.push({ label: '平均置信度', value: data.summary.avg_confidence })
  }
  if (Number.isFinite(Number(timing))) items.push({ label: '总耗时 ms', value: Math.round(Number(timing)) })
  return items
})

function buildEmptySteps() {
  return [makeInputStep(localPreviewUrl.value), ...flowModules.value.map((key) => makeModuleStep(key, '', mediaKind.value))]
}

function makeInputStep(src) {
  return {
    key: 'input',
    label: '上传',
    description: '原始输入。',
    empty: '等待上传',
    src,
    kind: mediaKind.value,
  }
}

function makeModuleStep(moduleKey, src, kind = mediaKind.value) {
  const module = moduleMap[moduleKey]
  return {
    key: moduleKey,
    label: module.label,
    description: module.description,
    empty: module.empty,
    src,
    kind,
  }
}

function asset(path) {
  return path ? resolveAssetUrl(path) : ''
}

function resultPath(data) {
  return data.result_media || data.result_image || data.enhanced_media || data.enhanced_image || ''
}

function extensionFor(kind) {
  return kind === 'video' ? 'mp4' : 'jpg'
}

function addModule(moduleKey) {
  flowModules.value = [...flowModules.value, moduleKey]
  resetResult()
}

function removeModule(index) {
  flowModules.value = flowModules.value.filter((_, itemIndex) => itemIndex !== index)
  resetResult()
}

function moveModule(index, direction) {
  const nextIndex = index + direction
  if (nextIndex < 0 || nextIndex >= flowModules.value.length) return

  const next = [...flowModules.value]
  const [item] = next.splice(index, 1)
  next.splice(nextIndex, 0, item)
  flowModules.value = next
  resetResult()
}

function clearFlow() {
  flowModules.value = []
  resetResult()
}

function applyPreset(steps) {
  flowModules.value = [...steps]
  resetResult()
}

function onCatalogDragStart(moduleKey) {
  dragPayload.value = { source: 'catalog', moduleKey }
}

function onFlowDragStart(index) {
  dragPayload.value = { source: 'flow', index }
}

function onFlowDrop(index) {
  const payload = dragPayload.value
  if (!payload) return

  const next = [...flowModules.value]
  if (payload.source === 'catalog') {
    next.splice(index, 0, payload.moduleKey)
  } else if (payload.source === 'flow') {
    const [item] = next.splice(payload.index, 1)
    const targetIndex = payload.index < index ? index - 1 : index
    next.splice(targetIndex, 0, item)
  }

  flowModules.value = next
  dragPayload.value = null
  resetResult()
}

function resetResult() {
  result.value = null
  liveSteps.value = null
  errorMessage.value = ''
  executingIndex.value = -1
}

function revokePreview() {
  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value)
    localPreviewUrl.value = ''
  }
}

function pickUploadFile(file) {
  if (!file) return
  const ok = file.type.startsWith('image/') || file.type.startsWith('video/')
  if (!ok) {
    errorMessage.value = '请上传图片或视频。'
    return
  }

  revokePreview()
  selectedFile.value = file
  errorMessage.value = ''
  result.value = null
  liveSteps.value = null
  localPreviewUrl.value = URL.createObjectURL(file)
}

function handleFileChange(event) {
  const [file] = event.target.files || []
  pickUploadFile(file)
  if (event.target) event.target.value = ''
}

function clearForRetest() {
  if (loading.value) return
  revokePreview()
  selectedFile.value = null
  result.value = null
  liveSteps.value = null
  errorMessage.value = ''
  executingIndex.value = -1
  dragOverUpload.value = false
  const input = document.getElementById('demo-film-upload-input')
  if (input) input.value = ''
}

function onUploadDragLeave(event) {
  const next = event.relatedTarget
  if (next && event.currentTarget.contains(next)) return
  dragOverUpload.value = false
}

function onUploadDrop(event) {
  dragOverUpload.value = false
  const [file] = event.dataTransfer?.files || []
  pickUploadFile(file)
}

async function submitPipeline() {
  if (!selectedFile.value || !flowModules.value.length || loading.value) return

  loading.value = true
  errorMessage.value = ''
  liveSteps.value = buildEmptySteps()
  executingIndex.value = -1

  const startedAt = performance.now()
  const steps = [makeInputStep(localPreviewUrl.value)]
  let currentFile = selectedFile.value
  let lastData = null

  try {
    for (const [index, moduleKey] of flowModules.value.entries()) {
      executingIndex.value = index + 1
      const module = moduleMap[moduleKey]
      const data = await module.runner({ file: currentFile })
      const outputPath = resultPath(data)
      const outputKind = data.media_type || mediaKind.value

      steps.push(makeModuleStep(moduleKey, asset(outputPath), outputKind))
      lastData = data

      const merged = buildEmptySteps().map((placeholder, stepIndex) => steps[stepIndex] || placeholder)
      liveSteps.value = merged

      if (index < flowModules.value.length - 1) {
        currentFile = await fileFromAssetUrl(
          outputPath,
          `${moduleKey}-${index + 1}.${extensionFor(outputKind)}`,
          currentFile.type,
        )
      }
    }

    result.value = {
      raw: lastData || {},
      steps,
      totalMs: performance.now() - startedAt,
    }
    liveSteps.value = null
  } catch (error) {
    errorMessage.value = error.message || '流程失败，请检查顺序或稍后重试。'
    liveSteps.value = null
  } finally {
    loading.value = false
    executingIndex.value = -1
  }
}

onBeforeUnmount(() => {
  revokePreview()
})
</script>

<style scoped>
.demo-studio {
  display: flex;
  flex-direction: column;
  gap: clamp(16px, 2.5vw, 22px);
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 4px 48px;
}

.studio-header {
  padding: clamp(20px, 3vw, 28px) clamp(22px, 3vw, 32px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background:
    linear-gradient(145deg, rgba(20, 184, 166, 0.12), transparent 55%),
    linear-gradient(320deg, rgba(56, 189, 248, 0.08), transparent 50%),
    rgba(8, 12, 22, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--shadow);
}

.studio-header--compact {
  padding: 10px 16px 12px;
  border-radius: 14px;
}

.studio-header__row {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 12px 20px;
  min-width: 0;
}

.studio-header__titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.studio-header__titles .eyebrow {
  margin: 0;
  font-size: 0.62rem;
}

.studio-header__titles h1 {
  margin: 0;
  font-size: clamp(1.05rem, 2.2vw, 1.35rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: #f8fafc;
  white-space: nowrap;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(94, 234, 212, 0.85);
}

.lede-one-line {
  flex: 1;
  min-width: 0;
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.35;
  color: rgba(203, 213, 225, 0.88);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lede {
  margin: 12px 0 0;
  max-width: 50rem;
  font-size: 0.98rem;
  line-height: 1.65;
  color: var(--muted);
}

.flow-chip {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 0.8rem;
  line-height: 1.45;
  color: rgba(226, 232, 240, 0.88);
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.08);
  max-height: 4.5em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.btn-primary {
  min-height: 48px;
  padding: 0 22px;
  border-radius: 14px;
  font-weight: 700;
  color: #041016;
  background: linear-gradient(180deg, #ecfeff 0%, #5eead4 100%);
  cursor: pointer;
  transition: transform 0.35s var(--ease-apple), opacity 0.25s ease;
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary:not(:disabled):hover {
  transform: translateY(-2px);
}

.btn-primary-bottom {
  min-width: min(100%, 200px);
  flex-shrink: 0;
}

.btn-secondary {
  min-height: 48px;
  padding: 0 20px;
  border-radius: 14px;
  font-weight: 650;
  color: rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  cursor: pointer;
  transition:
    transform 0.35s var(--ease-apple),
    border-color 0.25s ease,
    background 0.25s ease;
}

.btn-secondary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-secondary:not(:disabled):hover {
  transform: translateY(-2px);
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(255, 255, 255, 0.09);
}

.bottom-bar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
  align-items: center;
}

.status-line {
  margin: 0;
  font-size: 0.82rem;
  color: rgba(148, 163, 184, 0.9);
  line-height: 1.5;
}

.studio-bottom-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px 24px;
  margin-top: 22px;
  padding-top: 22px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.bottom-bar-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: min(100%, 520px);
  flex: 1;
}

.panel-orchestration {
  margin-bottom: 0;
}

.preset-block {
  margin-bottom: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.preset-block-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px 16px;
  margin-bottom: 12px;
}

.preset-block-title {
  font-size: 0.92rem;
  font-weight: 650;
  color: #f1f5f9;
}

.orchestration-split {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(280px, 1.15fr);
  gap: 0 20px;
  align-items: start;
}

.split-column {
  min-width: 0;
}

.split-flow {
  padding-left: 20px;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
}

.split-column-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px 12px;
  margin-bottom: 14px;
}

.split-column-head h3,
.timeline-head h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 650;
  color: #f1f5f9;
}

.panel {
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(6, 10, 20, 0.72);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: clamp(18px, 2.2vw, 22px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22);
}

.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-head.tight {
  margin-bottom: 10px;
}

.panel-head h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 650;
  color: #f1f5f9;
}

.panel-hint {
  font-size: 0.78rem;
  color: rgba(148, 163, 184, 0.95);
}

.preset-scroll {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-pill {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 0.78rem;
  color: rgba(226, 232, 240, 0.92);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: border-color 0.25s ease, background 0.25s ease;
}

.preset-pill:hover {
  border-color: rgba(94, 234, 212, 0.35);
  background: rgba(94, 234, 212, 0.08);
}

.palette {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.palette-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 12px 12px 14px;
  border-radius: 14px;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.03);
  color: #e2e8f0;
  cursor: grab;
  transition:
    transform 0.35s var(--ease-apple),
    border-color 0.25s ease,
    background 0.25s ease;
}

.palette-card:hover {
  transform: translateY(-2px);
  border-color: rgba(125, 211, 252, 0.28);
  background: rgba(255, 255, 255, 0.055);
}

.palette-code {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: rgba(250, 204, 21, 0.95);
}

.palette-label {
  font-size: 0.88rem;
  font-weight: 650;
}

.palette-short {
  font-size: 0.72rem;
  color: rgba(148, 163, 184, 0.95);
  line-height: 1.4;
}

.timeline-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.btn-text {
  padding: 6px 10px;
  border-radius: 10px;
  font-size: 0.8rem;
  color: rgba(203, 213, 225, 0.85);
  background: transparent;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.btn-text:hover {
  border-color: rgba(248, 113, 113, 0.35);
  color: #fecaca;
}

.timeline-scroll {
  overflow-x: auto;
  padding-bottom: 6px;
  scrollbar-width: thin;
}

.timeline-rail {
  display: flex;
  align-items: stretch;
  gap: 0;
  min-height: 120px;
}

.timeline-segment {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
}

.timeline-segment .timeline-node {
  flex-shrink: 0;
}

.timeline-connector {
  width: 28px;
  height: 2px;
  margin: 0 2px;
  background: linear-gradient(90deg, rgba(94, 234, 212, 0.15), rgba(94, 234, 212, 0.65));
  border-radius: 999px;
}

.timeline-connector.is-faint {
  opacity: 0.35;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.2), rgba(148, 163, 184, 0.45));
}

.timeline-node {
  position: relative;
  width: 148px;
  min-height: 112px;
  padding: 12px 12px 10px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.035);
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition:
    border-color 0.3s ease,
    box-shadow 0.35s ease;
}

.timeline-node.is-input {
  border-color: rgba(45, 212, 191, 0.35);
  background: linear-gradient(165deg, rgba(20, 184, 166, 0.14), rgba(255, 255, 255, 0.02));
}

.timeline-node.is-module {
  cursor: grab;
}

.timeline-node.is-ghost {
  border-style: dashed;
  opacity: 0.75;
}

.timeline-node.is-busy {
  border-color: rgba(125, 211, 252, 0.45);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.2);
  animation: node-pulse 1.2s ease-in-out infinite;
}

@keyframes node-pulse {
  50% {
    box-shadow: 0 0 24px rgba(56, 189, 248, 0.18);
  }
}

.node-index {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: rgba(250, 204, 21, 0.9);
}

.node-title {
  font-size: 0.88rem;
  font-weight: 650;
  color: #f8fafc;
}

.node-sub {
  font-size: 0.72rem;
  line-height: 1.35;
  color: rgba(148, 163, 184, 0.95);
}

.node-ops {
  display: flex;
  gap: 4px;
  margin-top: auto;
  padding-top: 8px;
}

.node-ops button {
  flex: 1;
  min-height: 28px;
  border-radius: 8px;
  font-size: 0.78rem;
  color: rgba(226, 232, 240, 0.85);
  background: rgba(2, 6, 23, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
}

.node-ops button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.film-section {
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(5, 9, 18, 0.82);
  padding: clamp(20px, 2.5vw, 26px);
  box-shadow: var(--shadow);
}

.film-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.film-head h2 {
  margin: 6px 0 0;
  font-size: clamp(1.15rem, 2.4vw, 1.45rem);
  font-weight: 650;
  color: #f8fafc;
}

.film-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.film-stats span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 0.78rem;
  color: rgba(203, 213, 225, 0.88);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.film-stats em {
  font-style: normal;
  font-weight: 700;
  color: #f8fafc;
}

.film-strip {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 8px;
  scroll-snap-type: x proximity;
}

.film-card {
  flex: 0 0 min(440px, 90vw);
  scroll-snap-align: start;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.03);
  transition: border-color 0.3s ease, transform 0.35s var(--ease-apple);
}

.film-card.is-ready {
  border-color: rgba(94, 234, 212, 0.22);
}

.film-card:hover {
  transform: translateY(-3px);
}

.film-card-top {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.film-idx {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.95);
  background: linear-gradient(145deg, #fef9c3, #fbbf24);
}

.film-titles {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.film-titles strong {
  font-size: 0.95rem;
  font-weight: 650;
  color: #f8fafc;
}

.film-titles span {
  font-size: 0.75rem;
  line-height: 1.45;
  color: rgba(148, 163, 184, 0.95);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.film-viewport {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  aspect-ratio: 16 / 10;
  min-height: clamp(240px, 36vw, 420px);
  background:
    radial-gradient(ellipse at 50% 0%, rgba(148, 163, 184, 0.12), transparent 55%),
    #020617;
}

.film-viewport-upload {
  border: 1px dashed rgba(255, 255, 255, 0.14);
  transition:
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.film-viewport-upload.is-drag-over {
  border-color: rgba(94, 234, 212, 0.55);
  box-shadow: inset 0 0 0 1px rgba(94, 234, 212, 0.2);
}

.film-viewport-upload.has-media {
  border-style: solid;
  border-color: rgba(255, 255, 255, 0.1);
}

.film-file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.film-upload-hit {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  text-align: center;
  cursor: pointer;
}

.film-upload-title {
  font-size: 0.92rem;
  font-weight: 650;
  color: #e2e8f0;
}

.film-upload-sub {
  max-width: 16rem;
  font-size: 0.78rem;
  line-height: 1.5;
  color: rgba(148, 163, 184, 0.92);
}

.film-replace-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 4;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #f8fafc;
  background: rgba(2, 6, 23, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.14);
  cursor: pointer;
  user-select: none;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition:
    border-color 0.25s ease,
    background 0.25s ease;
}

.film-replace-btn:hover {
  border-color: rgba(94, 234, 212, 0.35);
  background: rgba(15, 23, 42, 0.88);
}

.film-viewport img,
.film-viewport video {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  background: #020617;
}

.film-placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 12px;
  text-align: center;
  font-size: 0.82rem;
  color: rgba(148, 163, 184, 0.75);
}

.film-shimmer {
  position: absolute;
  inset: 0;
  z-index: 3;
  background: linear-gradient(
    110deg,
    transparent 0%,
    rgba(255, 255, 255, 0.06) 45%,
    rgba(255, 255, 255, 0.12) 50%,
    rgba(255, 255, 255, 0.06) 55%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.1s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

.film-error {
  margin: 14px 0 0;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 0.88rem;
  color: #fecaca;
  background: rgba(127, 29, 29, 0.4);
  border: 1px solid rgba(248, 113, 113, 0.2);
}

@media (max-width: 900px) {
  .studio-header__row {
    flex-wrap: wrap;
  }

  .studio-header__titles h1 {
    white-space: normal;
  }

  .lede-one-line {
    flex-basis: 100%;
    white-space: normal;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: unset;
  }
}

@media (max-width: 960px) {
  .orchestration-split {
    grid-template-columns: 1fr;
  }

  .split-flow {
    padding-left: 0;
    padding-top: 20px;
    margin-top: 4px;
    border-left: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .studio-bottom-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .bottom-bar-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-primary-bottom {
    min-width: 0;
    width: 100%;
  }
}

@media (max-width: 560px) {
  .timeline-connector {
    width: 16px;
  }

  .timeline-node {
    width: 132px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .btn-primary:not(:disabled):hover,
  .btn-secondary:not(:disabled):hover,
  .palette-card:hover,
  .film-card:hover {
    transform: none;
  }

  .timeline-node.is-busy,
  .film-shimmer {
    animation: none;
  }
}
</style>
