import axios from "axios";

/**
 * Gas System API 封装模块
 * 统一使用 /api 代理路径，在 vue.config.js 中已配置代理转发到后端
 */

const service = axios.create({
  baseURL: "/api",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// ========== 请求拦截器 ==========
service.interceptors.request.use(
  (config) => {
    // 可在此处添加 token 等认证信息
    // const token = localStorage.getItem("token");
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error),
);

// ========== 响应拦截器（统一错误处理） ==========
service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      const msg = data?.message || data?.error || "服务器错误";
      switch (status) {
        case 400:
          console.error("[API] 请求参数错误:", msg);
          break;
        case 401:
          console.error("[API] 未授权，请检查认证信息");
          break;
        case 403:
          console.error("[API] 无权限访问该资源");
          break;
        case 404:
          console.error("[API] 请求的资源不存在:", error.response.config?.url);
          break;
        case 500:
          console.error("[API] 服务器内部错误:", msg);
          break;
        default:
          console.error(`[API] HTTP ${status}:`, msg);
      }
    } else if (error.request) {
      console.error("[API] 网络异常：无法连接到服务器，请确认后端服务已启动");
    } else {
      console.error("[API] 请求配置错误:", error.message);
    }
    return Promise.reject(error);
  },
);

// ========== API 接口列表 ==========
const api = {
  /**
   * 获取未来6小时 VOCs 预测数据
   * @returns {Promise<{ history: Array<{ time: string, value: number }>, prediction: Array<{ time: string, value: number }> }>}
   */
  getPrediction() {
    return service.get("/prediction");
  },

  /**
   * 获取实时监测数据
   * @returns {Promise<{ voc: number, temp: number, humidity: number, wind: number }>}
   */
  getRealtimeData() {
    return service.get("/realtime");
  },

  /**
   * 获取预警列表
   * @returns {Promise<Array<{ id: string|number, time: string, metric: string, level: string, detail: string }>>}
   */
  getAlertList() {
    return service.get("/alerts");
  },

  /**
   * 导出数据报告
   * @param {Object} params - 查询参数（如时间范围、数据维度等）
   * @returns {Promise<Blob>} 文件二进制数据
   */
  exportReport(params = {}) {
    return service.get("/report/export", {
      params,
      responseType: "blob",
    });
  },
};

export default api;
