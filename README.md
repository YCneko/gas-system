# 🏭 TVOC 智能监测预警系统

> **第十七届中国大学生服务外包创新创业大赛 A 类赛题**  
> 面向化工园区的多源废气智能治理系统开发

[![Version](https://img.shields.io/badge/version-1.3.4-blue)](https://github.com/YCneko/gas-system/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.x-brightgreen)](https://vuejs.org/)
[![TensorFlow](https://img.shields.io/badge/tensorflow-2.x-orange)](https://www.tensorflow.org/)
[![Docker](https://img.shields.io/badge/docker-compose-blue)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](./LICENSE)

---

## 📥 获取与下载

### 方式一：Git 克隆（推荐）

```bash
# 克隆仓库（Gitee 国内镜像，速度更快）
git clone https://gitee.com/YCneko/gas-system.git

# 或从 GitHub 克隆
git clone https://github.com/YCneko/gas-system.git

cd gas-system
```

### 方式二：下载 ZIP 压缩包

| 源 | 下载地址 |
|------|------|
| **Gitee（国内推荐）** | [https://gitee.com/YCneko/gas-system/releases](https://gitee.com/YCneko/gas-system/releases) |
| **GitHub** | [https://github.com/YCneko/gas-system/releases](https://github.com/YCneko/gas-system/releases) |

点击上述链接 → 选择最新版本 → 下载 `Source code (zip)` → 解压到本地目录。

### 环境要求

| 依赖 | 最低版本 | 说明 |
|------|----------|------|
| **Docker** | ≥ 20.10 | 容器运行时 |
| **Docker Compose** | ≥ 2.0 | 多容器编排 |
| **Python** | ≥ 3.10 | 仅训练模型时需要 |
| **Git** | ≥ 2.0 | 克隆仓库时需要 |

### 部署启动（3 步）

```bash
# 1. 进入项目目录
cd gas-system

# 2. 一键启动所有服务（首次启动会自动拉取镜像，约 2-5 分钟）
docker compose up -d

# 3. 浏览器打开
# 本地访问：http://localhost
# API 测试：curl http://localhost:5000/api/realtime
```

### 容器状态验证

```bash
docker compose ps
# 期望输出：
# NAME          STATUS
# gas_mysql     healthy        ← 数据库已就绪
# gas_backend   running        ← 后端 API 运行中
# gas_frontend  running        ← 前端页面可访问
```

### 停止与重启

```bash
# 停止所有服务（保留数据）
docker compose down

# 停止并删除数据库数据（彻底重置）
docker compose down -v

# 重启服务
docker compose up -d
```

> ⚠️ **注意**：`docker compose down -v` 会删除数据库中的所有数据，请谨慎操作。

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 端口 80 被占用 | 修改 `docker-compose.yml` 中 frontend 的端口映射，如 `8080:80` |
| 端口 13306 被占用 | 修改 MySQL 端口映射，如 `3307:3306`，同时修改 `backend/app.py` 中的数据库连接 |
| 首次启动慢 | 首次需拉取 Docker 镜像（约 500MB），后续启动仅需数秒 |
| 后端 API 404 | 等待 MySQL 健康检查通过（约 30 秒）后，后端才会启动 |
| Windows 环境 | 需先安装 Docker Desktop，建议启用 WSL 2 后端 |

---

## 📋 目录

- [项目简介](#项目简介)
- [赛题要求](#赛题要求)
- [获取与下载](#获取与下载)
- [技术架构](#技术架构)
- [核心功能](#核心功能)
- [数据导入](#数据导入)
- [API 文档](#api-文档)
- [模型训练](#模型训练)
- [数据说明](#数据说明)
- [项目结构](#项目结构)
- [版本历史](#版本历史)

---

## 项目简介

TVOC 智能监测预警系统是一套面向化工园区的**多源废气实时监测与智能预测平台**。系统通过融合排放源数据、气象数据与设备运行数据，基于深度学习 LSTM 模型对未来 6 小时 VOCs（挥发性有机物）浓度进行预测，并在预测超标时自动触发分级预警，为园区环境管理提供决策支持。

### 🎯 赛题契合度

| 赛题要求 | 实现情况 |
|----------|----------|
| 多源数据融合（≥3 类） | ✅ 排放 + 气象 + 设备（3 类） |
| VOCs 预测（6h，准确率 ≥ 75%） | ✅ LSTM 多步预测，R² = 0.92 |
| 预测响应时间 ≤ 2s | ✅ ~100ms |
| 可视化看板 ≤ 5s 加载 | ✅ 异步加载 + ECharts |
| Docker 一键部署 ≤ 5 步 | ✅ `docker compose up -d` |

---

## 技术架构

```
┌──────────────────────────────────────────────────────┐
│                    前端 (Vue 3)                       │
│  Dashboard │ PredictionChart │ AlertList │ DataCard  │
│              ECharts + Axios + Router                 │
└──────────────────────┬───────────────────────────────┘
                       │ RESTful API (:5000)
┌──────────────────────┴───────────────────────────────┐
│                  后端 (Flask 3.1)                      │
│  app.py │ predictor.py │ alert.py │ data_cleaner.py  │
│              SQLAlchemy + PyMySQL                     │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────┐
│                 数据库 (MySQL 8.0)                     │
│  emission_data │ weather_data │ equipment_data        │
│              alert_records (预警历史)                   │
└──────────────────────────────────────────────────────┘

全部容器化 (Docker Compose)：
  gas_mysql (:13306) → gas_backend (:5000) → gas_frontend (:80)
```

### 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端框架** | Vue 3 + ECharts + Axios | 3.x |
| **后端框架** | Flask + SQLAlchemy | 3.1 |
| **深度学习** | TensorFlow / Keras (LSTM) | 2.x |
| **数据库** | MySQL + PyMySQL | 8.0 |
| **容器化** | Docker + Docker Compose | — |
| **ML 工具** | NumPy, Pandas, scikit-learn | — |

---

## 核心功能

### 🔮 智能预测
- 基于 24 小时历史窗口的 LSTM 多步预测
- 输出未来 6 小时 VOCs 浓度趋势
- 14 维特征工程：原始指标 + 时间编码 + 滞后特征 + 滚动统计

### 🚨 分级预警
- **阈值**: VOCs > 100 mg/m³ 触发预警
- **三级分类**: 高 / 中 / 低
- **去重**: 小时内不重复告警
- 预警记录持久化存储

### 📊 可视化看板
- 实时指标卡片：VOCs 浓度、温度、湿度、风速
- ECharts 预测趋势图：历史（蓝实线）+ 预测（黄虚线）+ 阈值线（红）
- 预警列表：按时间倒序，自动过滤过期记录
- 5 秒自动刷新

### 📥 数据接入
- JSON 实时数据推送接口（`/api/data/realtime`）
- 支持分钟级多传感器数据均值对齐
- 5 阶段数据清洗管线

### 🔬 演示模式
- 一键切换演示模式，模拟预警触发场景
- 数据即时响应（<100ms），无需等待轮询周期
- 自动生成高/中/低三级模拟预警记录
- 模拟预测曲线突破阈值线效果
- 所有演示数据标注 "演示" 标识、蓝色左边框区分，不写入数据库

### 🧠 模型训练展示
- 模型架构可视化：LSTM 2 层结构、参数详情
- 训练过程 Loss 曲线（ECharts 交互式图表）
- V1/V2/V3 多版本性能指标对比
- 14 维特征标签云展示
- 独立路由页面 `/training`

### 📄 报告导出
- CSV 格式排放数据报告
- 最近 500 条记录一键下载

---

## 数据导入

```bash
# 方式一：JSON 实时推送
curl -X POST http://localhost:5000/api/data/realtime \
  -H "Content-Type: application/json" \
  -d '{"data_type":"emission","records":[{...}]}'

# 方式二：批量脚本导入
python tools/import_real_data.py
```

---

## API 文档

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/realtime` | 最新实时监测值 |
| `GET` | `/api/prediction` | 历史 24h + 未来 6h 预测 |
| `GET` | `/api/alerts` | 预警记录列表 |
| `GET` | `/api/report/export` | CSV 报告导出 |
| `GET` | `/api/vocs/prediction` | 详细预测 + 预警状态 |
| `GET` | `/api/demo/alerts` | 演示模式-模拟预警数据 |
| `GET` | `/api/demo/prediction` | 演示模式-模拟预测曲线 |
| `GET` | `/api/model/info` | 模型架构与元信息 |
| `GET` | `/api/model/metrics` | 多版本训练指标对比 |
| `POST` | `/api/data/realtime` | JSON 实时数据接入 |

> 完整 OpenAPI 3.0 规范见 `tools/openapi.yaml`

---

## 模型训练

### 当前模型（v1.0.0）

| 指标 | 值 |
|------|-----|
| 架构 | LSTM 2 层 (128 → 64) |
| 参数量 | ~125K |
| 回看窗口 | 24 小时 |
| 预测范围 | 6 小时 |
| R² | 0.9217 |
| MAE | 8.11 mg/m³ |
| 推理时间 | ~99ms |
| 特征数 | 14 维 |

### 重新训练

```bash
# 基于当前数据库数据训练
pip install tensorflow pandas scikit-learn joblib
python tools/train_model.py

# 或使用真实数据集训练
python tools/train_real_model.py

# 部署新模型到容器
docker cp backend/vocs_lstm_model.keras gas_backend:/app/
docker cp backend/scaler.pkl gas_backend:/app/
docker cp backend/feature_cols.npy gas_backend:/app/
docker restart gas_backend
```

### 训练版本对比

| 版本 | 策略 | R² | MAE | MAPE |
|------|------|-----|-----|------|
| V1 (生产) | MSE + 24步 + 14特征 | 0.9217 | 8.11 | 46.49% |
| V2 | MAE + 48步 + BN + 18特征 | 0.9140 | 8.48 | 40.10% |
| V3 | Weighted MAE + CosineLR | 0.0449 | 27.0 | 70.42% |

> V1 为当前生产模型，R² 最高但 MAPE 受低值区影响偏大。赛题准确率用归一化 MAE（1 - MAE/均值 ≈ 85%）满足 ≥ 75% 要求。

---

## 数据说明

### 数据库表结构

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `emission_data` | 废气排放监测 | sensor_id, timestamp, voc_concentration |
| `weather_data` | 气象监测 | station_id, timestamp, temperature, humidity, wind_speed |
| `equipment_data` | 设备运行状态 | equipment_id, timestamp, operating_load |
| `alert_records` | 预警历史记录 | alert_timestamp, predicted_value, alert_level |

### 真实数据来源

项目使用某化工园区 2024 年 3—5 月的真实 TVOC 监测数据（2,207 条小时级记录），包含：

- **VOCs 组分**: Hexane, CH₄, Toluene, NH₄, Acetone, CO, H₂
- **气象参数**: 温度、湿度、风速、风向、气压
- **时间特征**: 月份、周末标记、昼夜标记、季节

---

## 项目结构

```
gas-system/
├── backend/                  # Flask 后端
│   ├── app.py               # 主应用 + 全部 API 路由
│   ├── predictor.py         # LSTM 预测器封装
│   ├── alert.py             # 预警检测模块
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── data_cleaner.py      # 5 阶段数据清洗管线
│   ├── extensions.py        # 数据库扩展初始化
│   ├── init.sql             # 数据库初始化脚本
│   └── requirements.txt     # Python 依赖
├── frontend/                 # Vue 3 前端
│   └── src/
│       ├── views/
│       │   ├── DashboardView.vue  # 主看板页面
│       │   └── TrainingView.vue   # 模型训练展示页面
│       ├── components/
│       │   ├── PredictionChart.vue # ECharts 预测图
│       │   ├── AlertList.vue      # 预警列表
│       │   ├── DataCard.vue       # 指标卡片
│       │   └── ...
│       └── utils/
│           ├── api.js       # Axios API 封装
│           └── globalState.js # 全局状态管理
├── tools/                    # 开发与部署工具
│   ├── train_model.py       # LSTM V1 训练脚本
│   ├── train_model_v2.py    # LSTM V2 (改进版)
│   ├── train_model_v3.py    # LSTM V3 (实验版)
│   ├── train_real_model.py  # 真实数据训练脚本
│   ├── import_real_data.py  # 真实数据导入脚本
│   ├── data_analysis.py     # 数据探索与特征工程基类
│   ├── rebuild_scaler.py    # Scaler 重建工具
│   ├── refresh_data.py      # 数据刷新工具
│   ├── openapi.yaml         # OpenAPI 3.0 接口规范
│   └── ...
├── docker-compose.yml        # Docker 三容器编排
├── .gitignore               # Git 忽略规则
└── README.md                # 本文件
```

---

## 版本历史

| 版本 | 日期 | 内容 |
|------|------|------|
| **v1.3.2** | 2026-06-18 | 演示模式即时响应优化（watch 监听，切换零延迟）；关于页改造为白蓝主题并移至右上角；README 新增详细下载与部署指南 |
| **v1.3.1** | 2026-06-18 | 修复模型训练页面 API 调用错误；演示数据视觉区分（蓝色左边框、演示标签、值域提升） |
| **v1.3.0** | 2026-06-18 | 新增演示模式（一键模拟预警+预测曲线）；新增模型训练展示页面（架构/曲线/版本对比）；全局 UI 升级为白蓝亮色主题 |
| **v1.2.0** | 2026-06-18 | 真实数据驱动：导入化工园区 TVOC 监测数据（2,207条），重新训练 LSTM 模型（R²=0.9157）；看板升级（标题/组分卡片/图表比例优化） |
| **v1.1.0** | 2026-06-18 | 移除 CSV/Excel 文件上传、清空数据、一键重导入功能，精简为纯实时监测系统 |
| **v1.0.0** | 2026-06-18 | 项目架构整理：训练脚本统一移入 `tools/`，新增 V2/V3 训练脚本，Docker 三容器部署，OpenAPI 规范 |

---

## 开源协议

MIT License

---

> 📧 问题反馈：[GitHub Issues](https://github.com/YCneko/gas-system/issues)
