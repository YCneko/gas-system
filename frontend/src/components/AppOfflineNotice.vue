<template>
  <Transition name="slide-down">
    <div v-if="store.offline" class="offline-banner">
      <span class="offline-icon">📡</span>
      <span>网络已断开，部分功能可能不可用</span>
      <button class="offline-retry" @click="checkConnection">重试</button>
    </div>
  </Transition>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import { store, setOffline } from "@/utils/globalState";

const handleOnline = () => setOffline(false);
const handleOffline = () => setOffline(true);

function checkConnection() {
  setOffline(!navigator.onLine);
}

onMounted(() => {
  setOffline(!navigator.onLine);
  window.addEventListener("online", handleOnline);
  window.addEventListener("offline", handleOffline);
});

onUnmounted(() => {
  window.removeEventListener("online", handleOnline);
  window.removeEventListener("offline", handleOffline);
});
</script>

<style scoped>
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #7f1d1d, #991b1b);
  color: #fecaca;
  font-size: 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.offline-icon {
  font-size: 18px;
}

.offline-retry {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fecaca;
  padding: 4px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.offline-retry:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* Transition */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
