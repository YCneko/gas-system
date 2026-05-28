const { defineConfig } = require("@vue/cli-service");

module.exports = defineConfig({
  // ========== 编译选项 ==========
  transpileDependencies: true,

  // ========== 开发服务器 ==========
  devServer: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
    },
  },

  // ========== 构建优化 ==========
  productionSourceMap: false, // 生产环境不输出 source map，减少体积

  configureWebpack: {
    performance: {
      hints: false, // 关闭大文件警告
    },
  },

  // ========== CSS 配置 ==========
  css: {
    extract: {
      // 将 CSS 提取为独立文件（默认开启），有助于缓存
      ignoreOrder: true,
    },
  },

  // ========== PWA / 离线支持（可选） ==========
  // pwa: { ... },
});
