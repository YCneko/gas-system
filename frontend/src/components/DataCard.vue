<template>
  <div class="data-card" :class="{ 'is-exceed': isExceed }">
    <div class="card-header">
      <span class="card-title">{{ title }}</span>
      <!-- 阈值超标指示点 -->
      <span v-if="isExceed" class="exceed-badge">超标</span>
    </div>
    <div class="card-body">
      <span class="card-value" :key="value">
        {{ formattedValue }}
      </span>
      <span class="card-unit">{{ unit }}</span>
    </div>
    <div class="card-footer">
      <span v-if="threshold !== undefined" class="threshold-label">
        阈值 {{ threshold }}{{ unit }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  value: { type: Number, required: true },
  unit: { type: String, default: "" },
  threshold: { type: Number, default: undefined },
});

/** 是否超过阈值 */
const isExceed = computed(() => {
  if (props.threshold === undefined) return false;
  return props.value > props.threshold;
});

/** 保留两位小数 */
const formattedValue = computed(() => {
  return Number(props.value).toFixed(2);
});
</script>

<style scoped>
.data-card {
  position: relative;
  background: rgba(21, 35, 66, 0.8);
  border-radius: 16px;
  padding: 18px 22px 16px;
  color: #fff;
  border: 2px solid rgba(46, 123, 207, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition:
    border-color 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.4s ease,
    transform 0.2s ease;
  backdrop-filter: blur(6px);
}

.data-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0, 212, 255, 0.2);
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
  color: #9aa4bf;
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
  color: #00d4ff;
  text-shadow: 0 0 12px rgba(0, 212, 255, 0.3);
  transition:
    color 0.4s ease,
    transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: inline-block;
}

/* 超过阈值 → 数值变红 */
.data-card.is-exceed .card-value {
  color: #f87171;
  text-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
}

.card-unit {
  font-size: 18px;
  font-weight: 500;
  color: #6b7a94;
}

/* ---------- 底部 ---------- */
.card-footer {
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.threshold-label {
  font-size: 12px;
  color: #576580;
}
</style>
