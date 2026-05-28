<template>
  <div class="skeleton-chart" :style="{ height }">
    <!-- 模拟图例 -->
    <div class="skeleton-legend">
      <span class="skeleton-legend-item"></span>
      <span class="skeleton-legend-item"></span>
      <span class="skeleton-legend-item"></span>
    </div>
    <!-- 模拟 y 轴标签 -->
    <div class="skeleton-body">
      <div class="skeleton-y-labels">
        <span v-for="i in 5" :key="i" class="skeleton-y-label"></span>
      </div>
      <!-- 模拟折线区域 -->
      <div class="skeleton-chart-area">
        <svg viewBox="0 0 400 200" class="skeleton-svg">
          <!-- 网格线 -->
          <line
            v-for="i in 4"
            :key="'g' + i"
            x1="0"
            :y1="i * 50"
            x2="400"
            :y2="i * 50"
            stroke="rgba(255,255,255,0.04)"
            stroke-width="1"
          />
          <!-- 模拟折线 -->
          <path
            d="M0,160 Q50,150 80,120 T160,100 T240,130 T320,90 T400,70"
            fill="none"
            stroke="rgba(0,212,255,0.2)"
            stroke-width="3"
            class="skeleton-line"
          />
          <path
            d="M0,180 Q50,170 80,140 T160,120 T240,150 T320,110 T400,90"
            fill="none"
            stroke="rgba(251,191,36,0.15)"
            stroke-width="3"
            stroke-dasharray="6 4"
            class="skeleton-line"
          />
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  height: { type: String, default: "100%" },
});
</script>

<style scoped>
.skeleton-chart {
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  animation: skeleton-pulse 2s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.skeleton-legend {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-left: 8px;
}

.skeleton-legend-item {
  width: 70px;
  height: 14px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
}

.skeleton-body {
  flex: 1;
  display: flex;
  gap: 12px;
  min-height: 0;
}

.skeleton-y-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 4px 0;
  width: 40px;
  flex-shrink: 0;
}

.skeleton-y-label {
  height: 10px;
  width: 100%;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
}

.skeleton-chart-area {
  flex: 1;
  position: relative;
}

.skeleton-svg {
  width: 100%;
  height: 100%;
}

.skeleton-line {
  animation: skeleton-line-pulse 2.5s ease-in-out infinite;
}

@keyframes skeleton-line-pulse {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
