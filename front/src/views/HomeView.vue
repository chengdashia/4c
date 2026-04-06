<template>
  <section class="home-page">
    <section id="pipeline-overview" class="pipeline-panel card-surface">
      <div class="panel-header premium">
        <div>
          <p class="section-tag">Pipeline Overview</p>
        </div>
        <div class="pipeline-actions">
          <span class="status-pill">Input → Enhance → Detect</span>
        </div>
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
import { fetchHomepageMedia, resolveAssetUrl } from '../services/api'

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
      tag: mediaType === 'video' ? 'video' : 'img',
      mediaSrc: resolveMedia(hasValidSrc ? panel.src : fallbackPanel.src),
      mediaProps: mediaType === 'video'
        ? { autoplay: true, muted: true, loop: true, playsinline: true, controls: true }
        : { alt: panel.title || fallbackPanel.title || '' },
    }
  })
})

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

.pipeline-copy h4 {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 500;
  letter-spacing: -0.02em;
  color: rgba(248, 250, 252, 0.92);
}

.pipeline-track {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.pipeline-card {
  display: grid;
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
}

.pipeline-media {
  overflow: hidden;
  border-radius: 18px;
  aspect-ratio: 4 / 3;
  background: rgba(2, 6, 23, 0.65);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05) inset;
}

.pipeline-asset {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #020617;
  transform: scale(1.001);
  transition: transform 0.85s cubic-bezier(0.16, 1, 0.3, 1);
}

.pipeline-card:hover .pipeline-asset {
  transform: scale(1.045);
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
}

@media (prefers-reduced-motion: reduce) {
  .panel-header.premium,
  .pipeline-card {
    animation: none;
  }

  .pipeline-card,
  .pipeline-asset {
    transition: none;
  }

  .pipeline-card:hover {
    transform: none;
  }

  .pipeline-card:hover .pipeline-asset {
    transform: none;
  }
}
</style>
