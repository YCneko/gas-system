<template>
  <div class="alert-list">
    <!-- 演示模式标签（表格上方） -->
    <div v-if="demoMode" class="demo-badge">🔬 演示数据</div>

    <table class="alert-table">
      <thead>
        <tr>
          <th>时间</th>
          <th>指标</th>
          <th>级别</th>
          <th>详情</th>
        </tr>
      </thead>
      <tbody>
        <TransitionGroup name="alert-row" tag="tbody">
          <tr
            v-for="(alert, index) in sortedAlerts"
            :key="alert.id || alert.time + alert.metric + index"
            :class="{ 'row-new': alert._isNew, 'row-demo': alert._isDemo || demoMode }"
            @click="openDetail(alert)"
          >
            <td>{{ alert.time }}</td>
            <td>{{ alert.metric }}</td>
            <td>
              <span :class="['level-badge', alert.level]">
                {{ levelText(alert.level) }}
              </span>
            </td>
            <td class="detail-cell">{{ alert.detail }}</td>
          </tr>
        </TransitionGroup>
      </tbody>
    </table>

    <div v-if="!sortedAlerts.length" class="empty-state">
      <span>暂无预警信息 ✅</span>
      <span class="empty-hint">仅显示预测时间在当前时间之后的预警</span>
    </div>

    <div class="current-time-bar">
      <span class="time-icon">🕐</span>
      <span>当前时间：{{ currentTime }}</span>
      <span class="filter-note">（仅显示未来预警，已过期自动隐藏）</span>
    </div>

    <!-- 预警详情弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showDetail" class="modal-overlay" @click.self="closeDetail">
          <div class="modal-panel">
            <div class="modal-header">
              <h3>预警详细信息</h3>
              <button class="modal-close" @click="closeDetail">&times;</button>
            </div>
            <div class="modal-body">
              <div class="detail-row">
                <span class="label">时间</span>
                <span class="value">{{ currentAlert?.time }}</span>
              </div>
              <div class="detail-row">
                <span class="label">指标</span>
                <span class="value">{{ currentAlert?.metric }}</span>
              </div>
              <div class="detail-row">
                <span class="label">级别</span>
                <span :class="['value', 'level-badge', currentAlert?.level]">
                  {{ levelText(currentAlert?.level) }}
                </span>
              </div>
              <div class="detail-row detail-full">
                <span class="label">详情</span>
                <span class="value">{{ currentAlert?.detail }}</span>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn-close" @click="closeDetail">关闭</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, inject, watch } from "vue";
import api from "@/utils/api";

const list = ref([]);
const showDetail = ref(false);
const currentAlert = ref(null);
const knownIds = ref(new Set());
const currentTime = ref(new Date().toLocaleString());

// 演示模式（从父组件注入，用于展示模拟数据）
const demoMode = inject("demoMode", ref(false));

// 监听演示模式切换，立即刷新预警列表
watch(demoMode, () => {
  knownIds.value = new Set(); // 清除已知 ID，让新数据有入场动画
  fetchAlerts();
});

// ========================
// 获取预警列表
// ========================
const fetchAlerts = async () => {
  try {
    let data;
    if (demoMode.value) {
      // 演示模式：使用内嵌模拟数据（6条，涵盖 error/warn/info 三个等级）
      data = [
        { id: "demo-1", time: new Date(Date.now() + 3600000).toLocaleString(), metric: "VOCs浓度", level: "error", detail: "⚠ 预测浓度将达 125.3 mg/m³，超过100mg/m³限值", predicted_exceedance_time: new Date(Date.now() + 3600000).toISOString(), _isDemo: true },
        { id: "demo-2", time: new Date(Date.now() + 7200000).toLocaleString(), metric: "VOCs浓度", level: "error", detail: "⚠ 预测浓度将达 118.7 mg/m³，超过100mg/m³限值", predicted_exceedance_time: new Date(Date.now() + 7200000).toISOString(), _isDemo: true },
        { id: "demo-3", time: new Date(Date.now() + 10800000).toLocaleString(), metric: "VOCs浓度", level: "warn", detail: "⚠ 预测浓度将达 105.2 mg/m³，接近并略超限值", predicted_exceedance_time: new Date(Date.now() + 10800000).toISOString(), _isDemo: true },
        { id: "demo-4", time: new Date(Date.now() + 14400000).toLocaleString(), metric: "VOCs浓度", level: "warn", detail: "⚠ 预测浓度将达 102.1 mg/m³，接近限值", predicted_exceedance_time: new Date(Date.now() + 14400000).toISOString(), _isDemo: true },
        { id: "demo-5", time: new Date(Date.now() + 18000000).toLocaleString(), metric: "VOCs浓度", level: "info", detail: "ℹ 预测浓度将达 92.5 mg/m³，处于正常偏高范围", predicted_exceedance_time: new Date(Date.now() + 18000000).toISOString(), _isDemo: true },
        { id: "demo-6", time: new Date(Date.now() + 21600000).toLocaleString(), metric: "VOCs浓度", level: "info", detail: "ℹ 预测浓度将达 88.3 mg/m³，处于正常范围", predicted_exceedance_time: new Date(Date.now() + 21600000).toISOString(), _isDemo: true },
      ];
    } else {
      data = await api.getAlertList();
    }
    const newList = Array.isArray(data) ? data : [];

    // 更新当前时间
    currentTime.value = new Date().toLocaleString();

    newList.forEach((item) => {
      const id = item.id ?? item.time + item.metric;
      if (!knownIds.value.has(id) && item.level !== "normal") {
        item._isNew = true;
        knownIds.value.add(id);
      } else {
        item._isNew = false;
      }
    });

    // 前端二次过滤：仅保留预测超标时间在当前时间之后的预警
    const now = new Date();
    list.value = newList.filter((item) => {
      if (!item.predicted_exceedance_time) {
        // 没有预测时间字段的旧数据保留（兼容）
        return true;
      }
      const predTime = new Date(item.predicted_exceedance_time);
      return predTime > now;
    });
  } catch (err) {
    console.error("[AlertList] 获取预警失败:", err);
  }
};

// ========================
// 浏览器桌面通知（已关闭，取消注释可恢复）
// ========================
// const sendNotification = (alert) => {
//   if (Notification.permission !== "granted") return;
//   try {
//     new Notification("⚠️ Gas System 预警", {
//       body: `[${levelText(alert.level)}] ${alert.metric}：${alert.detail}`,
//       tag: alert.id || alert.time + alert.metric,
//     });
//   } catch (e) {
//     // Notification API 不支持时静默
//   }
// };

// ========================
// 弹窗控制
// ========================
const openDetail = (item) => {
  currentAlert.value = item;
  showDetail.value = true;
};
const closeDetail = () => {
  showDetail.value = false;
  currentAlert.value = null;
};

// ========================
// 排序
// ========================
const sortedAlerts = computed(() => {
  return [...list.value].sort((a, b) =>
    (b.time || "").localeCompare(a.time || ""),
  );
});

// ========================
// 级别文本
// ========================
const levelText = (level) => {
  const map = {
    critical: "🔴 紧急",
    error: "🔴 严重",
    warn: "🟡 警告",
    warning: "🟡 警告",
    normal: "✅ 正常",
    info: "🔵 提示",
  };
  return map[level] || level;
};

// ========================
// 生命周期
// ========================
let timer = null;
let clockTimer = null;
onMounted(() => {
  fetchAlerts();
  timer = setInterval(fetchAlerts, 10000);
  // 每秒刷新当前时间显示
  clockTimer = setInterval(() => {
    currentTime.value = new Date().toLocaleString();
  }, 1000);
});
onUnmounted(() => {
  clearInterval(timer);
  clearInterval(clockTimer);
});
</script>

<style scoped>
.alert-list {
  width: 100%;
  color: #334155;
  font-size: 14px;
}

/* ---------- 表格 ---------- */
.alert-table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: 12px 16px;
  background: #f8fafc;
  text-align: left;
  color: #475569;
  font-weight: 600;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 1;
  backdrop-filter: blur(4px);
}

td {
  padding: 11px 16px;
  border-bottom: 1px solid #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

tr {
  cursor: pointer;
  transition: background 0.2s;
}
tr:hover {
  background: rgba(37, 99, 235, 0.04);
}

.detail-cell {
  max-width: 220px;
}

/* ---------- 级别徽标 ---------- */
.level-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
/* 亮色主题下降低徽标饱和度 */
.level-badge.critical,
.level-badge.error {
  background: rgba(245, 108, 108, 0.1);
  color: #e05252;
  border: 1px solid rgba(245, 108, 108, 0.2);
}
.level-badge.warn,
.level-badge.warning {
  background: rgba(230, 162, 60, 0.1);
  color: #d4a017;
  border: 1px solid rgba(230, 162, 60, 0.2);
}
.level-badge.normal {
  background: rgba(16, 185, 129, 0.1);
  color: #0d9488;
  border: 1px solid rgba(16, 185, 129, 0.2);
}
.level-badge.info {
  background: rgba(64, 158, 255, 0.1);
  color: #3b82f6;
  border: 1px solid rgba(64, 158, 255, 0.2);
}

/* ---------- 新条目滑入动画 ---------- */
.row-new {
  animation: slide-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slide-in {
  0% {
    transform: translateX(60px);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

/* TransitionGroup 动画 */
.alert-row-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.alert-row-leave-active {
  transition: all 0.3s ease-in;
}

.alert-row-enter-from {
  transform: translateX(80px);
  opacity: 0;
}

.alert-row-leave-to {
  transform: translateX(-40px);
  opacity: 0;
}

.alert-row-move {
  transition: transform 0.3s ease;
}

/* ---------- 空状态 ---------- */
.empty-state {
  text-align: center;
  padding: 36px 16px 8px;
  color: #94a3b8;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.empty-hint {
  font-size: 12px;
  color: #cbd5e1;
}

/* ---------- 演示模式标签 ---------- */
.demo-badge {
  text-align: center;
  padding: 8px 16px;
  margin: 0 0 4px 0;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(37, 99, 235, 0.05));
  color: #2563eb;
  border-radius: 0;
  font-size: 13px;
  font-weight: 600;
  border-bottom: 2px dashed #93c5fd;
  letter-spacing: 1px;
}

/* ---------- 演示行样式 ---------- */
tr.row-demo {
  border-left: 3px solid #93c5fd;
  background: rgba(37, 99, 235, 0.02);
}
tr.row-demo:hover {
  background: rgba(37, 99, 235, 0.06);
}

/* ---------- 当前时间指示条 ---------- */
.current-time-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px 12px;
  font-size: 12px;
  color: #64748b;
  border-top: 1px solid #e2e8f0;
}
.time-icon {
  font-size: 14px;
}
.filter-note {
  color: #94a3b8;
  font-size: 11px;
}

/* ---------- 弹窗 ---------- */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-panel {
  background: #ffffff;
  border-radius: 16px;
  min-width: 400px;
  max-width: 500px;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid #e2e8f0;
}
.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 24px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
.modal-close:hover {
  color: #1e293b;
}

.modal-body {
  padding: 20px 24px;
}

.detail-row {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
  align-items: baseline;
}
.detail-row .label {
  color: #64748b;
  min-width: 50px;
  font-size: 14px;
  flex-shrink: 0;
}
.detail-row .value {
  color: #334155;
  font-size: 14px;
}
.detail-full .value {
  line-height: 1.6;
  word-break: break-word;
}

.modal-footer {
  padding: 14px 24px;
  border-top: 1px solid #e2e8f0;
  text-align: right;
}

.btn-close {
  padding: 8px 22px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-close:hover {
  opacity: 0.85;
}

/* ---------- 过渡动画 ---------- */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
