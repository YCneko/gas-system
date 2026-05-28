<template>
  <div class="chart-wrapper" :style="{ height }">
    <!-- 骨架屏（加载态） -->
    <SkeletonChart v-if="loading" :height="height" />

    <!-- 图表（就绪态） -->
    <v-chart
      v-else
      :option="chartOption"
      autoresize
      ref="chartRef"
    />

    <!-- 错误态 -->
    <div v-if="error" class="chart-error">
      <span>⚠️ 图表加载失败</span>
      <button class="chart-retry" @click="retry">重试</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";
import VChart from "vue-echarts";
import SkeletonChart from "@/components/SkeletonChart.vue";
import api from "@/utils/api";

// ========== ECharts 按需引入 ==========
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
} from "echarts/components";

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
]);

const props = defineProps({
  limit: { type: Number, default: 80 },
  limitColor: { type: String, default: "#ef4444" },
  height: { type: String, default: "100%" },
});

const chartRef = ref(null);
const historyData = ref([]);
const predictionData = ref([]);
const loading = ref(true);
const error = ref(false);

// ========================
// 获取预测数据
// ========================
const fetchData = async () => {
  if (!error.value) loading.value = true;
  try {
    const res = await api.getPrediction();
    historyData.value = res.history || [];
    predictionData.value = res.prediction || [];
    error.value = false;
  } catch (err) {
    console.error("[PredictionChart] 获取预测数据失败:", err);
    error.value = true;
  } finally {
    loading.value = false;
  }
};

const retry = () => {
  error.value = false;
  fetchData();
};

// ========================
// 构建 ECharts 配置
// ========================
const chartOption = computed(() => {
  const history = historyData.value;
  const prediction = predictionData.value;
  const limitVal = props.limit;

  const historyLen = history.length;
  const predLen = prediction.length;
  const totalLen = historyLen + predLen;

  const xAxisData = [
    ...history.map((d) => d.time),
    ...prediction.map((d) => d.time),
  ];

  const historyValues = history.map((d) => d.value);
  historyValues.push(...new Array(predLen).fill(null));

  const predictionValues = new Array(historyLen).fill(null);
  predictionValues.push(...prediction.map((d) => d.value));

  const connectorValues = new Array(totalLen).fill(null);
  if (historyLen > 0 && predLen > 0) {
    connectorValues[historyLen - 1] = history[historyLen - 1].value;
    connectorValues[historyLen] = prediction[0].value;
  }

  return {
    // 图表更新动画
    animation: true,
    animationDuration: 500,
    animationEasing: "cubicOut",

    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(20, 28, 45, 0.92)",
      borderColor: "#2e7bcf",
      textStyle: { color: "#e0e6f0", fontSize: 13 },
      formatter: (params) => {
        let html = `<div style="font-weight:600;margin-bottom:6px;">${params[0].axisValue}</div>`;
        params.forEach((p) => {
          if (p.value != null) {
            html += `<div style="display:flex;align-items:center;gap:8px;margin:2px 0;">
              <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${p.color};"></span>
              ${p.seriesName}: <strong>${p.value} mg/m³</strong>
            </div>`;
          }
        });
        return html;
      },
    },
    legend: {
      data: ["历史浓度", "预测浓度", "限值"],
      textStyle: { color: "#8b98b0", fontSize: 12 },
      top: 8,
      icon: "roundRect",
    },
    grid: {
      top: 50,
      right: 30,
      bottom: 40,
      left: 55,
    },
    xAxis: {
      type: "category",
      data: xAxisData,
      boundaryGap: false,
      axisLabel: {
        color: "#8b98b0",
        fontSize: 11,
        rotate: 30,
      },
      axisLine: { lineStyle: { color: "#2a3852" } },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      name: "浓度 (mg/m³)",
      nameTextStyle: { color: "#8b98b0", fontSize: 12 },
      axisLabel: { color: "#8b98b0", fontSize: 11 },
      splitLine: {
        lineStyle: { color: "#1f2a44", type: "dashed" },
      },
    },
    series: [
      // 历史浓度（蓝色实线）
      {
        name: "历史浓度",
        type: "line",
        data: historyValues,
        smooth: true,
        symbol: "circle",
        symbolSize: 5,
        connectNulls: false,
        lineStyle: { color: "#00d4ff", width: 3 },
        itemStyle: { color: "#00d4ff" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(0,212,255,0.2)" },
              { offset: 1, color: "rgba(0,212,255,0.02)" },
            ],
          },
        },
      },
      // 预测浓度（黄色虚线，超阈值变红）
      {
        name: "预测浓度",
        type: "line",
        data: predictionValues,
        smooth: true,
        symbol: "diamond",
        symbolSize: 7,
        connectNulls: true,
        lineStyle: { width: 3, type: "dashed" },
        itemStyle: {
          color: (param) => (param.data > limitVal ? "#ef4444" : "#fbbf24"),
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(251,191,36,0.18)" },
              { offset: 1, color: "rgba(251,191,36,0.02)" },
            ],
          },
        },
      },
      // 连接线（历史→预测，灰色虚线）
      {
        name: "趋势连接",
        type: "line",
        data: connectorValues,
        connectNulls: true,
        symbol: "none",
        showSymbol: false,
        lineStyle: { color: "#8b98b0", width: 2, type: "dotted" },
        emphasis: { disabled: true },
        tooltip: { show: false },
      },
      // 阈值线
      {
        name: "限值",
        type: "line",
        data: [],
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: {
            color: props.limitColor,
            type: "dashed",
            width: 2,
          },
          label: {
            show: true,
            position: "end",
            color: props.limitColor,
            fontSize: 12,
            fontWeight: "bold",
            formatter: `限值: ${limitVal} mg/m³`,
          },
          data: [{ yAxis: limitVal }],
        },
      },
    ],
  };
});

// ========================
// 生命周期：30 秒自动刷新
// ========================
let timer = null;
onMounted(() => {
  fetchData();
  timer = setInterval(fetchData, 30000);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.chart-error {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #f87171;
  font-size: 14px;
}

.chart-retry {
  padding: 6px 18px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.chart-retry:hover {
  background: rgba(239, 68, 68, 0.25);
}
</style>
