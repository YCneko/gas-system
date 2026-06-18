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

  /**
   * 上传数据文件（CSV / Excel）
   * @param {File} file - 文件对象
   * @param {string} dataType - 数据类型: emission | weather | equipment
   * @returns {Promise<{ message: string, imported_rows: number, before_completeness: number, after_completeness: number }>}
   */
  uploadData(file, dataType) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("data_type", dataType);
    return service.post("/data/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 30000,
    });
  },

  /**
   * 清空所有数据（排放、气象、设备、预警记录）
   * @returns {Promise<{ message: string, deleted: object }>}
   */
  clearData() {
    return service.delete("/data/clear");
  },

  /**
   * 一键重新导入上次上传的数据
   * @returns {Promise<{ message: string, total_imported: number, results: object }>}
   */
  reimportData() {
    return service.post("/data/reimport");
  },
};

export default api;
