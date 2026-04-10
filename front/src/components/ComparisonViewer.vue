<template>
  <div class="comparison-viewer">
    <div
      ref="containerRef"
      class="comparison-stage"
      @pointerdown="startDrag"
      @pointermove="onDrag"
      @pointerup="stopDrag"
      @pointerleave="stopDrag"
    >
      <div v-if="beforeSrc || afterSrc" class="comparison-media">
        <div class="comparison-layer base-layer">
          <component
            :is="beforeTag"
            ref="beforeMediaRef"
            v-if="beforeSrc"
            :key="`${beforeTag}:${beforeSrc}`"
            :src="beforeSrc"
            class="comparison-asset"
            :controls="beforeTag === 'video'"
            autoplay
            muted
            loop
            playsinline
            preload="metadata"
            @loadedmetadata="syncFromBefore"
            @play="syncFromBefore"
            @pause="syncFromBefore"
            @seeking="syncFromBefore"
            @timeupdate="syncFromBefore"
          />
          <div v-else class="comparison-empty">等待基准画面</div>
        </div>

        <div class="comparison-layer reveal-layer" :style="{ clipPath: `inset(0 0 0 ${position}%)` }">
          <component
            :is="afterTag"
            ref="afterMediaRef"
            v-if="afterSrc"
            :key="`${afterTag}:${afterSrc}`"
            :src="afterSrc"
            class="comparison-asset"
            :controls="afterTag === 'video'"
            autoplay
            muted
            loop
            playsinline
            preload="metadata"
            @loadedmetadata="syncFromBefore"
          />
          <div v-else class="comparison-empty">等待处理结果</div>
        </div>

        <div class="comparison-divider" :style="{ left: `${position}%` }">
          <span class="comparison-handle">↔</span>
        </div>

        <div class="comparison-labels">
          <span>{{ beforeLabel }}</span>
          <span>{{ afterLabel }}</span>
        </div>
      </div>

      <div v-else class="comparison-placeholder">
        <div class="placeholder-orb"></div>
        <p>{{ emptyText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  beforeSrc: { type: String, default: '' },
  afterSrc: { type: String, default: '' },
  beforeKind: { type: String, default: 'image' },
  afterKind: { type: String, default: 'image' },
  beforeLabel: { type: String, default: 'Before' },
  afterLabel: { type: String, default: 'After' },
  emptyText: { type: String, default: '等待内容' },
})

const containerRef = ref(null)
const beforeMediaRef = ref(null)
const afterMediaRef = ref(null)
const position = ref(52)
const dragging = ref(false)
const syncing = ref(false)

const beforeTag = computed(() => (props.beforeKind === 'video' ? 'video' : 'img'))
const afterTag = computed(() => (props.afterKind === 'video' ? 'video' : 'img'))
const isVideoComparison = computed(() => beforeTag.value === 'video' && afterTag.value === 'video')

function updatePosition(event) {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  if (!rect.width) return
  const next = ((event.clientX - rect.left) / rect.width) * 100
  position.value = Math.min(100, Math.max(0, next))
}

function startDrag(event) {
  dragging.value = true
  event.currentTarget?.setPointerCapture?.(event.pointerId)
  updatePosition(event)
}

function onDrag(event) {
  if (!dragging.value) return
  updatePosition(event)
}

function stopDrag(event) {
  dragging.value = false
  event.currentTarget?.releasePointerCapture?.(event.pointerId)
}

function syncFromBefore() {
  if (!isVideoComparison.value || syncing.value) return

  const before = beforeMediaRef.value
  const after = afterMediaRef.value
  if (!before || !after) return

  syncing.value = true

  try {
    if (Math.abs((before.currentTime || 0) - (after.currentTime || 0)) > 0.08) {
      after.currentTime = before.currentTime || 0
    }

    if (before.paused) {
      after.pause()
    } else {
      const promise = after.play?.()
      if (promise?.catch) promise.catch(() => {})
    }
  } finally {
    window.requestAnimationFrame(() => {
      syncing.value = false
    })
  }
}

watch(
  () => [props.beforeSrc, props.afterSrc, props.beforeKind, props.afterKind],
  () => {
    if (isVideoComparison.value) {
      window.requestAnimationFrame(syncFromBefore)
    }
  },
)
</script>

<style scoped>
.comparison-viewer {
  width: 100%;
  height: 100%;
  min-height: 0;
  display: block;
}

.comparison-stage {
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 100%;
  min-height: 280px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background:
    radial-gradient(ellipse 100% 80% at 50% 0%, rgba(148, 163, 184, 0.12), transparent 50%),
    linear-gradient(180deg, rgba(9, 16, 28, 0.95), rgba(15, 23, 42, 0.82));
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05) inset;
  user-select: none;
  touch-action: none;
  transition:
    border-color 0.45s ease,
    box-shadow 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.comparison-stage:hover {
  border-color: rgba(255, 255, 255, 0.11);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.07) inset,
    0 0 48px rgba(56, 189, 248, 0.05);
}

.comparison-media,
.comparison-layer,
.comparison-asset,
.comparison-placeholder {
  width: 100%;
  height: 100%;
}

.comparison-media {
  position: absolute;
  inset: 0;
}

.comparison-layer {
  position: absolute;
  inset: 0;
}

.comparison-asset {
  display: block;
  object-fit: cover;
  background: #020617;
}

.comparison-empty,
.comparison-placeholder {
  display: grid;
  place-items: center;
  color: rgba(226, 232, 240, 0.7);
}

.comparison-placeholder {
  gap: 12px;
  padding: 28px;
  text-align: center;
}

.placeholder-orb {
  width: 108px;
  height: 108px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, rgba(110, 231, 255, 0.9), rgba(110, 231, 255, 0.08)),
    radial-gradient(circle at 72% 72%, rgba(251, 191, 36, 0.6), transparent 48%);
  filter: blur(2px);
  animation: compare-orb-pulse 6s ease-in-out infinite;
}

@keyframes compare-orb-pulse {
  0%,
  100% {
    opacity: 0.95;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.06);
  }
}

.comparison-placeholder p {
  animation: compare-fade-up 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both;
}

@keyframes compare-fade-up {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.comparison-divider {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 3px;
  margin-left: -0.5px;
  background: linear-gradient(
    180deg,
    rgba(253, 224, 71, 0.15) 0%,
    rgba(253, 224, 71, 0.95) 22%,
    rgba(250, 250, 250, 0.98) 50%,
    rgba(253, 224, 71, 0.95) 78%,
    rgba(253, 224, 71, 0.15) 100%
  );
  box-shadow:
    0 0 20px rgba(253, 224, 71, 0.35),
    0 0 1px rgba(0, 0, 0, 0.4);
  transform: translateX(-50%);
}

.comparison-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 999px;
  background: linear-gradient(180deg, #fafafa 0%, #e2e8f0 100%);
  color: #0f172a;
  font-weight: 700;
  transform: translate(-50%, -50%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 12px 32px rgba(2, 6, 23, 0.35),
    0 0 0 1px rgba(15, 23, 42, 0.08);
  transition:
    transform 0.4s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.comparison-stage:hover .comparison-handle {
  transform: translate(-50%, -50%) scale(1.06);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 16px 40px rgba(2, 6, 23, 0.4),
    0 0 0 1px rgba(125, 211, 252, 0.25);
}

.comparison-labels {
  position: absolute;
  right: 18px;
  bottom: 18px;
  left: 18px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.comparison-labels span {
  padding: 9px 14px;
  border-radius: 999px;
  background: rgba(12, 18, 32, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(248, 250, 252, 0.95);
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition:
    border-color 0.35s ease,
    background 0.35s ease;
}

.comparison-labels span:hover {
  border-color: rgba(255, 255, 255, 0.16);
  background: rgba(12, 18, 32, 0.68);
}

@media (prefers-reduced-motion: reduce) {
  .placeholder-orb,
  .comparison-placeholder p {
    animation: none;
  }

  .comparison-handle {
    transition: none;
  }

  .comparison-stage:hover .comparison-handle {
    transform: translate(-50%, -50%);
  }
}

@media (max-width: 760px) {
  .comparison-stage {
    min-height: 240px;
  }

  .comparison-handle {
    width: 42px;
    height: 42px;
  }

  .comparison-labels {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
