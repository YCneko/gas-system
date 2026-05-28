<template>
  <div class="alert-list">
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
            :class="{ 'row-new': alert._isNew }"
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
import { computed, ref, onMounted, onUnmounted } from "vue";
import api from "@/utils/api";

const list = ref([]);
const showDetail = ref(false);
const currentAlert = ref(null);
const knownIds = ref(new Set());

// ========================
// 获取预警列表
// ========================
const fetchAlerts = async () => {
  try {
    const data = await api.getAlertList();
    const newList = Array.isArray(data) ? data : [];

    newList.forEach((item) => {
      const id = item.id ?? item.time + item.metric;
      if (!knownIds.value.has(id) && item.level !== "normal") {
        item._isNew = true;
        sendNotification(item);
        knownIds.value.add(id);
      } else {
        item._isNew = false;
      }
    });

    list.value = newList;
  } catch (err) {
    console.error("[AlertList] 获取预警失败:", err);
  }
};

// ========================
// 浏览器桌面通知
// ========================
const sendNotification = (alert) => {
  if (Notification.permission !== "granted") return;
  try {
    new Notification("⚠️ Gas System 预警", {
      body: `[${levelText(alert.level)}] ${alert.metric}：${alert.detail}`,
      tag: alert.id || alert.time + alert.metric,
    });
  } catch (e) {
    // Notification API 不支持时静默
  }
};

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
onMounted(() => {
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
  fetchAlerts();
  timer = setInterval(fetchAlerts, 10000);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.alert-list {
  width: 100%;
  color: #cbd5e1;
  font-size: 14px;
}

/* ---------- 表格 ---------- */
.alert-table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  text-align: left;
  color: #8b98b0;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: 0;
  z-index: 1;
  backdrop-filter: blur(4px);
}

td {
  padding: 11px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

tr {
  cursor: pointer;
  transition: background 0.2s;
}
tr:hover {
  background: rgba(0, 212, 255, 0.06);
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
.level-badge.critical,
.level-badge.error {
  background: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.3);
}
.level-badge.warn,
.level-badge.warning {
  background: rgba(230, 162, 60, 0.15);
  color: #e6a23c;
  border: 1px solid rgba(230, 162, 60, 0.3);
}
.level-badge.normal {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.level-badge.info {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
  border: 1px solid rgba(64, 158, 255, 0.3);
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
  padding: 36px 16px;
  color: #576580;
  font-size: 14px;
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
  background: #16203a;
  border-radius: 16px;
  min-width: 400px;
  max-width: 500px;
  color: #e0e6f0;
  border: 1px solid #2a3852;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: #6b7a94;
  font-size: 24px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
.modal-close:hover {
  color: #e0e6f0;
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
  color: #6b7a94;
  min-width: 50px;
  font-size: 14px;
  flex-shrink: 0;
}
.detail-row .value {
  color: #e0e6f0;
  font-size: 14px;
}
.detail-full .value {
  line-height: 1.6;
  word-break: break-word;
}

.modal-footer {
  padding: 14px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  text-align: right;
}

.btn-close {
  padding: 8px 22px;
  background: linear-gradient(135deg, #1e3a8a, #00d4ff);
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
