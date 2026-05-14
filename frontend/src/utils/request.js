import axios from "axios";

const request = axios.create({
  baseURL: "http://127.0.0.1:5000",
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// 响应拦截：直接返回 data，方便组件使用
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error("请求出错：", error);
    return Promise.reject(error);
  },
);

export default request;
