<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="close">
        <div class="modal-panel">
          <div class="modal-header">
            <h3>数据导入</h3>
            <button class="modal-close" @click="close">&times;</button>
          </div>

          <div class="modal-body">
            <!-- 数据类型选择 -->
            <div class="form-group">
              <label class="form-label">数据类型</label>
              <div class="type-selector">
                <button
                  v-for="opt in dataTypes"
                  :key="opt.value"
                  :class="['type-btn', { active: dataType === opt.value }]"
                  @click="dataType = opt.value"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- 文件选择区域 -->
            <div class="form-group">
              <label class="form-label">选择文件</label>
              <div
                :class="['drop-zone', { dragover: isDragover, hasFile: selectedFile }]"
                @dragover.prevent="isDragover = true"
                @dragleave.prevent="isDragover = false"
                @drop.prevent="onDrop"
                @click="$refs.fileInput.click()"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  style="display:none"
                  @change="onFileChange"
                />
                <template v-if="!selectedFile">
                  <div class="drop-icon">📂</div>
                  <p class="drop-text">点击选择文件，或将 CSV / Excel 文件拖拽到此处</p>
                  <p class="drop-hint">支持 .csv / .xlsx / .xls 格式</p>
                </template>
                <template v-else>
                  <div class="file-info">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ selectedFile.name }}</span>
                    <span class="file-size">{{ formatSize(selectedFile.size) }}</span>
                    <button class="file-remove" @click.stop="removeFile">✕</button>
                  </div>
                </template>
              </div>
            </div>

            <!-- 上传进度 -->
            <div v-if="uploading" class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>

            <!-- 结果提示 -->
            <div v-if="result" :class="['result-box', result.error ? 'result-error' : 'result-success']">
              <template v-if="result.error">
                <span>导入失败：{{ result.message }}</span>
              </template>
              <template v-else>
                <span>导入成功！共 {{ result.imported_rows }} 条记录</span>
                <span v-if="result.before_completeness !== undefined" class="result-detail">
                  （数据完整性：{{ result.before_completeness }}% → {{ result.after_completeness }}%）
                </span>
              </template>
            </div>

            <!-- CSV 模板帮助 -->
            <details class="template-help">
              <summary>查看 CSV 文件格式要求</summary>
              <div class="template-content">
                <p class="template-title">emission（废气排放数据）</p>
                <code>sensor_id,timestamp,voc_concentration,nox_concentration,so2_concentration</code>
                <p class="template-title">weather（气象数据）</p>
                <code>station_id,timestamp,temperature,humidity,wind_speed,wind_direction</code>
                <p class="template-title">equipment（设备数据）</p>
                <code>equipment_id,timestamp,operating_load,production_phase,status</code>
              </div>
            </details>
          </div>

          <div class="modal-footer">
            <button class="btn-cancel" @click="close">取消</button>
            <button
              :class="['btn-upload', { disabled: !selectedFile || uploading }]"
              :disabled="!selectedFile || uploading"
              @click="doUpload"
            >
              {{ uploading ? '上传中...' : '开始导入' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from "vue";
import api from "@/utils/api";

const props = defineProps({
  visible: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "uploaded"]);

const dataTypes = [
  { label: "废气排放 (emission)", value: "emission" },
  { label: "气象数据 (weather)", value: "weather" },
  { label: "设备数据 (equipment)", value: "equipment" },
];

const dataType = ref("emission");
const selectedFile = ref(null);
const isDragover = ref(false);
const uploading = ref(false);
const progress = ref(0);
const result = ref(null);

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

function onFileChange(e) {
  const file = e.target.files[0];
  if (file) {
    selectedFile.value = file;
    result.value = null;
  }
}

function onDrop(e) {
  isDragover.value = false;
  const file = e.dataTransfer.files[0];
  if (file) {
    selectedFile.value = file;
    result.value = null;
  }
}

function removeFile() {
  selectedFile.value = null;
  result.value = null;
  if (document.querySelector('input[type="file"]')) {
    document.querySelector('input[type="file"]').value = "";
  }
}

async function doUpload() {
  if (!selectedFile.value || uploading.value) return;

  uploading.value = true;
  progress.value = 30;
  result.value = null;

  try {
    const res = await api.uploadData(selectedFile.value, dataType.value);
    progress.value = 100;
    result.value = { error: false, ...res };
    selectedFile.value = null;
    emit("uploaded", res);
  } catch (err) {
    progress.value = 0;
    const msg = err?.response?.data?.error || err?.message || "网络错误";
    result.value = { error: true, message: msg };
  } finally {
    uploading.value = false;
  }
}

function close() {
  selectedFile.value = null;
  result.value = null;
  progress.value = 0;
  emit("close");
}
</script>

<style scoped>
/* ---- 遮罩 ---- */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

/* ---- 面板 ---- */
.modal-panel {
  background: #16203a;
  border-radius: 16px;
  width: 520px;
  max-width: 95vw;
  border: 1px solid #2a3852;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e0e6f0;
  margin: 0;
}
.modal-close {
  background: none;
  border: none;
  color: #6b7a94;
  font-size: 22px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
.modal-close:hover { color: #e0e6f0; }

.modal-body {
  padding: 20px 24px;
}

/* ---- 表单 ---- */
.form-group { margin-bottom: 18px; }
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #8b98b0;
  margin-bottom: 8px;
}

/* ---- 类型选择器 ---- */
.type-selector { display: flex; gap: 8px; }
.type-btn {
  flex: 1;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #8b98b0;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.type-btn:hover { border-color: #2e7bcf; color: #c0d0e8; }
.type-btn.active {
  background: rgba(46, 123, 207, 0.15);
  border-color: #2e7bcf;
  color: #00d4ff;
}

/* ---- 拖拽区 ---- */
.drop-zone {
  border: 2px dashed rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 28px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.drop-zone:hover,
.drop-zone.dragover {
  border-color: #2e7bcf;
  background: rgba(46, 123, 207, 0.06);
}
.drop-zone.hasFile {
  border-color: #10b981;
  border-style: solid;
  background: rgba(16, 185, 129, 0.06);
  padding: 16px;
}
.drop-icon { font-size: 32px; margin-bottom: 8px; }
.drop-text { font-size: 13px; color: #c0d0e8; margin: 4px 0; }
.drop-hint { font-size: 11px; color: #576580; margin: 4px 0; }

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.file-icon { font-size: 20px; }
.file-name { font-size: 13px; color: #e0e6f0; flex: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { font-size: 11px; color: #576580; }
.file-remove {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.file-remove:hover { background: rgba(239, 68, 68, 0.25); }

/* ---- 进度条 ---- */
.progress-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #2e7bcf);
  border-radius: 2px;
  transition: width 0.3s;
}

/* ---- 结果 ---- */
.result-box {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}
.result-success { background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
.result-error { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }
.result-detail { display: block; font-size: 11px; opacity: 0.8; margin-top: 4px; }

/* ---- 模板帮助 ---- */
.template-help {
  margin-top: 16px;
  font-size: 12px;
  color: #6b7a94;
  cursor: pointer;
}
.template-help summary { margin-bottom: 8px; }
.template-help summary:hover { color: #8b98b0; }
.template-content {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 12px;
}
.template-title {
  font-size: 11px;
  color: #00d4ff;
  margin: 6px 0 2px;
}
.template-content code {
  display: block;
  font-size: 10px;
  color: #8b98b0;
  font-family: Consolas, monospace;
  word-break: break-all;
}

/* ---- 底部按钮 ---- */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.btn-cancel {
  padding: 8px 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #c0d0e8;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-cancel:hover { background: rgba(255, 255, 255, 0.1); }
.btn-upload {
  padding: 8px 24px;
  background: linear-gradient(135deg, #00d4ff, #009cbb);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-upload:hover:not(.disabled) { opacity: 0.85; }
.btn-upload.disabled { opacity: 0.4; cursor: not-allowed; }

/* ---- 过渡动画 ---- */
.modal-enter-active, .modal-leave-active { transition: opacity 0.25s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
