<template>
  <section class="home-page">
    <section class="home-hero">
      <div class="hero-copy">
        <p class="section-tag">Weather Vision System</p>
        <h2>复杂天气感知展示系统</h2>
        <p class="hero-lead">
          雨雾夜间道路场景下的复原、视频处理与目标识别。
        </p>
        <RouterLink class="primary-button hero-cta" to="/demo">进入功能展示</RouterLink>
      </div>

      <div class="hero-media">
        <ComparisonViewer
          :before-src="rawPanel.mediaSrc"
          :after-src="detectedPanel.mediaSrc"
          :before-kind="rawPanel.kind"
          :after-kind="detectedPanel.kind"
          before-label="原始输入"
          after-label="识别输出"
          empty-text="等待媒体内容"
        />
      </div>
    </section>

    <section class="capability-section">
      <div class="section-heading">
        <p class="section-tag">Capabilities</p>
        <h3>功能覆盖</h3>
      </div>

      <div class="capability-grid">
        <article v-for="item in capabilityItems" :key="item.title" class="capability-item">
          <span>{{ item.code }}</span>
          <h4>{{ item.title }}</h4>
          <p>{{ item.description }}</p>
        </article>
      </div>
    </section>

    <section class="recipe-section">
      <div class="section-heading">
        <p class="section-tag">Combinations</p>
        <h3>可搭配流程</h3>
      </div>

      <div class="recipe-list">
        <article v-for="recipe in recipes" :key="recipe.title" class="recipe-item">
          <h4>{{ recipe.title }}</h4>
          <p>{{ recipe.flow }}</p>
        </article>
      </div>
    </section>

    <section id="pipeline-overview" class="pipeline-panel">
      <div class="section-heading inline">
        <div>
          <p class="section-tag">Sample Pipeline</p>
          <h3>示例链路</h3>
        </div>
        <span class="status-pill">Input → Enhance → Detect</span>
      </div>

      <div class="pipeline-track">
        <article v-for="panel in displayPanels" :key="panel.key" class="pipeline-card">
          <div class="pipeline-step">{{ panel.step }}</div>
          <div class="pipeline-media">
            <component :is="panel.tag" :src="panel.mediaSrc" class="pipeline-asset" v-bind="panel.mediaProps" />
          </div>
          <div class="pipeline-copy">
            <h4>{{ panel.title }}</h4>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ComparisonViewer from '../components/ComparisonViewer.vue'
import { fetchHomepageMedia, resolveAssetUrl } from '../services/api'

const capabilityItems = [
  { code: 'DET', title: '直接识别', description: '上传图片或视频后直接输出目标框、类别与置信度。' },
  { code: 'RAIN', title: '去雨处理', description: '降低雨线和湿滑画面对检测结果的干扰。' },
  { code: 'FOG', title: '去雾处理', description: '增强雾天道路轮廓和远处目标可见度。' },
  { code: 'LUX', title: '低光增强', description: '提升夜间和欠曝光场景中的细节表现。' },
  { code: 'FAST', title: '轻量增强', description: '适合更关注响应速度的展示与验证。' },
  { code: 'VID', title: '视频流程', description: '对视频逐帧处理，并输出完整结果片段。' },
]

const recipes = [
  { title: '直接识别', flow: '上传 → 识别' },
  { title: '雨天识别', flow: '上传 → 去雨 → 识别' },
  { title: '夜间识别', flow: '上传 → 增强 → 识别' },
  { title: '复杂天气识别', flow: '上传 → 增强 → 去雨 → 识别' },
]

const fallbackPanels = [
  {
    key: 'raw',
    step: 'Stage 01',
    title: '原始输入',
    media_type: 'image',
    src: '/posters/raw-scene.svg',
  },
  {
    key: 'enhanced',
    step: 'Stage 02',
    title: '增强输出',
    media_type: 'image',
    src: '/posters/enhanced-scene.svg',
  },
  {
    key: 'detected',
    step: 'Stage 03',
    title: '检测输出',
    media_type: 'image',
    src: '/posters/detected-scene.svg',
  },
]

const remotePanels = ref([])

const displayPanels = computed(() => {
  return fallbackPanels.map((fallbackPanel, index) => {
    const panel = remotePanels.value[index] || {}
    const hasValidSrc = typeof panel.src === 'string' && panel.src.trim() !== ''
    const mediaType = panel.media_type === 'video' && hasValidSrc ? 'video' : fallbackPanel.media_type
    return {
      key: panel.key || fallbackPanel.key || `stage-${index + 1}`,
      step: panel.step || fallbackPanel.step || `Stage 0${index + 1}`,
      title: panel.title || fallbackPanel.title || '',
      kind: mediaType,
      tag: mediaType === 'video' ? 'video' : 'img',
      mediaSrc: resolveMedia(hasValidSrc ? panel.src : fallbackPanel.src),
      mediaProps:
        mediaType === 'video'
          ? { autoplay: true, muted: true, loop: true, playsinline: true, preload: 'metadata', controls: true }
          : { alt: panel.title || fallbackPanel.title || '' },
    }
  })
})

const rawPanel = computed(() => displayPanels.value[0] || fallbackPanels[0])
const detectedPanel = computed(() => displayPanels.value[2] || fallbackPanels[2])

function resolveMedia(src) {
  if (!src) return ''
  if (src.startsWith('/posters/')) return src
  return resolveAssetUrl(src)
}

async function loadHomepageMedia() {
  try {
    remotePanels.value = await fetchHomepageMedia()
  } catch (_error) {
    remotePanels.value = []
  }
}

onMounted(() => {
  loadHomepageMedia()
})
</script>

<style scoped>
.home-page {
  display: grid;
  gap: clamp(18px, 2.5vw, 26px);
  max-width: 1320px;
  margin: 0 auto;
}

.home-hero {
  display: grid;
  grid-template-columns: minmax(280px, 0.68fr) minmax(400px, 1fr);
  gap: 0;
  align-items: stretch;
  min-height: min(calc(100svh - 168px), 820px);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 22px;
  background:
    linear-gradient(145deg, rgba(20, 184, 166, 0.14), transparent 42%),
    linear-gradient(320deg, rgba(56, 189, 248, 0.1), transparent 48%),
    rgba(6, 10, 20, 0.78);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--shadow);
}

.hero-copy {
  display: grid;
  align-content: center;
  justify-items: start;
  gap: clamp(16px, 2.5vw, 22px);
  padding: clamp(28px, 5vw, 56px);
  animation: copy-in 0.75s var(--ease-apple) both;
}

.hero-copy .section-tag {
  color: rgba(94, 234, 212, 0.9);
  font-weight: 600;
  letter-spacing: 0.16em;
}

.hero-copy h2 {
  margin: 0;
  max-width: 9em;
  color: #f8fafc;
  font-size: clamp(2.25rem, 6.2vw, 4.75rem);
  line-height: 1.02;
  letter-spacing: -0.03em;
  font-weight: 700;
}

.hero-lead {
  max-width: 28rem;
  margin: 0;
  color: rgba(203, 213, 225, 0.82);
  font-size: clamp(0.95rem, 1.35vw, 1.08rem);
  line-height: 1.75;
}

.hero-cta {
  margin-top: 4px;
  min-height: 48px;
  padding: 12px 28px;
  border-radius: 14px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.hero-media {
  min-height: 400px;
  animation: media-in 0.85s var(--ease-apple) 0.1s both;
}

.hero-media :deep(.comparison-stage) {
  height: 100%;
  min-height: 400px;
  border: 0;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0 22px 22px 0;
}

.capability-section,
.recipe-section,
.pipeline-panel {
  display: grid;
  gap: 20px;
  padding: clamp(22px, 3vw, 32px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  background: rgba(6, 10, 20, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.2);
}

.section-heading {
  display: grid;
  gap: 8px;
}

.section-heading.inline {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.status-pill {
  flex-shrink: 0;
  padding: 10px 16px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, 0.92);
  background: rgba(2, 6, 23, 0.5);
  border: 1px solid rgba(94, 234, 212, 0.22);
}

.section-heading .section-tag {
  color: rgba(94, 234, 212, 0.88);
  font-weight: 600;
}

.section-heading h3 {
  margin: 0;
  color: #f8fafc;
  font-size: clamp(1.45rem, 2.8vw, 2.15rem);
  letter-spacing: -0.02em;
  font-weight: 650;
}

.capability-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.capability-item,
.recipe-item,
.pipeline-card {
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  transition:
    transform 0.45s var(--ease-apple),
    border-color 0.3s ease,
    background 0.3s ease,
    box-shadow 0.35s ease;
}

.capability-item {
  display: grid;
  gap: 12px;
  padding: 22px;
}

.capability-item:hover,
.recipe-item:hover,
.pipeline-card:hover {
  transform: translateY(-3px);
  border-color: rgba(94, 234, 212, 0.28);
  background: rgba(255, 255, 255, 0.055);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
}

.capability-item span {
  display: grid;
  place-items: center;
  width: 44px;
  height: 32px;
  border-radius: 10px;
  color: #042f2e;
  background: linear-gradient(145deg, #ccfbf1, #5eead4);
  font-size: 0.76rem;
  font-weight: 800;
}

.capability-item h4,
.recipe-item h4,
.pipeline-copy h4 {
  margin: 0;
  color: rgba(248, 250, 252, 0.94);
  letter-spacing: 0;
}

.capability-item p,
.recipe-item p {
  margin: 0;
  color: rgba(203, 213, 225, 0.68);
  line-height: 1.7;
}

.recipe-list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.recipe-item {
  padding: 20px;
}

.recipe-item p {
  margin-top: 10px;
}

.pipeline-track {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.pipeline-card {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 14px;
  padding: 16px;
}

.pipeline-step {
  color: rgba(250, 204, 21, 0.88);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.pipeline-media {
  overflow: hidden;
  aspect-ratio: 16 / 10;
  min-height: 200px;
  border-radius: 14px;
  background: #020617;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.pipeline-asset {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.75s var(--ease-apple);
}

.pipeline-card:hover .pipeline-asset {
  transform: scale(1.04);
}

.pipeline-copy {
  text-align: center;
}

.pipeline-copy h4 {
  font-size: 0.95rem;
  font-weight: 650;
}

@keyframes copy-in {
  from {
    opacity: 0;
    transform: translateX(-16px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes media-in {
  from {
    opacity: 0;
    transform: scale(1.02);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 1080px) {
  .home-hero {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .hero-media :deep(.comparison-stage) {
    border-left: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 0 0 22px 22px;
  }

  .capability-grid,
  .recipe-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .home-hero {
    min-height: 0;
  }

  .hero-media,
  .hero-media :deep(.comparison-stage) {
    min-height: 320px;
  }

  .capability-grid,
  .recipe-list,
  .pipeline-track {
    grid-template-columns: 1fr;
  }

  .section-heading.inline {
    align-items: flex-start;
    flex-direction: column;
  }

  .capability-section,
  .recipe-section,
  .pipeline-panel {
    padding: 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-copy,
  .hero-media {
    animation: none;
  }

  .capability-item,
  .recipe-item,
  .pipeline-card,
  .pipeline-asset {
    transition: none;
  }

  .capability-item:hover,
  .recipe-item:hover,
  .pipeline-card:hover {
    transform: none;
  }
}
</style>
