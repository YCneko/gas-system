<template>
  <div class="dashboard">
    <!-- ===== 顶部导航栏 ===== -->
    <header class="header">
      <div class="header-left">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
        </div>
        <div class="header-title-group">
          <h1 class="system-name">TVOC 智能监测预警系统</h1>
          <p class="subtitle">TVOC 实时监测与智能预警</p>
        </div>
      </div>
      <div class="header-right">
        <button class="export-btn" :disabled="exporting" @click="handleExport">
          {{ exporting ? "导出中..." : "📄 导出报告" }}
        </button>
        <span class="status-badge">● 运行中</span>
        <span class="clock">{{ currentTime }}</span>
      </div>
    </header>

    <!-- ===== 主体内容 ===== -->
    <main class="main-content">
      <!-- 左侧：实时指标卡片 -->
      <section class="left-panel">
        <DataCard
          v-for="item in indicators"
          :key="item.title"
          :title="item.title"
          :value="item.value"
          :unit="item.unit"
          :threshold="item.threshold"
        />

        <!-- 各组分浓度卡片 -->
        <div class="data-card components-card">
          <div class="card-header">
            <span class="card-title">各组分浓度</span>
          </div>
          <div class="components-grid">
            <div class="comp-item" v-for="comp in components" :key="comp.name">
              <div class="comp-header">
                <span class="comp-name">{{ comp.name }}</span>
                <span class="comp-number">
                  <span class="comp-value">{{ comp.value.toFixed(2) }}</span>
                  <span class="comp-unit">mg/m³</span>
                </span>
              </div>
              <div class="comp-bar">
                <div class="comp-fill" :style="{ width: comp.percentage + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧：预测图表 + 预警列表 -->
      <section class="right-panel">
        <div class="panel chart-panel">
          <div class="panel-header">
            <h3>VOCs 浓度预测趋势</h3>
            <span class="panel-meta">更新于 {{ latestUpdate }}</span>
          </div>
          <div class="chart-container">
            <PredictionChart :limit="100" />
          </div>
        </div>

        <div class="panel alert-panel">
          <div class="panel-header">
            <h3>预警信息列表</h3>
          </div>
          <div class="alert-container">
            <AlertList />
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import DataCard from "@/components/DataCard.vue";
import AlertList from "@/components/AlertList.vue";
import PredictionChart from "@/components/PredictionChart.vue";
import api from "@/utils/api";

// ========================
// 实时指标数据
// ========================
const indicators = ref([
  { title: "VOCs 浓度", value: 0, unit: "mg/m³", threshold: 100 },
  { title: "温度", value: 0, unit: "°C", threshold: 30 },
  { title: "湿度", value: 0, unit: "%", threshold: 70 },
  { title: "风速", value: 0, unit: "m/s", threshold: 2.0 },
]);

// 各组分浓度数据（HEXANE, TOLUENE, ACETONE）
const components = ref([
  { name: "HEXANE", value: 0, percentage: 0 },
  { name: "TOLUENE", value: 0, percentage: 0 },
  { name: "ACETONE", value: 0, percentage: 0 },
]);

const latestUpdate = ref("加载中...");
const currentTime = ref(new Date().toLocaleString());
const exporting = ref(false);

// ========================
// 实时数据轮询（每 5 秒）
// ========================
const fetchRealtimeData = async () => {
  try {
    const res = await api.getRealtimeData();
    indicators.value[0].value = res.voc ?? 0;
    indicators.value[1].value = res.temp ?? 0;
    indicators.value[2].value = res.humidity ?? 0;
    indicators.value[3].value = res.wind ?? 0;
    // 各组分浓度数据
    if (res.components) {
      components.value[0].value = res.components.hexane ?? 0;
      components.value[1].value = res.components.toluene ?? 0;
      components.value[2].value = res.components.acetone ?? 0;
    } else {
      // 如果没有嵌套对象，尝试从顶层字段获取
      components.value[0].value = res.hexane ?? 0;
      components.value[1].value = res.toluene ?? 0;
      components.value[2].value = res.acetone ?? 0;
    }
    // 计算百分比柱状图（阈值参考 200 mg/m³）
    components.value.forEach(c => {
      c.percentage = Math.min((c.value / 200) * 100, 100);
    });
    latestUpdate.value = new Date().toLocaleTimeString();
  } catch (err) {
    // 后端未就绪时使用模拟数据
    indicators.value[0].value = 0.85;
    indicators.value[1].value = 26.3;
    indicators.value[2].value = 68;
    indicators.value[3].value = 1.2;
    // 模拟组分数据
    components.value[0].value = 0.35;
    components.value[1].value = 0.12;
    components.value[2].value = 0.08;
    components.value.forEach(c => {
      c.percentage = Math.min((c.value / 200) * 100, 100);
    });
    latestUpdate.value = new Date().toLocaleTimeString();
  }
};

// ========================
// 导出报告
// ========================
const handleExport = async () => {
  exporting.value = true;
  try {
    const blob = await api.exportReport({ timestamp: Date.now() });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Gas监控报告_${new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/[:-]/g, "")}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("[Dashboard] 导出失败:", err);
    // 全局 Toast 已由 api.js 统一处理错误
  } finally {
    exporting.value = false;
  }
};

// ========================
// 生命周期
// ========================
let clockTimer = null;
let realtimeTimer = null;

onMounted(() => {
  clockTimer = setInterval(() => {
    currentTime.value = new Date().toLocaleString();
  }, 1000);

  fetchRealtimeData();
  realtimeTimer = setInterval(fetchRealtimeData, 5000);
});

onUnmounted(() => {
  clearInterval(clockTimer);
  clearInterval(realtimeTimer);
});
</script>

<style scoped>
/* ===== 全局重置 ===== */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.dashboard {
  height: 100%;
  display: grid;
  grid-template-rows: auto 1fr;
  background: linear-gradient(135deg, #0a0f1a 0%, #0d1422 100%);
  color: #e0e6f0;
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  overflow: hidden;
}

/* =====================================
   ===== 大屏 ≥1920px（默认） =====
   ===================================== */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 32px;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(46, 123, 207, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 10;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #1e3a8a, #00d4ff);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
  flex-shrink: 0;
}

.system-name {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(to right, #fff, #8bb9ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
}

.subtitle {
  font-size: 13px;
  color: #6c7a93;
  margin-top: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.status-badge {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid rgba(16, 185, 129, 0.3);
  white-space: nowrap;
}

.clock {
  font-size: 15px;
  font-weight: 500;
  color: #8b98b0;
  background: rgba(255, 255, 255, 0.05);
  padding: 8px 18px;
  border-radius: 8px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.export-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #00d4ff, #009cbb);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.15s;
  white-space: nowrap;
}
.export-btn:hover:not(:disabled) {
  opacity: 0.85;
  transform: translateY(-1px);
}
.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== 主体网格 ===== */
.main-content {
  display: grid;
  grid-template-columns: 35% 65%;
  gap: 24px;
  padding: 24px 32px;
  min-height: 0;
  overflow: hidden;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow-y: auto;
}

.right-panel {
  display: grid;
  grid-template-rows: 3fr 2fr;
  gap: 24px;
  min-height: 0;
}

/* ===== 面板 ===== */
.panel {
  background: rgba(18, 26, 46, 0.6);
  backdrop-filter: blur(6px);
  border-radius: 16px;
  border: 1px solid rgba(46, 123, 207, 0.15);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.panel-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #cdd6f0;
}

.panel-meta {
  font-size: 13px;
  color: #576580;
}

.chart-panel .chart-container {
  flex: 1;
  min-height: 0;
  padding: 4px 16px 12px;
}

.alert-panel .alert-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.alert-container::-webkit-scrollbar {
  width: 5px;
}
.alert-container::-webkit-scrollbar-track {
  background: transparent;
}
.alert-container::-webkit-scrollbar-thumb {
  background: #2e3a56;
  border-radius: 10px;
}

/* ===== 各组分浓度卡片 ===== */
.components-card {
  flex-shrink: 0;
}

.components-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 4px;
}

.comp-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.comp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.comp-name {
  font-size: 13px;
  font-weight: 600;
  color: #cdd6f0;
  letter-spacing: 0.5px;
}

.comp-number {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.comp-value {
  font-size: 20px;
  font-weight: 700;
  color: #00d4ff;
  font-variant-numeric: tabular-nums;
}

.comp-unit {
  font-size: 11px;
  color: #6b7a94;
}

/* 进度条 */
.comp-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.comp-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #00d4ff, #009cbb);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 0;
}

/* =====================================
   ===== 笔记本 1366-1919px =====
   ===================================== */
@media (max-width: 1919px) {
  .header {
    padding: 14px 24px;
  }

  .system-name {
    font-size: 22px;
  }

  .header-right {
    gap: 14px;
  }

  .status-badge {
    padding: 4px 12px;
    font-size: 13px;
  }

  .clock {
    font-size: 14px;
    padding: 6px 14px;
  }

  .export-btn {
    padding: 6px 16px;
    font-size: 13px;
  }

  .main-content {
    grid-template-columns: 30% 70%;
    gap: 20px;
    padding: 20px 24px;
  }

  .left-panel {
    gap: 14px;
  }

  .right-panel {
    gap: 20px;
  }

  .panel-header {
    padding: 14px 18px;
  }

  .panel-header h3 {
    font-size: 14px;
  }

  .chart-panel .chart-container {
    padding: 2px 12px 10px;
  }

  .comp-value {
    font-size: 17px;
  }
}

/* =====================================
   ===== 小屏 ≤1365px =====
   ===================================== */
@media (max-width: 1365px) {
  .header {
    padding: 10px 16px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .header-title-group {
    min-width: 0;
  }

  .system-name {
    font-size: 18px;
    white-space: normal;
    -webkit-text-fill-color: #fff;
    background: none;
  }

  .subtitle {
    font-size: 12px;
  }

  .logo-icon {
    width: 38px;
    height: 38px;
  }

  .logo-icon svg {
    width: 22px;
    height: 22px;
  }

  .header-right {
    gap: 10px;
    flex-wrap: wrap;
  }

  .status-badge {
    font-size: 12px;
    padding: 3px 10px;
  }

  .clock {
    font-size: 13px;
    padding: 4px 12px;
  }

  .export-btn {
    font-size: 12px;
    padding: 5px 14px;
  }

  .main-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
    gap: 16px;
    padding: 16px;
  }

  /* 4 张卡片排成 2×2 网格 */
  .left-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    overflow: visible;
  }

  .right-panel {
    grid-template-rows: 300px 200px;
    gap: 16px;
  }

  .panel-header {
    padding: 12px 16px;
  }

  .panel-header h3 {
    font-size: 13px;
  }

  .panel-meta {
    font-size: 12px;
  }

  .chart-panel .chart-container {
    padding: 0 8px 8px;
  }

  .alert-container {
    font-size: 13px;
  }

  th,
  td {
    padding: 8px 10px;
  }

  .components-card {
    grid-column: 1 / -1;
  }

  .comp-value {
    font-size: 18px;
  }
}

/* 极小屏处理 */
@media (max-width: 768px) {
  .left-panel {
    grid-template-columns: 1fr;
  }

  .right-panel {
    grid-template-rows: 240px 160px;
  }

  .header-right .status-badge,
  .header-right .clock {
    display: none;
  }

  .comp-value {
    font-size: 16px;
  }
}
</style>
