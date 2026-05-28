<template>
  <!-- 全局 UI 组件 -->
  <AppLoadingBar />
  <AppToast />
  <AppOfflineNotice />

  <!-- 导航栏 -->
  <nav class="app-nav">
    <router-link to="/" class="nav-link" exact-active-class="nav-active">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
        <polyline points="9 22 9 12 15 12 15 22"></polyline>
      </svg>
      监控看板
    </router-link>
    <router-link to="/about" class="nav-link" active-class="nav-active">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      关于
    </router-link>
  </nav>

  <!-- 页面切换过渡动画 -->
  <router-view v-slot="{ Component, route }">
    <Transition name="page" mode="out-in">
      <component :is="Component" :key="route.path" />
    </Transition>
  </router-view>
</template>

<script setup>
import AppLoadingBar from "@/components/AppLoadingBar.vue";
import AppToast from "@/components/AppToast.vue";
import AppOfflineNotice from "@/components/AppOfflineNotice.vue";
</script>

<style>
/* ===== 全局样式 ===== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  overflow: hidden;
}

body {
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #0a0f1a;
  color: #e0e6f0;
}

#app {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* ===== 导航栏 ===== */
.app-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 24px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(46, 123, 207, 0.15);
  z-index: 100;
  flex-shrink: 0;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  color: #6b7a94;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: #cdd6f0;
  background: rgba(255, 255, 255, 0.05);
}

.nav-active {
  color: #00d4ff !important;
  background: rgba(0, 212, 255, 0.08);
}

/* ===== 页面过渡动画 ===== */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
