<template>
  <div class="loading-bar-container">
    <div
      class="loading-bar"
      :class="{ visible: active, exiting: exiting }"
    ></div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { store } from "@/utils/globalState";

const active = ref(false);
const exiting = ref(false);
let exitTimer = null;

watch(
  () => store.activeRequests,
  (val) => {
    if (exitTimer) {
      clearTimeout(exitTimer);
      exitTimer = null;
    }
    if (val > 0) {
      active.value = true;
      exiting.value = false;
    } else {
      // 所有请求完成 → 先标记 exiting 播放消失动画
      exiting.value = true;
      exitTimer = setTimeout(() => {
        active.value = false;
        exiting.value = false;
      }, 400);
    }
  },
);
</script>

<style scoped>
.loading-bar-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 9999;
  pointer-events: none;
}

.loading-bar {
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, #00d4ff, #7c3aed, #00d4ff);
  background-size: 200% 100%;
  border-radius: 0 2px 2px 0;
  opacity: 0;
  transition: width 0.3s ease, opacity 0.3s ease;
}

.loading-bar.visible {
  opacity: 1;
  width: 80%;
  animation: bar-slide 1.5s ease-in-out infinite;
}

.loading-bar.exiting {
  width: 100%;
  opacity: 0;
  transition: width 0.3s ease, opacity 0.4s ease 0.1s;
}

@keyframes bar-slide {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
