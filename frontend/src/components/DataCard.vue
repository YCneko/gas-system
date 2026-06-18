<template>
  <div class="data-card" :class="{ 'is-exceed': isExceed }">
    <div class="card-header">
      <span class="card-title">{{ title }}</span>
      <span v-if="isExceed" class="exceed-badge">超标</span>
    </div>
    <div class="card-body">
      <span class="card-value" :key="animateKey">
        {{ formattedValue }}
      </span>
      <span class="card-unit">{{ unit }}</span>
    </div>
    <div class="card-footer">
      <span v-if="threshold !== undefined" class="threshold-label">
        阈值 {{ threshold }}{{ unit }}
      </span>
      <span class="update-indicator" :class="{ active: animating }">
        {{ animating ? "更新中" : "" }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  value: { type: Number, required: true },
  unit: { type: String, default: "" },
  threshold: { type: Number, default: undefined },
});

// ========================
// 数字滚动动画
// ========================
const displayValue = ref(props.value);
const animating = ref(false);
const animateKey = ref(0);
let animId = null;

watch(
  () => props.value,
  (newVal, oldVal) => {
    if (animId) cancelAnimationFrame(animId);
    const start = oldVal ?? newVal;
    const diff = newVal - start;
    const duration = 400;
    const startTime = performance.now();

    animating.value = true;

    const tick = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      displayValue.value = start + diff * eased;
      animateKey.value++;
      if (progress < 1) {
        animId = requestAnimationFrame(tick);
      } else {
        animating.value = false;
      }
    };
    animId = requestAnimationFrame(tick);
  },
);

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId);
});

// ========================
// 计算属性
// ========================
const isExceed = computed(() => {
  if (props.threshold === undefined) return false;
  return displayValue.value > props.threshold;
});

const formattedValue = computed(() => {
  return Number(displayValue.value).toFixed(2);
});
</script>

<style scoped>
.data-card {
  position: relative;
  background: #ffffff;
  border-radius: 16px;
  padding: 18px 22px 16px;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition:
    border-color 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.4s ease,
    transform 0.2s ease;
}

.data-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.1);
}

/* ---------- 超过阈值 ---------- */
.data-card.is-exceed {
  border-color: #ef4444;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
  animation: pulse-border 1.5s ease-in-out infinite;
}

@keyframes pulse-border {
  0% {
    border-color: #ef4444;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
  }
  50% {
    border-color: #f87171;
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
  }
  100% {
    border-color: #ef4444;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
  }
}

/* ---------- 超标徽标 ---------- */
.exceed-badge {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid rgba(239, 68, 68, 0.3);
  animation: badge-pulse 1.5s ease-in-out infinite;
}

@keyframes badge-pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

/* ---------- 头部 ---------- */
.card-header {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ---------- 数值 ---------- */
.card-body {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 10px;
}

.card-value {
  font-size: 38px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #2563eb;
  display: inline-block;
  font-variant-numeric: tabular-nums;
  transition:
    color 0.4s ease;
}

/* 数值变化动画 */
.card-value {
  animation: value-pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes value-pop {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.08);
  }
  100% {
    transform: scale(1);
  }
}

/* 超过阈值 → 数值变红 */
.data-card.is-exceed .card-value {
  color: #f87171;
  text-shadow: 0 0 8px rgba(239, 68, 68, 0.15);
}

.card-unit {
  font-size: 18px;
  font-weight: 500;
  color: #94a3b8;
}

/* ---------- 底部 ---------- */
.card-footer {
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.threshold-label {
  font-size: 12px;
  color: #94a3b8;
}

.update-indicator {
  font-size: 11px;
  color: #2563eb;
  opacity: 0;
  transition: opacity 0.3s;
}

.update-indicator.active {
  opacity: 1;
}
</style>
