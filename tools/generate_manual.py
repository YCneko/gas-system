"""生成专业风格的系统使用手册 Word 文档"""
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.8)

style = doc.styles['Normal']
style.font.name = '微软雅黑'
style.font.size = Pt(11)
style.paragraph_format.line_spacing = 1.4
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

for level in range(1, 4):
    h = doc.styles[f'Heading {level}']
    h.font.name = '微软雅黑'
    h.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    if level == 1:
        h.font.size = Pt(16)
        h.font.color.rgb = RGBColor(0, 51, 102)
        h.paragraph_format.space_before = Pt(24)
    elif level == 2:
        h.font.size = Pt(13)
        h.font.color.rgb = RGBColor(0, 70, 130)
        h.paragraph_format.space_before = Pt(18)
    else:
        h.font.size = Pt(11.5)
        h.font.color.rgb = RGBColor(50, 50, 50)


def p(text, bold=False, size=11, color=None, align=None, indent=None):
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.name = '微软雅黑'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    if align is not None:
        para.alignment = align
    if indent:
        para.paragraph_format.left_indent = Cm(indent)
    para.paragraph_format.space_after = Pt(4)
    return para


def gap():
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def code(text):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(4)
    para.paragraph_format.space_after = Pt(4)
    para.paragraph_format.left_indent = Cm(0.6)
    shd = para._element.get_or_add_pPr().makeelement(qn('w:shd'), {
        qn('w:val'): 'clear', qn('w:color'): 'auto', qn('w:fill'): 'F0F0F0',
    })
    para._element.get_or_add_pPr().append(shd)
    run = para.add_run(text)
    run.font.name = 'Consolas'
    run.font.size = Pt(9)
    return para


def table(headers, rows, widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'
    for j, hdr in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = hdr
        for pr in cell.paragraphs:
            for rn in pr.runs:
                rn.bold = True
                rn.font.size = Pt(10)
                rn.font.name = '微软雅黑'
                rn._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            cell.text = str(val)
            for pr in cell.paragraphs:
                for rn in pr.runs:
                    rn.font.size = Pt(10)
                    rn.font.name = '微软雅黑'
                    rn._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    gap()
    return t


def note(text):
    para = doc.add_paragraph()
    para._element.get_or_add_pPr().append(
        para._element.get_or_add_pPr().makeelement(qn('w:shd'), {
            qn('w:val'): 'clear', qn('w:color'): 'auto', qn('w:fill'): 'E8F5E9',
        }))
    run = para.add_run(text)
    run.font.name = '微软雅黑'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    run.font.size = Pt(10)
    para.paragraph_format.left_indent = Cm(0.6)
    para.paragraph_format.space_after = Pt(4)
    return para


def page_break():
    doc.add_page_break()


# ===================== 封面 =====================
for _ in range(7):
    gap()
p('Gas System', bold=True, size=32, color=(0, 51, 102), align=WD_ALIGN_PARAGRAPH.CENTER)
p('面向化工园区的多源废气智能治理系统', size=16, color=(80, 80, 80), align=WD_ALIGN_PARAGRAPH.CENTER)
gap()
p('系统使用手册', size=14, color=(120, 120, 120), align=WD_ALIGN_PARAGRAPH.CENTER)
gap()
gap()
p('版本 3.1 | 2026年6月', size=11, color=(150, 150, 150), align=WD_ALIGN_PARAGRAPH.CENTER)
page_break()

# ===================== 1 系统概述 =====================
doc.add_heading('1. 系统概述', level=1)
p('Gas System 是一套面向化工园区的废气智能治理系统，集成多源数据融合、VOCs 浓度预测、可视化监控三大核心能力。')
gap()
p('核心模块：', bold=True)
table(
    ['模块', '功能', '技术实现'],
    [
        ['数据融合', '多源异构数据接入、清洗、分钟级时序对齐、结构化存储', 'Flask + PyMySQL + pandas'],
        ['VOCs 预测', '基于 LSTM 时序模型的未来 6 小时浓度趋势预测', 'TensorFlow 2.21 + Keras'],
        ['预警引擎', '超标自动检测、三级分级告警、数据库持久化', 'Flask + MySQL'],
        ['监控看板', '实时指标卡片、预测曲线图、预警列表一体化展示', 'Vue 3 + ECharts + Nginx'],
        ['报告导出', '历史排放数据 CSV 导出', 'Flask Response'],
    ]
)

p('系统架构：四层结构，前后端分离，容器化部署。', bold=True)
code(
    '表现层 (Vue.js + ECharts)         http://localhost (Nginx :80)\n'
    '业务层 (Flask RESTful API)        http://localhost:5000\n'
    '数据层 (TensorFlow + MySQL)       MySQL :3306\n'
    '部署层 (Docker + docker-compose)   一键编排'
)
page_break()

# ===================== 2 部署 =====================
doc.add_heading('2. 系统部署', level=1)
p('系统支持两种部署方式：Docker 容器化部署（推荐）和手动部署。')

doc.add_heading('2.1 Docker 部署（推荐）', level=2)

p('前置条件：', bold=True)
p('安装 Docker Desktop（https://www.docker.com/products/docker-desktop），启动后确认引擎正常运行：')
code('docker --version')
gap()

p('部署步骤：', bold=True)
p('步骤 1 — 进入项目根目录：')
code('cd /d "e:\\文件\\大二下作业\\Gas System"')
p('步骤 2 — 构建并启动所有服务：')
code('docker-compose up -d --build')
p('首次构建约 5-15 分钟（下载基础镜像和依赖包）。后续启动仅需数秒。')
gap()
p('步骤 3 — 验证服务状态：')
code('docker ps')
p('预期输出：gas_mysql (healthy)、gas_backend (Up)、gas_frontend (Up) 三个容器均处于运行状态。')
gap()
p('步骤 4 — 打开浏览器访问 http://localhost 进入监控看板。')
note('首次部署后数据库为空，需导入数据后看板才会显示有效数值。参考第 3 章。')

doc.add_heading('Docker 常用管理命令', level=2)
table(
    ['操作', '命令'],
    [
        ['查看运行状态', 'docker ps'],
        ['查看后端日志', 'docker logs gas_backend'],
        ['查看 MySQL 日志', 'docker logs gas_mysql'],
        ['进入后端容器', 'docker exec -it gas_backend bash'],
        ['重启后端 (更新模型后)', 'docker-compose restart backend'],
        ['停止所有服务', 'docker-compose down'],
        ['停止并清除数据卷', 'docker-compose down -v'],
        ['重建并重启', 'docker-compose up -d --build'],
    ]
)

doc.add_heading('2.2 手动部署', level=2)

p('前置条件：Python 3.10+、Node.js 16+、MySQL 8.0（需创建 gas_system 数据库，字符集 utf8mb4）。', bold=True)
gap()

p('后端部署：', bold=True)
code(
    'cd backend\n'
    'pip install -r requirements.txt\n'
    'python generate_real_data.py      # 生成并导入训练数据\n'
    'python data_analysis.py           # 特征工程\n'
    'python train_model.py             # 训练模型 (约2分钟)\n'
    'python app.py                     # 启动后端 (默认 :5000)'
)
gap()

p('前端部署：', bold=True)
code(
    'cd frontend\n'
    'npm install --registry=https://registry.npmmirror.com\n'
    'npm run serve                     # 启动开发服务器 (默认 :8080)'
)
gap()

p('完成后访问 http://localhost:8080。前端开发服务器已配置 /api 代理至后端 :5000。')

doc.add_heading('2.3 运行集成测试', level=2)
code('cd backend\npython test_integration.py')
p('预期输出：9/9 接口通过，4/4 性能指标达标。')
page_break()

# ===================== 3 数据管理 =====================
doc.add_heading('3. 数据管理', level=1)

p('系统管理三类核心数据：废气排放浓度、气象环境参数、设备运行工况。数据按分钟级精度对齐后统一存储。')

doc.add_heading('3.1 数据导入方式', level=2)

p('方式一：文件上传（CSV / Excel）', bold=True)
code(
    'curl -X POST http://localhost:5000/api/data/upload \\\n'
    '  -F "file=@/path/to/data.csv" -F "data_type=emission"'
)
p('data_type 可选值：emission | weather | equipment')
gap()

p('方式二：JSON 实时接入', bold=True)
code(
    'curl -X POST http://localhost:5000/api/data/realtime \\\n'
    '  -H "Content-Type: application/json" \\\n'
    '  -d \'{"data_type":"emission","records":[{...}]}\''
)
gap()

p('方式三：批量生成模拟数据', bold=True)
code('python generate_real_data.py')
p('生成 90 天 × 24 小时共 2160 条基于物理模型的数据，涵盖完整日周期和季节趋势。')

doc.add_heading('3.2 数据格式规范', level=2)

p('emission_data（废气排放）', bold=True)
table(
    ['字段', '类型', '必填', '说明'],
    [
        ['sensor_id', 'String', '是', '传感器标识'],
        ['timestamp', 'DateTime', '是', '采样时间，格式 YYYY-MM-DD HH:MM:SS'],
        ['voc_concentration', 'Float', '否', 'VOCs 浓度 (mg/m³)'],
        ['nox_concentration', 'Float', '否', 'NOx 浓度 (mg/m³)'],
        ['so2_concentration', 'Float', '否', 'SO₂ 浓度 (mg/m³)'],
    ]
)

p('weather_data（气象数据）', bold=True)
table(
    ['字段', '类型', '必填', '说明'],
    [
        ['station_id', 'String', '是', '气象站标识'],
        ['timestamp', 'DateTime', '是', '观测时间'],
        ['temperature', 'Float', '否', '温度 (°C)'],
        ['humidity', 'Float', '否', '相对湿度 (%)'],
        ['wind_speed', 'Float', '否', '风速 (m/s)'],
        ['wind_direction', 'Float', '否', '风向 (度)'],
    ]
)

p('equipment_data（设备数据）', bold=True)
table(
    ['字段', '类型', '必填', '说明'],
    [
        ['equipment_id', 'String', '是', '设备标识'],
        ['timestamp', 'DateTime', '是', '记录时间'],
        ['operating_load', 'Float', '否', '运行负荷 (%)'],
        ['production_phase', 'String', '否', '生产时段'],
        ['status', 'String', '否', '运行状态'],
    ]
)

doc.add_heading('3.3 CSV 文件模板', level=2)
code(
    '# emission_data.csv\n'
    'sensor_id,timestamp,voc_concentration,nox_concentration,so2_concentration\n'
    'S01,2026-06-03 10:00:00,120.5,45.6,10.2\n\n'
    '# weather_data.csv\n'
    'station_id,timestamp,temperature,humidity,wind_speed,wind_direction\n'
    'W01,2026-06-03 10:00:00,25.5,60.2,3.5,180\n\n'
    '# equipment_data.csv\n'
    'equipment_id,timestamp,operating_load,production_phase,status\n'
    'E01,2026-06-03 10:00:00,72.5,正常,running'
)
page_break()

# ===================== 4 模型 =====================
doc.add_heading('4. 预测模型', level=1)

doc.add_heading('4.1 模型架构', level=2)
p('采用双 LSTM 层 + Dropout 正则化的序列到序列架构：')
code(
    'Input(24 timesteps, 14 features)\n'
    '  → LSTM(128, return_sequences=True)\n'
    '  → Dropout(0.3)\n'
    '  → LSTM(64)\n'
    '  → Dropout(0.3)\n'
    '  → Dense(32, ReLU)\n'
    '  → Dense(6)                    # 输出未来 6 小时预测'
)
p('总参数量：124,902（< 500,000 约束）')

doc.add_heading('4.2 特征工程', level=2)
p('从原始数据提取 14 维特征：')
table(
    ['类别', '特征', '说明'],
    [
        ['原始数值', 'temperature, humidity, wind_speed, operating_load', '气象与工况参数'],
        ['时间编码', 'hour_sin/cos, day_of_week_sin/cos, is_workday', '周期信号正弦余弦编码'],
        ['滞后特征', 'voc_lag_1h, voc_lag_3h, voc_lag_6h', '前 1/3/6 小时 VOCs 浓度'],
        ['滚动统计', 'voc_rolling_6h_mean, voc_rolling_6h_std', '过去 6 小时均值与标准差'],
    ]
)

doc.add_heading('4.3 训练配置', level=2)
table(
    ['参数', '取值'],
    [
        ['损失函数', 'MSE (均方误差)'],
        ['优化器', 'Adam (lr=0.001)'],
        ['数据划分', '70% 训练 / 15% 验证 / 15% 测试（时序顺序，不随机）'],
        ['回调', 'EarlyStopping(patience=15) + ReduceLROnPlateau(factor=0.5) + ModelCheckpoint'],
        ['训练集规模', '1,487 条 (70%)'],
        ['验证集规模', '319 条 (15%)'],
        ['测试集规模', '319 条 (15%)'],
    ]
)

doc.add_heading('4.4 性能指标', level=2)
table(
    ['指标', '要求', '实测', '结论'],
    [
        ['准确率 (1-MAPE)', '≥ 75%', '82.61%', '达标'],
        ['单次推理耗时', '≤ 2秒', '~99ms', '达标'],
        ['参数量', '< 500,000', '124,902', '达标'],
        ['MAE', '-', '12.40 mg/m³', '-'],
        ['MSE', '-', '258.12', '-'],
    ]
)

doc.add_heading('4.5 模型训练流程', level=2)
p('在 backend 目录下依次执行：')
code(
    'python generate_real_data.py    # 步骤 1: 生成训练数据\n'
    'python data_analysis.py         # 步骤 2: 相关性分析 + 特征工程\n'
    'python train_model.py           # 步骤 3: 训练 + 评估 + 保存模型'
)
p('训练输出文件：vocs_lstm_model.keras（预测服务加载）、scaler.pkl（特征标准化）、feature_cols.npy（特征列名）。')
note('更换训练数据后需重新执行步骤 2-3，并重启后端服务使新模型生效。')
page_break()

# ===================== 5 前端看板 =====================
doc.add_heading('5. 监控看板', level=1)

doc.add_heading('5.1 页面布局', level=2)
p('访问 http://localhost (Docker) 或 http://localhost:8080 (开发模式) 进入看板。')
gap()
table(
    ['区域', '位置', '内容', '刷新频率'],
    [
        ['标题栏', '顶部', '系统名称、实时时钟、导出报告按钮', '-'],
        ['指标卡片 (×4)', '左侧', 'VOCs 浓度、温度、湿度、风速当前值', '5 秒'],
        ['预测趋势图', '右上方', '24 小时历史值 + 6 小时预测值 + 80mg 限值线', '30 秒'],
        ['预警列表', '右下方', '超标告警记录，按时间倒序排列', '10 秒'],
    ]
)

doc.add_heading('5.2 趋势图说明', level=2)
table(
    ['图例', '含义'],
    [
        ['蓝色实线', '过去 24 小时实测 VOCs 浓度'],
        ['黄色虚线', '未来 6 小时 AI 预测浓度'],
        ['红色虚线', '预警限值线 (80 mg/m³)'],
    ]
)

doc.add_heading('5.3 预警分级', level=2)
table(
    ['级别', '显示颜色', '触发条件', '建议操作'],
    [
        ['高 (error)', '红色', '超过 3 个预测值均超标', '立即响应，检查排放源'],
        ['中 (warn)', '黄色', '2-3 个预测值超标', '密切关注，准备应对'],
        ['低 (info)', '蓝色', '1 个预测值超标', '记录观察，持续跟踪'],
    ]
)
p('无超标时，预警列表区域显示"暂无预警信息"。')

doc.add_heading('5.4 报告导出', level=2)
p('点击标题栏"导出报告"按钮，浏览器自动下载包含最近 500 条历史排放记录的 CSV 文件。')
page_break()

# ===================== 6 API参考 =====================
doc.add_heading('6. API 接口参考', level=1)
p('Base URL: http://localhost:5000 | Content-Type: application/json | Charset: UTF-8')

doc.add_heading('6.1 接口总览', level=2)
table(
    ['接口', '方法', '功能', '返回'],
    [
        ['/api/data/upload', 'POST', '上传 CSV/Excel 数据文件', 'imported_rows, completeness'],
        ['/api/data/realtime', 'POST', '接收 JSON 实时数据', 'processed_records'],
        ['/api/realtime', 'GET', '获取最新四项监测指标', 'voc, temp, humidity, wind'],
        ['/api/prediction', 'GET', '获取 24h 历史 + 6h 预测', 'history[24], prediction[6]'],
        ['/api/vocs/prediction', 'GET', '预测并自动执行预警检查', 'predictions[6] + alert{}'],
        ['/api/alerts', 'GET', '查询历史预警记录', '[alert_record, ...]'],
        ['/api/report/export', 'GET', '导出 CSV 历史排放报告', 'text/csv 文件流'],
    ]
)

doc.add_heading('6.2 错误码', level=2)
table(
    ['状态码', '含义', '典型原因'],
    [
        ['200', '成功', '-'],
        ['400', '请求参数错误', '文件格式不支持 / 必填字段缺失 / 数据量不足'],
        ['500', '服务器内部错误', '数据库连接失败 / 模型推理异常'],
        ['503', '服务不可用', '模型文件缺失，需执行 train_model.py'],
    ]
)

doc.add_heading('6.3 请求示例', level=2)
p('文件上传：', bold=True)
code(
    'curl -X POST http://localhost:5000/api/data/upload \\\n'
    '  -F "file=@emission_202606.csv" -F "data_type=emission"'
)
gap()
p('实时数据：', bold=True)
code(
    'curl -X POST http://localhost:5000/api/data/realtime \\\n'
    '  -H "Content-Type: application/json" \\\n'
    '  -d \'{"data_type":"weather","records":[{"station_id":"W01","timestamp":"2026-06-03 10:00:00","temperature":25.5,"humidity":60.2,"wind_speed":3.5}]}\''
)
gap()
p('获取预测：', bold=True)
code('curl http://localhost:5000/api/prediction')
page_break()

# ===================== 7 故障排查 =====================
doc.add_heading('7. 故障排查', level=1)

table(
    ['现象', '原因', '处理'],
    [
        ['浏览器无法访问 http://localhost', 'Docker 未启动或容器未运行', '执行 docker ps 检查，若无输出则执行 docker-compose up -d'],
        ['看板数据全部显示 0', '数据库无数据', '执行 python generate_real_data.py 或上传数据文件'],
        ['预测接口返回 400 "数据不足"', '数据量 < 30 条小时级记录', '确保导入至少 30 条跨小时的历史数据'],
        ['预测接口返回 503', '模型文件缺失', '执行 python data_analysis.py && python train_model.py'],
        ['Docker 启动报 "port already allocated"', '端口被占用', '修改 docker-compose.yml 端口映射，如 5000→5001, 80→8080'],
        ['pip install 下载失败', '网络连通性问题', '添加 -i https://pypi.tuna.tsinghua.edu.cn/simple 使用清华镜像'],
        ['容器状态 Restarting', '后端启动失败', '执行 docker logs gas_backend 查看错误日志'],
        ['数据库连接拒绝', 'MySQL 未就绪或密码错误', '确认 docker ps 中 MySQL 状态为 healthy，密码为 123456'],
    ]
)

page_break()

# ===================== 附录 =====================
doc.add_heading('附录 A：技术栈', level=1)
table(
    ['层级', '技术', '版本'],
    [
        ['前端框架', 'Vue.js', '3.2'],
        ['图表库', 'ECharts (vue-echarts)', '6.1 / 8.0'],
        ['HTTP', 'Axios', '1.16'],
        ['后端框架', 'Flask', '3.1.3'],
        ['ORM', 'Flask-SQLAlchemy', '3.1.1'],
        ['数据库', 'MySQL', '8.0'],
        ['数据库驱动', 'PyMySQL', '1.1.3'],
        ['深度学习', 'TensorFlow (Keras)', '2.21'],
        ['数据处理', 'pandas', '3.0'],
        ['机器学习', 'scikit-learn', '1.6'],
        ['可视化', 'matplotlib / seaborn', '3.10 / 0.13'],
        ['容器化', 'Docker + Compose', '29.x / 2.x'],
        ['Web 服务器', 'Nginx', 'Alpine'],
    ]
)

doc.add_heading('附录 B：项目结构', level=1)
code(
    'Gas-System/\n'
    '├── docker-compose.yml              # 三服务编排\n'
    '├── 使用手册.docx                    # 本文档\n'
    '├── backend/\n'
    '│   ├── app.py                      # Flask 主程序 (7 个 API)\n'
    '│   ├── models.py                   # ORM 模型 (4 表)\n'
    '│   ├── predictor.py                # VOCSPredictor 推理封装\n'
    '│   ├── alert.py                    # 预警触发逻辑\n'
    '│   ├── data_cleaner.py             # 数据清洗\n'
    '│   ├── data_analysis.py            # 数据分析 + 特征工程\n'
    '│   ├── train_model.py              # LSTM 训练 + 评估\n'
    '│   ├── generate_real_data.py       # 数据生成器\n'
    '│   ├── test_integration.py         # 集成测试\n'
    '│   ├── Dockerfile                  # 后端镜像\n'
    '│   └── requirements.txt            # Python 依赖\n'
    '├── frontend/\n'
    '│   ├── Dockerfile                  # 前端镜像\n'
    '│   ├── nginx.conf                  # Nginx 反向代理\n'
    '│   ├── package.json                # npm 依赖\n'
    '│   └── src/\n'
    '│       ├── views/DashboardView.vue # 监控看板主页\n'
    '│       ├── components/             # UI 组件\n'
    '│       └── utils/api.js            # API 封装\n'
    '└── .gitignore'
)

# ===================== 保存 =====================
if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r'e:\文件\大二下作业\Gas System\使用手册_新版.docx'
    doc.save(out)
    print(f'已生成: {out}')
