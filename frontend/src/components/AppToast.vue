<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast" tag="div">
        <div
          v-for="toast in store.toasts"
          :key="toast.id"
          :class="['toast-item', toast.type]"
        >
          <span class="toast-icon">{{ iconMap[toast.type] }}</span>
          <span class="toast-msg">{{ toast.message }}</span>
          <button class="toast-close" @click="removeToast(toast.id)">&times;</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { store, removeToast } from "@/utils/globalState";

const iconMap = {
  success: "✅",
  error: "❌",
  warning: "⚠️",
  info: "ℹ️",
};
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 420px;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  color: #e0e6f0;
  font-size: 14px;
  backdrop-filter: blur(8px);
  min-width: 280px;
  word-break: break-word;
}

.toast-item.error {
  border-left: 4px solid #ef4444;
}

.toast-item.success {
  border-left: 4px solid #10b981;
}

.toast-item.warning {
  border-left: 4px solid #e6a23c;
}

.toast-item.info {
  border-left: 4px solid #409eff;
}

.toast-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.toast-msg {
  flex: 1;
  line-height: 1.5;
}

.toast-close {
  background: none;
  border: none;
  color: #6b7a94;
  font-size: 20px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
  flex-shrink: 0;
}

.toast-close:hover {
  color: #e0e6f0;
}

/* TransitionGroup 动画 */
.toast-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-leave-active {
  transition: all 0.25s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(80px) scale(0.9);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(80px) scale(0.9);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
