<template>
  <section class="demo-page">
    <section class="pipeline-panel card-surface">
      <div class="panel-header premium">
        <div>
          <p class="section-tag">Pipeline Overview</p>
        </div>
        <div class="pipeline-actions">
          <button
            v-for="option in pipelineOptions"
            :key="option.value"
            class="mode-button"
            :class="{ 'is-active': pipelineMode === option.value }"
            type="button"
            @click="setPipelineMode(option.value)"
          >
            {{ option.label }}
          </button>
          <span class="status-pill">{{ activePipeline.status }}</span>
        </div>
      </div>

      <div class="pipeline-track">
        <article class="pipeline-card">
          <div class="pipeline-step">Stage 01</div>
          <div
            class="pipeline-media pipeline-media--upload"
            :class="{ 'is-drag-over': dragOverUpload }"
            @dragenter.prevent="dragOverUpload = true"
            @dragleave.prevent="onUploadDragLeave"
            @dragover.prevent="dragOverUpload = true"
            @drop.prevent="onUploadDrop"
          >
            <label class="upload-stage">
              <input type="file" accept="image/*,video/*" @change="handleFileChange" />

              <div v-if="localPreviewUrl" class="upload-preview">
                <video
                  v-if="isPreviewVideo"
                  :src="localPreviewUrl"
                  class="pipeline-asset"
                  controls
                  muted
                  playsinline
                />
                <img v-else :src="localPreviewUrl" alt="" class="pipeline-asset" />
              </div>
              <div v-else class="upload-empty">
                <span class="upload-plus" aria-hidden="true">+</span>
                <span class="upload-hint">点击或拖放上传</span>
              </div>
            </label>
          </div>
          <div class="pipeline-copy">
            <h4>上传图片或视频资源</h4>
          </div>
        </article>

        <article class="pipeline-card">
          <div class="pipeline-step">Compare 01</div>
          <div class="pipeline-media pipeline-media--compare">
            <ComparisonViewer
              :before-src="originalMediaUrl"
              :after-src="enhancedMediaUrl"
              :before-kind="originalMediaKind"
              :after-kind="enhancedMediaKind"
              before-label="原始输入"
              :after-label="activePipeline.middleLabel"
              :empty-text="emptyCompareText"
            />
          </div>
          <div class="pipeline-copy">
            <h4>{{ compareOneTitle }}</h4>
          </div>
        </article>

        <article class="pipeline-card">
          <div class="pipeline-step">Compare 02</div>
          <div class="pipeline-media pipeline-media--compare">
            <ComparisonViewer
              :before-src="enhancedMediaUrl"
              :after-src="detectedMediaUrl"
              :before-kind="enhancedMediaKind"
              :after-kind="detectedMediaKind"
              :before-label="activePipeline.middleLabel"
              after-label="检测结果"
              :empty-text="processingCompareText"
            />
          </div>
          <div class="pipeline-copy">
            <h4>{{ compareTwoTitle }}</h4>
          </div>
        </article>
      </div>

      <p v-if="loading" class="message-info">
        {{ loadingMessage }}
      </p>
      <p v-if="errorMessage" class="message-error">{{ errorMessage }}</p>
    </section>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import ComparisonViewer from '../components/ComparisonViewer.vue'
import {
  resolveAssetUrl,
  runDehazePipeline,
  runDerainPipeline,
  runLightweightPipeline,
  runVisionPipeline,
} from '../services/api'

const pipelineOptions = [
  {
    value: 'enhance',
    label: '增强识别',
    status: 'Input → Enhance → Detect',
    middleLabel: '增强结果',
    compareOneImage: '原始图片 / 增强结果',
    compareOneVideo: '原始视频 / 增强视频',
    compareTwoImage: '增强结果 / 检测结果',
    compareTwoVideo: '增强视频 / 检测视频',
    emptyImage: '上传图片后显示增强对比。',
    emptyVideo: '上传视频后显示增强对比。',
    processingImage: '处理完成后显示检测对比。',
    processingVideo: '视频处理完成后显示检测对比。',
    loadingImage: '图片增强与识别中，请稍候。',
    loadingVideo: '视频逐帧增强与识别中，请等待结果导出。',
    runner: runVisionPipeline,
  },
  {
    value: 'lightweight-enhance',
    label: '轻量增强识别',
    status: 'Input → Lightweight Enhance → Detect',
    middleLabel: '轻量增强结果',
    compareOneImage: '原始图片 / 轻量增强结果',
    compareOneVideo: '原始视频 / 轻量增强视频',
    compareTwoImage: '轻量增强结果 / 检测结果',
    compareTwoVideo: '轻量增强视频 / 检测视频',
    emptyImage: '上传图片后显示轻量增强对比。',
    emptyVideo: '上传视频后显示轻量增强对比。',
    processingImage: '处理完成后显示检测对比。',
    processingVideo: '视频处理完成后显示检测对比。',
    loadingImage: '图片轻量增强与识别中，请稍候。',
    loadingVideo: '视频逐帧轻量增强与识别中，请等待结果导出。',
    runner: runLightweightPipeline,
  },
  {
    value: 'dehaze',
    label: '去雾识别',
    status: 'Input → Dehaze → Detect',
    middleLabel: '去雾结果',
    compareOneImage: '原始图片 / 去雾结果',
    compareOneVideo: '原始视频 / 去雾视频',
    compareTwoImage: '去雾结果 / 检测结果',
    compareTwoVideo: '去雾视频 / 检测视频',
    emptyImage: '上传图片后显示去雾对比。',
    emptyVideo: '上传视频后显示去雾对比。',
    processingImage: '处理完成后显示检测对比。',
    processingVideo: '视频处理完成后显示检测对比。',
    loadingImage: '图片去雾与识别中，请稍候。',
    loadingVideo: '视频逐帧去雾与识别中，请等待结果导出。',
    runner: runDehazePipeline,
  },
  {
    value: 'derain',
    label: '去雨识别',
    status: 'Input → Derain → Detect',
    middleLabel: '去雨结果',
    compareOneImage: '原始图片 / 去雨结果',
    compareOneVideo: '原始视频 / 去雨视频',
    compareTwoImage: '去雨结果 / 检测结果',
    compareTwoVideo: '去雨视频 / 检测视频',
    emptyImage: '上传图片后显示去雨对比。',
    emptyVideo: '上传视频后显示去雨对比。',
    processingImage: '处理完成后显示检测对比。',
    processingVideo: '视频处理完成后显示检测对比。',
    loadingImage: '图片去雨与识别中，请稍候。',
    loadingVideo: '视频逐帧去雨与识别中，请等待结果导出。',
    runner: runDerainPipeline,
  },
]

const loading = ref(false)
const selectedFile = ref(null)
const result = ref(null)
const errorMessage = ref('')
const localPreviewUrl = ref('')
const dragOverUpload = ref(false)
const pipelineMode = ref('enhance')

const activePipeline = computed(() => pipelineOptions.find((option) => option.value === pipelineMode.value) || pipelineOptions[0])

const isPreviewVideo = computed(() => {
  const t = selectedFile.value?.type || ''
  return t.startsWith('video/')
})

const mediaType = computed(() => result.value?.media_type || (isPreviewVideo.value ? 'video' : 'image'))

const originalMediaKind = computed(() => (isPreviewVideo.value ? 'video' : 'image'))
const enhancedMediaKind = computed(() => mediaType.value)
const detectedMediaKind = computed(() => mediaType.value)

const compareOneTitle = computed(() =>
  mediaType.value === 'video' ? activePipeline.value.compareOneVideo : activePipeline.value.compareOneImage,
)

const compareTwoTitle = computed(() =>
  mediaType.value === 'video' ? activePipeline.value.compareTwoVideo : activePipeline.value.compareTwoImage,
)

const emptyCompareText = computed(() =>
  isPreviewVideo.value ? activePipeline.value.emptyVideo : activePipeline.value.emptyImage,
)

const processingCompareText = computed(() =>
  isPreviewVideo.value ? activePipeline.value.processingVideo : activePipeline.value.processingImage,
)

const loadingMessage = computed(() =>
  isPreviewVideo.value ? activePipeline.value.loadingVideo : activePipeline.value.loadingImage,
)

const originalMediaUrl = computed(() => {
  if (result.value?.upload_media) return resolveAssetUrl(result.value.upload_media)
  if (result.value?.upload_image) return resolveAssetUrl(result.value.upload_image)
  return localPreviewUrl.value
})

const enhancedMediaUrl = computed(() => {
  if (result.value?.enhanced_media) return resolveAssetUrl(result.value.enhanced_media)
  if (!result.value?.enhanced_image) return ''
  return resolveAssetUrl(result.value.enhanced_image)
})

const detectedMediaUrl = computed(() => {
  if (result.value?.result_media) return resolveAssetUrl(result.value.result_media)
  if (!result.value?.result_image) return ''
  return resolveAssetUrl(result.value.result_image)
})

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
    errorMessage.value = '请上传图片或视频文件。'
    return
  }

  revokePreview()
  selectedFile.value = file
  errorMessage.value = ''
  result.value = null
  localPreviewUrl.value = URL.createObjectURL(file)
  submitPipeline()
}

function setPipelineMode(mode) {
  if (pipelineMode.value === mode) return
  pipelineMode.value = mode
  result.value = null
  errorMessage.value = ''
  if (selectedFile.value) {
    submitPipeline()
  }
}

function handleFileChange(event) {
  const [file] = event.target.files || []
  pickUploadFile(file)
  if (event.target) event.target.value = ''
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
  if (!selectedFile.value) return

  loading.value = true
  errorMessage.value = ''

  try {
    result.value = await activePipeline.value.runner({
      file: selectedFile.value,
    })
  } catch (error) {
    errorMessage.value = error.message || '处理失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onBeforeUnmount(() => {
  revokePreview()
})
</script>

<style scoped>
.demo-page {
  display: grid;
}

.card-surface {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 28px;
  background: linear-gradient(165deg, rgba(18, 26, 42, 0.72) 0%, rgba(8, 12, 24, 0.88) 100%);
  box-shadow:
    0 0 0 0.5px rgba(255, 255, 255, 0.06) inset,
    0 24px 80px rgba(0, 0, 0, 0.35),
    0 1px 0 rgba(255, 255, 255, 0.04) inset;
  backdrop-filter: blur(48px) saturate(150%);
  -webkit-backdrop-filter: blur(48px) saturate(150%);
  transition:
    box-shadow 0.6s cubic-bezier(0.16, 1, 0.3, 1),
    border-color 0.5s ease;
}

.pipeline-panel {
  padding: 30px;
}

.pipeline-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(125, 211, 252, 0.07), transparent 55%),
    linear-gradient(145deg, rgba(148, 163, 184, 0.06), transparent 42%);
  pointer-events: none;
}

.panel-header.premium {
  position: relative;
  z-index: 1;
  margin-bottom: 24px;
  animation: panel-header-in 0.75s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.pipeline-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.mode-button {
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.72);
  color: rgba(226, 232, 240, 0.78);
  font: inherit;
  font-size: 0.86rem;
  cursor: pointer;
  transition:
    border-color 0.3s ease,
    background 0.3s ease,
    color 0.3s ease;
}

.mode-button:hover,
.mode-button.is-active {
  border-color: rgba(125, 211, 252, 0.55);
  background: rgba(14, 116, 144, 0.24);
  color: rgba(248, 250, 252, 0.94);
}

.pipeline-track {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  align-items: stretch;
}

.pipeline-card {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  align-content: start;
  gap: 16px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  animation: card-rise 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
  transition:
    transform 0.55s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.55s cubic-bezier(0.16, 1, 0.3, 1),
    border-color 0.4s ease,
    background 0.45s ease;
}

.pipeline-card:nth-child(1) {
  animation-delay: 0.06s;
}

.pipeline-card:nth-child(2) {
  animation-delay: 0.14s;
}

.pipeline-card:nth-child(3) {
  animation-delay: 0.22s;
}

.pipeline-card:hover {
  transform: translateY(-6px);
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.055);
  box-shadow:
    0 20px 56px rgba(0, 0, 0, 0.28),
    0 0 0 1px rgba(125, 211, 252, 0.06);
}

.pipeline-step {
  font-size: 0.78rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.8);
  text-align: center;
}

.pipeline-media {
  overflow: hidden;
  width: 100%;
  max-height: 100%;
  min-height: 0;
  aspect-ratio: 4 / 3;
  border-radius: 18px;
  background: rgba(2, 6, 23, 0.65);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05) inset;
  transition: box-shadow 0.45s ease;
  place-self: center;
}

.pipeline-card:hover .pipeline-media {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.08) inset,
    0 0 40px rgba(56, 189, 248, 0.06);
}

.pipeline-media--compare,
.pipeline-media--upload {
  position: relative;
}

.pipeline-media--upload .upload-stage {
  position: absolute;
  inset: 0;
  display: block;
  margin: 0;
}

.pipeline-media--compare :deep(.comparison-viewer) {
  position: absolute;
  inset: 0;
  height: 100%;
}

.pipeline-media--compare :deep(.comparison-stage) {
  min-height: 0;
  height: 100%;
  border-radius: 18px;
}

.pipeline-copy h4 {
  margin: 0;
  color: rgba(248, 250, 252, 0.92);
  font-size: 0.98rem;
  font-weight: 500;
  letter-spacing: -0.02em;
  text-align: center;
}

.upload-stage {
  cursor: pointer;
}

.upload-stage input {
  display: none;
}

.upload-preview,
.upload-empty {
  overflow: hidden;
  height: 100%;
  min-height: 100%;
  border-radius: 18px;
  border: 1px dashed rgba(125, 211, 252, 0.2);
  background:
    radial-gradient(circle at 50% 30%, rgba(125, 211, 252, 0.08), transparent 45%),
    linear-gradient(180deg, rgba(9, 16, 28, 0.94), rgba(15, 23, 42, 0.82));
  transition:
    border-color 0.45s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.pipeline-media--upload.is-drag-over .upload-preview,
.pipeline-media--upload.is-drag-over .upload-empty {
  border-color: rgba(125, 211, 252, 0.55);
  box-shadow: inset 0 0 0 1px rgba(94, 234, 212, 0.2);
}

.upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  pointer-events: none;
}

.upload-plus {
  font-size: clamp(3.25rem, 11vw, 5.25rem);
  font-weight: 200;
  line-height: 1;
  color: rgba(125, 211, 252, 0.88);
  text-shadow: 0 0 48px rgba(94, 234, 212, 0.35);
  user-select: none;
  animation: upload-plus-breathe 5s ease-in-out infinite;
}

@keyframes upload-plus-breathe {
  0%,
  100% {
    opacity: 0.82;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.04);
  }
}

.upload-hint {
  font-size: 0.86rem;
  letter-spacing: 0.04em;
  color: rgba(203, 213, 225, 0.58);
  user-select: none;
}

.upload-preview {
  border-style: solid;
  border-color: rgba(255, 255, 255, 0.1);
}

.pipeline-asset {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  background: #020617;
  transform: scale(1.001);
  transition: transform 0.85s cubic-bezier(0.16, 1, 0.3, 1);
}

.pipeline-card:hover .upload-preview .pipeline-asset {
  transform: scale(1.03);
}

.message-error {
  position: relative;
  z-index: 1;
  margin: 18px 0 0;
  padding: 12px 16px;
  border-radius: 14px;
  color: #fecaca;
  background: rgba(127, 29, 29, 0.45);
  border: 1px solid rgba(248, 113, 113, 0.2);
  animation: message-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.message-info {
  position: relative;
  z-index: 1;
  margin: 18px 0 0;
  padding: 12px 16px;
  border-radius: 14px;
  color: rgba(226, 232, 240, 0.92);
  background: rgba(14, 116, 144, 0.22);
  border: 1px solid rgba(103, 232, 249, 0.2);
  animation: message-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes message-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1180px) {
  .pipeline-track {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .pipeline-panel {
    padding: 22px;
  }

  .pipeline-actions {
    align-items: flex-start;
  }

  .panel-header {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .panel-header.premium,
  .pipeline-card {
    animation: none;
  }

  .upload-plus {
    animation: none;
  }

  .message-error,
  .message-info {
    animation: none;
  }

  .pipeline-card,
  .pipeline-media,
  .pipeline-asset,
  .upload-preview,
  .upload-empty {
    transition: none;
  }

  .pipeline-card:hover {
    transform: none;
  }

  .pipeline-card:hover .upload-preview .pipeline-asset {
    transform: none;
  }
}
</style>
