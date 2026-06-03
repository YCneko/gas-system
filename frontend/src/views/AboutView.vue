<template>
  <div class="about">
    <!-- 头部 -->
    <header class="about-header">
      <div class="about-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
        </div>
        <div>
          <h1>深信软技信息技术有限公司</h1>
          <p>ShenXin Software Technology Co., Ltd.</p>
        </div>
      </div>
    </header>

    <!-- 主体 -->
    <main class="about-body">
      <!-- 公司简介 -->
      <section class="section">
        <h2>公司简介</h2>
        <p>
          深信软技信息技术有限公司成立于 2021 年，总部位于山东省济南市高新区，
          是一家专注于工业智能化与环保科技领域的国家级高新技术企业。
          公司深耕"AI + 工业互联网"赛道，为化工、制药、能源等行业客户提供
          从数据采集、智能分析到可视化决策的一站式数字化解决方案。
        </p>
        <p>
          公司核心产品 <strong>Gas System</strong> 多源废气智能治理平台，
          融合物联网、深度学习与大数据可视化技术，
          实现了工业园区废气排放的全流程透明化监控与 AI 预测预警，
          已累计服务超过 30 家大中型化工园区及制造企业。
        </p>
      </section>

      <!-- 核心业务 -->
      <section class="section">
        <h2>核心业务</h2>
        <div class="biz-grid">
          <div class="biz-card">
            <div class="biz-icon">📡</div>
            <h3>工业数据融合</h3>
            <p>多源异构数据接入、清洗与分钟级时序对齐，打破信息孤岛</p>
          </div>
          <div class="biz-card">
            <div class="biz-icon">🧠</div>
            <h3>AI 预测引擎</h3>
            <p>基于 LSTM 深度学习的排放趋势预测，支持多指标时序建模</p>
          </div>
          <div class="biz-card">
            <div class="biz-icon">📊</div>
            <h3>智能监控大屏</h3>
            <p>Web 端一体化可视化看板，支持实时监控、预警展示与数据导出</p>
          </div>
          <div class="biz-card">
            <div class="biz-icon">🚀</div>
            <h3>敏捷部署交付</h3>
            <p>Docker 容器化、微服务架构，支持本地私有化与云上混合部署</p>
          </div>
        </div>
      </section>

      <!-- 资质与荣誉 -->
      <section class="section">
        <h2>资质与荣誉</h2>
        <div class="honor-grid">
          <div class="honor-item">
            <span class="honor-year">2023</span>
            <span class="honor-text">国家级高新技术企业认定</span>
          </div>
          <div class="honor-item">
            <span class="honor-year">2024</span>
            <span class="honor-text">山东省"专精特新"中小企业</span>
          </div>
          <div class="honor-item">
            <span class="honor-year">2024</span>
            <span class="honor-text">ISO 9001 / ISO 14001 双体系认证</span>
          </div>
          <div class="honor-item">
            <span class="honor-year">2025</span>
            <span class="honor-text">工业互联网平台可信服务评估认证</span>
          </div>
          <div class="honor-item">
            <span class="honor-year">2025</span>
            <span class="honor-text">山东省软件企业认定</span>
          </div>
          <div class="honor-item">
            <span class="honor-year">2026</span>
            <span class="honor-text">化工园区环保智能监测领域优秀解决方案奖</span>
          </div>
        </div>
      </section>

      <!-- 联系信息 -->
      <section class="section">
        <h2>联系我们</h2>
        <div class="contact-grid">
          <div class="contact-item">
            <span class="contact-label">公司地址</span>
            <span class="contact-value">山东省济南市高新区舜华路 2000 号  舜泰广场 8 号楼 15 层</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">联系电话</span>
            <span class="contact-value">0531-8896 3300</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">电子邮箱</span>
            <span class="contact-value">contact@shenxin-tech.com</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">官方网站</span>
            <span class="contact-value">www.shenxin-tech.com</span>
          </div>
        </div>
      </section>

      <!-- 底部 -->
      <footer class="about-footer">
        <p>© 2021–2026 深信软技信息技术有限公司  |  版本 v3.2</p>
        <p>Gas System — 面向化工园区的多源废气智能治理系统</p>
      </footer>
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.about {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: linear-gradient(135deg, #0a0f1a 0%, #0d1422 100%);
}

.about-header {
  padding: 28px 40px;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(46, 123, 207, 0.2);
}
.about-brand {
  display: flex;
  align-items: center;
  gap: 20px;
}
.brand-logo {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, #1e40af, #3b82f6);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 0 30px rgba(59, 130, 246, 0.25);
}
.about-brand h1 {
  font-size: 24px;
  font-weight: 700;
  color: #e0e6f0;
  margin: 0 0 4px;
}
.about-brand p {
  font-size: 13px;
  color: #6b7a94;
  margin: 0;
}

.about-body {
  flex: 1;
  padding: 32px 40px;
  max-width: 960px;
}
.section {
  margin-bottom: 36px;
}
.section h2 {
  font-size: 18px;
  font-weight: 700;
  color: #cdd6f0;
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.section p {
  font-size: 14px;
  line-height: 1.8;
  color: #8b98b0;
  margin-bottom: 10px;
}
.section p strong {
  color: #3b82f6;
}

.biz-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.biz-card {
  background: rgba(18, 26, 46, 0.6);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 12px;
  padding: 18px 14px;
  text-align: center;
  transition: all 0.2s;
}
.biz-card:hover {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(18, 26, 46, 0.8);
}
.biz-icon { font-size: 28px; margin-bottom: 8px; }
.biz-card h3 { font-size: 13px; font-weight: 600; color: #cdd6f0; margin-bottom: 6px; }
.biz-card p { font-size: 11px; color: #6b7a94; line-height: 1.6; margin: 0; }

.honor-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.honor-item {
  background: rgba(18, 26, 46, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.honor-year {
  font-size: 13px;
  font-weight: 700;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  padding: 3px 10px;
  border-radius: 6px;
  white-space: nowrap;
}
.honor-text { font-size: 14px; color: #c0d0e8; }

.contact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.contact-item {
  background: rgba(18, 26, 46, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.contact-label {
  font-size: 11px;
  font-weight: 600;
  color: #576580;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.contact-value { font-size: 14px; color: #c0d0e8; }

.about-footer {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  text-align: center;
}
.about-footer p {
  font-size: 12px;
  color: #4a5568;
  margin: 2px 0;
}

@media (max-width: 768px) {
  .about-header { padding: 20px; }
  .about-body { padding: 20px; }
  .biz-grid { grid-template-columns: 1fr 1fr; }
  .contact-grid, .honor-grid { grid-template-columns: 1fr; }
}
</style>
