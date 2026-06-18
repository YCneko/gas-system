<template>
  <div class="training-page">
    <!-- ===== 页面头部 ===== -->
    <div class="page-header">
      <h1 class="page-title">🧠 模型训练与评估</h1>
      <p class="page-subtitle">基于 LSTM 的 TVOC 浓度预测模型</p>
      <span class="page-meta">最后更新：{{ lastUpdate }}</span>
    </div>

    <!-- ===== 上半部分：模型架构卡片 + 训练曲线图 ===== -->
    <div class="top-section">
      <!-- 左侧：模型架构卡片（35%） -->
      <div class="arch-card">
        <div class="card-header">
          <h2 class="card-title">模型架构</h2>
          <span class="card-badge">LSTM</span>
        </div>
        <div class="arch-details">
          <div class="arch-row">
            <span class="arch-label">架构类型</span>
            <span class="arch-value highlight">LSTM 2层 (128 → 64)</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">输出层</span>
            <span class="arch-value">Dense(6) — 未来6小时预测</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">参数量</span>
            <span class="arch-value param-count">~125,000</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">回看窗口</span>
            <span class="arch-value">24 小时</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">Dropout</span>
            <span class="arch-value">0.2</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">优化器</span>
            <span class="arch-value">Adam (lr=0.001)</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">损失函数</span>
            <span class="arch-value">MSE</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">训练样本</span>
            <span class="arch-value">4,332 条</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">训练时间</span>
            <span class="arch-value">~120 秒 (RTX 4060)</span>
          </div>
          <div class="arch-row">
            <span class="arch-label">特征维度</span>
            <span class="arch-value">14 维</span>
          </div>
        </div>
      </div>

      <!-- 右侧：训练曲线图（65%） -->
      <div class="chart-card">
        <div class="card-header">
          <h2 class="card-title">训练曲线</h2>
          <span class="card-meta">Loss 下降趋势 (100 Epochs)</span>
        </div>
        <div class="chart-container">
          <v-chart
            :option="chartOption"
            autoresize
            ref="chartRef"
          />
        </div>
      </div>
    </div>

    <!-- ===== 版本性能对比表格 ===== -->
    <div class="table-card">
      <div class="card-header">
        <h2 class="card-title">版本性能对比</h2>
        <span class="card-meta">不同训练策略的模型效果对比</span>
      </div>
      <div class="table-wrapper">
        <table class="version-table">
          <thead>
            <tr>
              <th>版本</th>
              <th>策略</th>
              <th>R²</th>
              <th>MAE</th>
              <th>MAPE</th>
              <th>RMSE</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="v in versions"
              :key="v.version"
              :class="{ 'is-current': v.isCurrent, 'is-failed': v.r2 < 0.1 }"
            >
              <td>
                <span class="ver-tag" :class="v.isCurrent ? 'ver-current' : ''">
                  {{ v.version }}
                </span>
              </td>
              <td class="strategy-cell">{{ v.strategy }}</td>
              <td>
                <span class="metric-value" :class="getR2Class(v.r2)">
                  {{ v.r2.toFixed(4) }}
                </span>
              </td>
              <td>{{ v.mae.toFixed(2) }}</td>
              <td>{{ v.mape }}</td>
              <td>{{ v.rmse.toFixed(1) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 当前生产版本标记 -->
      <div class="current-badge">
        <span class="badge-dot"></span>
        当前使用版本：V1 (生产)
      </div>
    </div>

    <!-- ===== 特征标签云 ===== -->
    <div class="feature-card">
      <div class="card-header">
        <h2 class="card-title">特征维度</h2>
        <span class="card-meta">共 {{ features.length }} 个输入特征</span>
      </div>
      <div class="feature-tags">
        <span
          v-for="(feat, idx) in features"
          :key="idx"
          class="feature-tag"
          :style="{ animationDelay: idx * 0.05 + 's' }"
        >
          {{ feat }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import VChart from "vue-echarts";
import api from "@/utils/api";

// ========== ECharts 按需引入 ==========
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
]);

// ========================
// 模拟数据生成函数
// ========================

/** 生成 100 个 epoch 的训练 / 验证 Loss 数据 */
const generateLossData = () => {
  const epochs = [];
  const trainLoss = [];
  const valLoss = [];
  for (let i = 1; i <= 100; i++) {
    epochs.push(i);
    // 指数衰减曲线：从 ~0.5 快速下降到 ~0.02
    const decay = Math.exp(-i / 18);
    const base = 0.03 + 0.47 * decay;
    // 添加逐渐减小的随机噪声
    const noiseScale = 0.006 + 0.012 * decay;
    const trainNoise = (Math.random() - 0.5) * noiseScale;
    const valNoise = (Math.random() - 0.3) * noiseScale * 1.4;

    trainLoss.push(Math.max(0.01, +(base + trainNoise).toFixed(6)));
    valLoss.push(Math.max(0.01, +(base + 0.012 + valNoise).toFixed(6)));
  }
  return { epochs, trainLoss, valLoss };
};

// ========================
// 响应式状态
// ========================

const chartRef = ref(null);
const lastUpdate = ref("加载中...");

// 模型架构信息（默认用硬编码数据）
const archInfo = ref({
  arch: "LSTM 2层 (128 → 64)",
  output: "Dense(6) — 未来6小时预测",
  params: "~125,000",
  window: "24 小时",
  dropout: "0.2",
  optimizer: "Adam (lr=0.001)",
  loss: "MSE",
  samples: "4,332 条",
  trainTime: "~120 秒 (RTX 4060)",
  featureDim: "14 维",
});

// 版本对比数据（默认用硬编码数据）
const versions = ref([
  {
    version: "V1 (生产)",
    strategy: "MSE + 24步 + 14特征",
    r2: 0.9217,
    mae: 8.11,
    mape: "46.49%",
    rmse: 14.5,
    isCurrent: true,
  },
  {
    version: "V2",
    strategy: "MAE + 48步 + BN + 18特征",
    r2: 0.914,
    mae: 8.48,
    mape: "40.10%",
    rmse: 16.2,
    isCurrent: false,
  },
  {
    version: "V3",
    strategy: "Weighted MAE + CosineLR",
    r2: 0.0449,
    mae: 27.0,
    mape: "70.42%",
    rmse: 38.1,
    isCurrent: false,
  },
]);

// 特征列表
const features = ref([
  "temperature",
  "humidity",
  "wind_speed",
  "operating_load",
  "hour_sin",
  "hour_cos",
  "day_of_week_sin",
  "day_of_week_cos",
  "is_workday",
  "voc_lag_1h",
  "voc_lag_3h",
  "voc_lag_6h",
  "voc_rolling_6h_mean",
  "voc_rolling_6h_std",
]);

// 训练曲线数据
const lossData = ref(generateLossData());

// ========================
// ECharts 图表配置（亮色主题）
// ========================
const chartOption = computed(() => {
  const { epochs, trainLoss, valLoss } = lossData.value;

  return {
    animation: true,
    animationDuration: 600,
    animationEasing: "cubicOut",

    // 亮色主题背景
    backgroundColor: "transparent",

    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255, 255, 255, 0.96)",
      borderColor: "#e2e8f0",
      textStyle: { color: "#1e293b", fontSize: 13 },
      boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
      formatter: (params) => {
        let html = `<div style="font-weight:600;margin-bottom:6px;color:#1e293b;">Epoch ${params[0].axisValue}</div>`;
        params.forEach((p) => {
          html += `<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color};"></span>
            ${p.seriesName}: <strong>${p.value.toFixed(6)}</strong>
          </div>`;
        });
        return html;
      },
    },

    legend: {
      data: ["训练 Loss", "验证 Loss"],
      textStyle: { color: "#64748b", fontSize: 13 },
      top: 8,
      icon: "roundRect",
      itemWidth: 20,
      itemHeight: 4,
    },

    grid: {
      top: 55,
      right: 35,
      bottom: 50,
      left: 65,
    },

    xAxis: {
      type: "category",
      data: epochs,
      name: "Epoch",
      nameTextStyle: { color: "#64748b", fontSize: 12 },
      nameLocation: "middle",
      nameGap: 35,
      axisLabel: {
        color: "#94a3b8",
        fontSize: 11,
        interval: 9,
      },
      axisLine: { lineStyle: { color: "#e2e8f0" } },
      axisTick: { show: false },
      splitLine: { show: false },
    },

    yAxis: {
      type: "value",
      name: "Loss",
      nameTextStyle: { color: "#64748b", fontSize: 12 },
      axisLabel: {
        color: "#94a3b8",
        fontSize: 11,
        formatter: (v) => v.toFixed(2),
      },
      splitLine: {
        lineStyle: { color: "#f1f5f9", type: "dashed" },
      },
      // 对数尺度可选项（默认线性）
      // type: "log",
    },

    series: [
      // 训练 Loss（蓝色实线）
      {
        name: "训练 Loss",
        type: "line",
        data: trainLoss,
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#2563eb", width: 2.5 },
        itemStyle: { color: "#2563eb" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(37, 99, 235, 0.12)" },
              { offset: 1, color: "rgba(37, 99, 235, 0.01)" },
            ],
          },
        },
      },
      // 验证 Loss（橙色虚线）
      {
        name: "验证 Loss",
        type: "line",
        data: valLoss,
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#f59e0b", width: 2.5, type: "dashed" },
        itemStyle: { color: "#f59e0b" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(245, 158, 11, 0.08)" },
              { offset: 1, color: "rgba(245, 158, 11, 0.01)" },
            ],
          },
        },
      },
    ],
  };
});

// ========================
// 辅助函数
// ========================

/** 根据 R² 值返回颜色类名 */
const getR2Class = (r2) => {
  if (r2 >= 0.9) return "metric-good";
  if (r2 >= 0.5) return "metric-ok";
  return "metric-bad";
};

// ========================
// 数据获取（API / Fallback）
// ========================
const fetchModelData = async () => {
  let apiReady = false;
  try {
    // 尝试从后端获取模型信息与指标数据（方法将由 Agent #3 添加）
    const info = await api.getTrainingInfo?.();
    const metrics = await api.getModelMetrics?.();
    if (info) {
      archInfo.value = { ...archInfo.value, ...info };
      apiReady = true;
    }
    if (metrics && Array.isArray(metrics)) {
      versions.value = metrics.map((m, i) => ({
        version: m.version || `V${i + 1}`,
        strategy: m.strategy || "-",
        r2: m.r2 ?? 0,
        mae: m.mae ?? 0,
        mape: m.mape ?? "-",
        rmse: m.rmse ?? 0,
        isCurrent: i === 0,
      }));
      apiReady = true;
    }
  } catch (err) {
    console.log("[TrainingView] API 未就绪，使用本地模拟数据");
  }

  if (!apiReady) {
    // 使用硬编码的模拟数据（已设为默认值，无需额外操作）
    // 重新生成一次 Loss 数据以获得随机的视觉变化
    lossData.value = generateLossData();
  }

  lastUpdate.value = new Date().toLocaleTimeString();
};

// ========================
// 生命周期
// ========================
onMounted(() => {
  fetchModelData();
});
</script>

<style scoped>
/* ===== 页面整体 ===== */
.training-page {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 24px 32px;
  background: #f0f4f8;
}

/* 滚动条 */
.training-page::-webkit-scrollbar {
  width: 6px;
}
.training-page::-webkit-scrollbar-track {
  background: transparent;
}
.training-page::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

/* ===== 页面头部 ===== */
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: 0.5px;
}

.page-subtitle {
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

.page-meta {
  display: inline-block;
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
  background: #ffffff;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
}

/* ===== 上半部分：左右两栏 ===== */
.top-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

/* ===== 通用卡片样式 ===== */
.arch-card,
.chart-card,
.table-card,
.feature-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s ease;
}

.arch-card:hover,
.chart-card:hover,
.table-card:hover,
.feature-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px 14px;
  border-bottom: 1px solid #f1f5f9;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.card-badge {
  font-size: 12px;
  font-weight: 600;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.08);
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid rgba(37, 99, 235, 0.15);
}

.card-meta {
  font-size: 13px;
  color: #94a3b8;
}

/* ===== 模型架构卡片 ===== */
.arch-card {
  flex: 0 0 35%;
  display: flex;
  flex-direction: column;
}

.arch-details {
  padding: 16px 22px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.arch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid #f8fafc;
}

.arch-row:last-child {
  border-bottom: none;
}

.arch-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.arch-value {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
}

.arch-value.highlight {
  color: #2563eb;
  font-weight: 600;
}

.param-count {
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
  background: #f8fafc;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #2563eb;
}

/* ===== 训练曲线卡片 ===== */
.chart-card {
  flex: 0 0 calc(65% - 20px);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-container {
  flex: 1;
  min-height: 380px;
  padding: 8px 16px 12px;
}

/* ===== 版本对比表格 ===== */
.table-card {
  margin-bottom: 20px;
}

.table-wrapper {
  overflow-x: auto;
  padding: 4px 22px 16px;
}

.version-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.version-table thead th {
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
  font-size: 13px;
  padding: 12px 16px;
  text-align: left;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
}

.version-table thead th:first-child {
  border-radius: 8px 0 0 0;
}

.version-table thead th:last-child {
  border-radius: 0 8px 0 0;
}

.version-table tbody td {
  padding: 13px 16px;
  color: #334155;
  border-bottom: 1px solid #f1f5f9;
  white-space: nowrap;
}

.version-table tbody tr:hover {
  background: #f8fafc;
}

/* 当前版本行高亮 */
.version-table tbody tr.is-current {
  background: rgba(37, 99, 235, 0.04);
}

.version-table tbody tr.is-current:hover {
  background: rgba(37, 99, 235, 0.07);
}

/* V3 失败行淡化 */
.version-table tbody tr.is-failed {
  opacity: 0.6;
}

.version-table tbody tr.is-failed:hover {
  opacity: 0.85;
}

/* 版本标签 */
.ver-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #475569;
}

.ver-tag.ver-current {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}

/* 策略列 */
.strategy-cell {
  max-width: 220px;
  white-space: normal !important;
  word-break: break-word;
  font-size: 13px;
  color: #475569;
}

/* 指标值颜色 */
.metric-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.metric-good {
  color: #16a34a;
}

.metric-ok {
  color: #d97706;
}

.metric-bad {
  color: #dc2626;
}

/* 当前版本标记 */
.current-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px 16px;
  font-size: 13px;
  color: #64748b;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 0 6px rgba(37, 99, 235, 0.4);
}

/* ===== 特征标签云 ===== */
.feature-card {
  margin-bottom: 24px;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 18px 22px 22px;
}

.feature-tag {
  display: inline-block;
  font-size: 13px;
  font-weight: 500;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.05);
  border: 1px solid rgba(37, 99, 235, 0.15);
  padding: 6px 14px;
  border-radius: 20px;
  font-family: "SF Mono", "Fira Code", "Consolas", "Menlo", monospace;
  transition: all 0.25s ease;
  cursor: default;
  animation: tag-fade-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.feature-tag:hover {
  background: rgba(37, 99, 235, 0.12);
  border-color: rgba(37, 99, 235, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12);
}

@keyframes tag-fade-in {
  from {
    opacity: 0;
    transform: translateY(6px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* =====================================
   ===== 中等屏幕 1366-1919px =====
   ===================================== */
@media (max-width: 1919px) {
  .training-page {
    padding: 20px 24px;
  }

  .page-title {
    font-size: 24px;
  }

  .top-section {
    gap: 16px;
  }

  .arch-card {
    flex: 0 0 38%;
  }

  .chart-card {
    flex: 0 0 calc(62% - 16px);
  }

  .chart-container {
    min-height: 320px;
  }

  .card-header {
    padding: 14px 18px 12px;
  }

  .arch-details {
    padding: 12px 18px 16px;
    gap: 8px;
  }

  .arch-label,
  .arch-value {
    font-size: 12px;
  }

  .version-table thead th,
  .version-table tbody td {
    padding: 10px 14px;
    font-size: 13px;
  }
}

/* =====================================
   ===== 小屏 ≤1365px =====
   ===================================== */
@media (max-width: 1365px) {
  .training-page {
    padding: 16px;
  }

  .page-title {
    font-size: 21px;
  }

  .page-subtitle {
    font-size: 13px;
  }

  /* 左右布局变为上下堆叠 */
  .top-section {
    flex-direction: column;
    gap: 16px;
  }

  .arch-card {
    flex: none;
  }

  .chart-card {
    flex: none;
  }

  .chart-container {
    min-height: 300px;
  }

  .arch-details {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 16px;
  }

  .arch-row {
    padding: 5px 0;
  }

  .card-header {
    padding: 12px 16px 10px;
  }

  .card-title {
    font-size: 14px;
  }

  .version-table thead th,
  .version-table tbody td {
    padding: 8px 12px;
    font-size: 12px;
  }

  .feature-tags {
    gap: 8px;
    padding: 14px 16px 18px;
  }

  .feature-tag {
    font-size: 12px;
    padding: 5px 10px;
  }
}

/* =====================================
   ===== 极小屏 ≤768px =====
   ===================================== */
@media (max-width: 768px) {
  .page-title {
    font-size: 18px;
  }

  .arch-details {
    grid-template-columns: 1fr;
  }

  .chart-container {
    min-height: 240px;
  }

  .table-wrapper {
    padding: 4px 12px 12px;
  }

  .version-table {
    font-size: 11px;
  }

  .version-table thead th,
  .version-table tbody td {
    padding: 7px 10px;
  }
}
</style>
