/**
 * 全局响应式状态（替代 Pinia，轻量方案）
 * 跨组件共享 loading、toast、离线状态
 */
import { reactive } from "vue";

// ========== 全局状态 ==========
export const store = reactive({
  /** 顶部进度条：活跃请求数 */
  activeRequests: 0,
  /** Toast 消息列表 */
  toasts: [],
  /** 是否离线 */
  offline: false,
});

// ========== Loading 进度条 ==========
export function setLoading(loading) {
  if (loading) {
    store.activeRequests++;
  } else {
    store.activeRequests = Math.max(0, store.activeRequests - 1);
  }
}

// ========== Toast 消息 ==========
let toastId = 0;

/**
 * 显示 Toast 通知
 * @param {string} message - 消息内容
 * @param {'success'|'error'|'warning'|'info'} type - 类型
 * @param {number} duration - 自动关闭毫秒数
 */
export function showToast(message, type = "error", duration = 4000) {
  const id = ++toastId;
  store.toasts.push({ id, message, type });
  if (duration > 0) {
    setTimeout(() => {
      const idx = store.toasts.findIndex((t) => t.id === id);
      if (idx !== -1) store.toasts.splice(idx, 1);
    }, duration);
  }
}

/** 移除指定 Toast */
export function removeToast(id) {
  const idx = store.toasts.findIndex((t) => t.id === id);
  if (idx !== -1) store.toasts.splice(idx, 1);
}

// ========== 离线检测 ==========
export function setOffline(val) {
  store.offline = val;
}

/**
 * 从 API 错误对象中提取可读信息
 */
export function getErrorMessage(error) {
  if (!error) return "未知错误";
  if (error.response) {
    const data = error.response.data;
    const msg = data?.message || data?.error || "";
    const status = error.response.status;
    const statusMap = {
      400: "请求参数错误",
      401: "未授权，请重新登录",
      403: "无权限访问",
      404: "请求的资源不存在",
      500: "服务器内部错误",
      502: "网关错误",
      503: "服务暂不可用",
    };
    const prefix = statusMap[status] || `HTTP ${status}`;
    return msg ? `${prefix}：${msg}` : prefix;
  }
  if (error.request) return "无法连接到服务器，请检查网络";
  return error.message || "请求异常";
}
