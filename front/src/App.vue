<template>
  <div class="app-shell">
    <div class="app-backdrop">
      <span class="backdrop-orb orb-left"></span>
      <span class="backdrop-orb orb-right"></span>
      <span class="backdrop-grid"></span>
    </div>

    <header class="topbar">
      <div class="brand-block">
        <div class="brand-mark">WX</div>
        <div>
          <p class="eyebrow">Weather Vision Pipeline</p>
          <h1>复杂天气感知展示系统</h1>
        </div>
      </div>

      <nav class="topbar-nav">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/demo">功能展示</RouterLink>
      </nav>
    </header>

    <main class="page-shell">
      <RouterView v-slot="{ Component }">
        <Transition name="route-soft" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>
