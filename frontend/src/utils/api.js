import axios from "axios";
import { setLoading, showToast, getErrorMessage } from "@/utils/globalState";

/**
 * Gas System API 封装模块
 * 统一使用 /api 代理路径，在 vue.config.js 中已配置代理转发到后端
 */

const service = axios.create({
  baseURL: "/api",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// ========== 请求计数器（支持并发请求） ==========
let activeCount = 0;

// ========== 请求拦截器 ==========
service.interceptors.request.use(
  (config) => {
    activeCount++;
    if (activeCount === 1) setLoading(true);
    return config;
  },
  (error) => {
    activeCount = Math.max(0, activeCount - 1);
    if (activeCount === 0) setLoading(false);
    return Promise.reject(error);
  },
);

// ========== 响应拦截器（统一错误处理 + Toast） ==========
service.interceptors.response.use(
  (response) => {
    activeCount--;
    if (activeCount <= 0) {
      activeCount = 0;
      setLoading(false);
    }
    return response.data;
  },
  (error) => {
    activeCount--;
    if (activeCount <= 0) {
      activeCount = 0;
      setLoading(false);
    }
    // Toast 显示友好错误信息
    const msg = getErrorMessage(error);
    showToast(msg, "error");
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

  // ========== 演示模式 API（用于前端演示，不依赖后端） ==========

  /**
   * 获取演示模式预测数据
   * @returns {Promise<{ history: Array, prediction: Array }>}
   */
  getDemoPrediction() {
    return service.get("/demo/prediction");
  },

  /**
   * 获取演示模式预警列表
   * @returns {Promise<Array>}
   */
  getDemoAlerts() {
    return service.get("/demo/alerts");
  },

  // ========== 模型相关 API ==========

  /**
   * 获取模型信息（配置、参数等）
   * @returns {Promise<Object>}
   */
  getModelInfo() {
    return service.get("/model/info");
  },

  /**
   * 获取模型性能指标（准确率、召回率等）
   * @returns {Promise<Object>}
   */
  getModelMetrics() {
    return service.get("/model/metrics");
  },

};

export default api;
