<template>
  <div class="about">
    <!-- 头部 -->
    <header class="about-header">
      <div class="about-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
        </div>
        <div>
          <h1>齐鲁绿源环保科技有限公司</h1>
          <p>Qilu Green Source Environmental Technology Co., Ltd.</p>
        </div>
      </div>
    </header>

    <!-- 主体 -->
    <main class="about-body">
      <!-- 公司简介 -->
      <section class="section">
        <h2>公司简介</h2>
        <p>
          齐鲁绿源环保科技有限公司成立于 2023 年，由齐鲁师范学院信息科学与工程学院（人工智能学院）
          及化学与化工学院联合孵化，是一家专注于工业园区智能化环保治理解决方案的科技型企业。
          公司核心团队来自人工智能、环境工程与数据科学领域的跨学科研究团队，
          依托山东省数据开放应用创新实验室、山东省数字经济产业创新中心等多个省级科研平台，
          致力于为中小企业和化工园区提供"低成本、高可用"的废气智能监测与治理解决方案。
        </p>
        <p>
          公司自主研发的 <strong>Gas System</strong> 多源废气智能治理平台，
          集成了多源数据融合、VOCs 浓度 AI 预测、一体化可视化监控三大核心能力，
          已在国内多个中型化工园区完成试点部署，有效降低了园区环保合规风险和运营成本。
        </p>
      </section>

      <!-- 核心业务 -->
      <section class="section">
        <h2>核心业务</h2>
        <div class="biz-grid">
          <div class="biz-card">
            <div class="biz-icon">📡</div>
            <h3>多源数据融合</h3>
            <p>接入废气浓度、气象参数、设备工况等多源异构数据，分钟级对齐与清洗</p>
          </div>
          <div class="biz-card">
            <div class="biz-icon">🧠</div>
            <h3>AI 智能预测</h3>
            <p>基于深度学习的 VOCs 浓度趋势预测，提前 6 小时预警超标风险</p>
          </div>
          <div class="biz-card">
            <div class="biz-icon">📊</div>
            <h3>可视化监控</h3>
            <p>一体化 Web 监控大屏，实时指标、预测曲线、预警列表一站式管理</p>
          </div>
          <div class="biz-card">
            <div class="biz-icon">🔧</div>
            <h3>定制化部署</h3>
            <p>支持 Docker 容器化一键部署，适配本地服务器与云环境</p>
          </div>
        </div>
      </section>

      <!-- 联系信息 -->
      <section class="section">
        <h2>联系我们</h2>
        <div class="contact-grid">
          <div class="contact-item">
            <span class="contact-label">公司地址</span>
            <span class="contact-value">山东省济南市章丘区文博路 2 号  齐鲁师范学院章丘校区</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">联系电话</span>
            <span class="contact-value">0531-6677 8000</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">电子邮箱</span>
            <span class="contact-value">contact@qlgreensource.com</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">研发中心</span>
            <span class="contact-value">山东省数据开放应用创新实验室（齐鲁师范学院）</span>
          </div>
        </div>
      </section>

      <!-- 底部 -->
      <footer class="about-footer">
        <p>© 2023–2026 齐鲁绿源环保科技有限公司  | 版本 v3.1</p>
        <p>本系统由齐鲁师范学院信息科学与工程学院（人工智能学院）提供技术支持</p>
      </footer>
    </main>
  </div>
</template>

<script setup>
// About page — 公司信息展示
</script>

<style scoped>
.about {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: linear-gradient(135deg, #0a0f1a 0%, #0d1422 100%);
}

/* ---- 头部 ---- */
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
  background: linear-gradient(135deg, #1e3a8a, #00d4ff);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.25);
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

/* ---- 主体 ---- */
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
  color: #00d4ff;
}

/* ---- 业务卡片 ---- */
.biz-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.biz-card {
  background: rgba(18, 26, 46, 0.6);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(46, 123, 207, 0.12);
  border-radius: 12px;
  padding: 18px 14px;
  text-align: center;
  transition: all 0.2s;
}
.biz-card:hover {
  border-color: rgba(0, 212, 255, 0.3);
  background: rgba(18, 26, 46, 0.8);
}
.biz-icon { font-size: 28px; margin-bottom: 8px; }
.biz-card h3 {
  font-size: 13px;
  font-weight: 600;
  color: #cdd6f0;
  margin-bottom: 6px;
}
.biz-card p {
  font-size: 11px;
  color: #6b7a94;
  line-height: 1.6;
  margin: 0;
}

/* ---- 联系信息 ---- */
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
.contact-value {
  font-size: 14px;
  color: #c0d0e8;
}

/* ---- 底部 ---- */
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

/* ---- 响应式 ---- */
@media (max-width: 768px) {
  .about-header { padding: 20px; }
  .about-body { padding: 20px; }
  .biz-grid { grid-template-columns: 1fr 1fr; }
  .contact-grid { grid-template-columns: 1fr; }
}
</style>
