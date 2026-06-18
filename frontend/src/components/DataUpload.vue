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
            <!-- 文件选择区域 -->
            <div class="form-group">
              <label class="form-label">选择文件（支持多选）</label>
              <div
                :class="['drop-zone', { dragover: isDragover, hasFile: files.length > 0 }]"
                @dragover.prevent="isDragover = true"
                @dragleave.prevent="isDragover = false"
                @drop.prevent="onDrop"
                @click="$refs.fileInput.click()"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  multiple
                  style="display:none"
                  @change="onFileChange"
                />
                <template v-if="files.length === 0">
                  <div class="drop-icon">📂</div>
                  <p class="drop-text">点击选择文件，或将 CSV / Excel 文件拖拽到此处</p>
                  <p class="drop-hint">支持 .csv / .xlsx / .xls 格式，可一次选择多个文件，系统自动识别数据类型</p>
                </template>
                <template v-else>
                  <div class="file-list">
                    <div v-for="(f, i) in files" :key="i" class="file-item">
                      <span class="file-icon">📄</span>
                      <div class="file-meta">
                        <span class="file-name">{{ f.file.name }}</span>
                        <span class="file-type">{{ inferDataTypeLabel(f.file.name) }}</span>
                      </div>
                      <span class="file-size">{{ formatSize(f.file.size) }}</span>
                      <button class="file-remove" @click.stop="removeFile(i)" :disabled="uploading">✕</button>
                    </div>
                  </div>
                  <p class="drop-hint" style="margin-top:8px">点击继续添加文件</p>
                </template>
              </div>
            </div>

            <!-- 上传进度：逐文件展示 -->
            <div v-if="uploading" class="upload-status">
              <div class="status-header">
                <span>{{ statusText }}</span>
                <span>{{ completedCount }} / {{ totalCount }}</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: overallProgress + '%' }"></div>
              </div>
              <!-- 逐文件结果 -->
              <div v-for="(fr, i) in fileResults" :key="i" :class="['file-result', fr.error ? 'fr-error' : 'fr-ok']">
                <span class="fr-icon">{{ fr.error ? '✗' : '✓' }}</span>
                <span class="fr-name">{{ fr.filename }}</span>
                <span class="fr-msg">{{ fr.error ? fr.message : fr.imported_rows + ' 条' }}</span>
              </div>
            </div>

            <!-- 最终汇总 -->
            <div v-if="finalResult" :class="['result-box', finalResult.hasError ? 'result-error' : 'result-success']">
              <span>导入完成：{{ finalResult.okCount }}/{{ finalResult.total }} 个文件成功，共 {{ finalResult.totalRows }} 条记录</span>
            </div>

            <!-- CSV 模板帮助 -->
            <details class="template-help">
              <summary>查看 CSV / Excel 文件格式要求</summary>
              <div class="template-content">
                <p class="template-note">系统会根据文件名自动识别数据类型。包含 "emission" 或 "废气" 识别为排放数据，包含 "weather" 或 "气象" 识别为气象数据，包含 "equipment" 或 "设备" 识别为设备数据，其余默认为排放数据。</p>
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
            <button
              class="btn-reimport"
              :disabled="reimporting || !hasLastUpload"
              @click="doReimport"
            >
              {{ reimporting ? '导入中...' : '⚡ 一键导入上次数据' }}
            </button>
            <div class="footer-right">
              <button class="btn-cancel" @click="close" :disabled="uploading">取消</button>
              <button
                :class="['btn-upload', { disabled: files.length === 0 || uploading }]"
                :disabled="files.length === 0 || uploading"
                @click="doUpload"
              >
                {{ uploading ? '上传中...' : `开始导入 (${files.length} 个文件)` }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from "vue";
import api from "@/utils/api";

defineProps({
  visible: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "uploaded"]);

const files = ref([]);
const isDragover = ref(false);
const uploading = ref(false);
const reimporting = ref(false);
const completedCount = ref(0);
const totalCount = ref(0);
const fileResults = ref([]);
const finalResult = ref(null);

// 检查是否有上次上传记录
const hasLastUpload = computed(() => {
  try {
    const types = JSON.parse(localStorage.getItem("gas_last_upload") || "[]");
    return types.length > 0;
  } catch {
    return false;
  }
});

const overallProgress = computed(() => {
  if (totalCount.value === 0) return 0;
  return Math.round((completedCount.value / totalCount.value) * 100);
});

const statusText = computed(() => {
  if (totalCount.value === 0) return "准备中...";
  return `正在导入第 ${completedCount.value + 1} / ${totalCount.value} 个文件`;
});

function inferDataType(filename) {
  const name = filename.toLowerCase();
  if (/weather|气象|气候/.test(name)) return "weather";
  if (/equipment|设备|机器/.test(name)) return "equipment";
  return "emission";
}

function inferDataTypeLabel(filename) {
  const map = { weather: "气象数据", equipment: "设备数据", emission: "排放数据" };
  return map[inferDataType(filename)] || "排放数据";
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

function addFiles(fileList) {
  for (let i = 0; i < fileList.length; i++) {
    const f = fileList[i];
    // 去重：同名同大小视为重复
    const dup = files.value.find((x) => x.file.name === f.name && x.file.size === f.size);
    if (!dup) {
      files.value.push({ file: f });
    }
  }
  finalResult.value = null;
  fileResults.value = [];
}

function onFileChange(e) {
  if (e.target.files.length > 0) {
    addFiles(e.target.files);
    e.target.value = "";
  }
}

function onDrop(e) {
  isDragover.value = false;
  if (e.dataTransfer.files.length > 0) {
    addFiles(e.dataTransfer.files);
  }
}

function removeFile(index) {
  files.value.splice(index, 1);
  finalResult.value = null;
}

async function doUpload() {
  if (files.value.length === 0 || uploading.value) return;

  uploading.value = true;
  completedCount.value = 0;
  totalCount.value = files.value.length;
  fileResults.value = [];
  finalResult.value = null;

  let totalRows = 0;
  let okCount = 0;
  let hasError = false;

  for (let i = 0; i < files.value.length; i++) {
    const { file } = files.value[i];
    const dataType = inferDataType(file.name);

    try {
      const res = await api.uploadData(file, dataType);
      totalRows += res.imported_rows || 0;
      okCount++;
      fileResults.value.push({
        filename: file.name,
        error: false,
        imported_rows: res.imported_rows,
        message: `导入成功`,
      });
      // 记录到 localStorage
      const types = JSON.parse(localStorage.getItem("gas_last_upload") || "[]");
      if (!types.includes(dataType)) types.push(dataType);
      localStorage.setItem("gas_last_upload", JSON.stringify(types));
    } catch (err) {
      hasError = true;
      const msg = err?.response?.data?.error || err?.message || "网络错误";
      fileResults.value.push({
        filename: file.name,
        error: true,
        message: msg,
      });
    }
    completedCount.value = i + 1;
  }

  finalResult.value = { total: files.value.length, okCount, totalRows, hasError };
  files.value = [];
  uploading.value = false;
  if (totalRows > 0) emit("uploaded", { imported_rows: totalRows });
}

async function doReimport() {
  if (reimporting.value) return;
  reimporting.value = true;
  finalResult.value = null;
  fileResults.value = [];
  try {
    const res = await api.reimportData();
    const detail = res.results || {};
    for (const [type, r] of Object.entries(detail)) {
      fileResults.value.push({
        filename: type,
        error: !!r.error,
        imported_rows: r.imported_rows || 0,
        message: r.error || "导入成功",
      });
    }
    finalResult.value = {
      total: Object.keys(detail).length,
      okCount: Object.values(detail).filter((r) => !r.error).length,
      totalRows: res.total_imported || 0,
      hasError: false,
    };
    emit("uploaded", res);
  } catch (err) {
    const msg = err?.response?.data?.error || err?.message || "网络错误";
    finalResult.value = { total: 1, okCount: 0, totalRows: 0, hasError: true };
    fileResults.value.push({ filename: "一键导入", error: true, message: msg });
  } finally {
    reimporting.value = false;
  }
}

function close() {
  if (uploading.value) return;
  files.value = [];
  fileResults.value = [];
  finalResult.value = null;
  emit("close");
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}
.modal-panel {
  background: #16203a;
  border-radius: 16px;
  width: 540px;
  max-width: 95vw;
  max-height: 85vh;
  border: 1px solid #2a3852;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}
.modal-header h3 { font-size: 16px; font-weight: 600; color: #e0e6f0; margin: 0; }
.modal-close {
  background: none; border: none; color: #6b7a94; font-size: 22px;
  cursor: pointer; padding: 0 4px; line-height: 1;
}
.modal-close:hover { color: #e0e6f0; }
.modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.form-group { margin-bottom: 18px; }
.form-label { display: block; font-size: 13px; font-weight: 600; color: #8b98b0; margin-bottom: 8px; }

.drop-zone {
  border: 2px dashed rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 28px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.drop-zone:hover,
.drop-zone.dragover { border-color: #2e7bcf; background: rgba(46, 123, 207, 0.06); }
.drop-zone.hasFile {
  border-color: #10b981; border-style: solid;
  background: rgba(16, 185, 129, 0.06); padding: 12px 16px;
}
.drop-icon { font-size: 32px; margin-bottom: 8px; }
.drop-text { font-size: 13px; color: #c0d0e8; margin: 4px 0; }
.drop-hint { font-size: 11px; color: #576580; margin: 4px 0; }

/* 多文件列表 */
.file-list { display: flex; flex-direction: column; gap: 8px; }
.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 8px 12px;
  text-align: left;
}
.file-icon { font-size: 18px; flex-shrink: 0; }
.file-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.file-name { font-size: 13px; color: #e0e6f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-type { font-size: 11px; color: #00d4ff; }
.file-size { font-size: 11px; color: #576580; white-space: nowrap; flex-shrink: 0; }
.file-remove {
  background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171; border-radius: 50%; width: 24px; height: 24px;
  font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.file-remove:hover:not(:disabled) { background: rgba(239, 68, 68, 0.25); }
.file-remove:disabled { opacity: 0.3; cursor: not-allowed; }

/* 上传状态 */
.upload-status { margin-top: 12px; }
.status-header { display: flex; justify-content: space-between; font-size: 12px; color: #8b98b0; margin-bottom: 6px; }

.progress-bar { height: 4px; background: rgba(255, 255, 255, 0.06); border-radius: 2px; margin-bottom: 10px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #2e7bcf); border-radius: 2px; transition: width 0.3s; }

.file-result { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 6px; margin-bottom: 4px; font-size: 12px; }
.fr-ok { background: rgba(16, 185, 129, 0.08); }
.fr-error { background: rgba(239, 68, 68, 0.08); }
.fr-icon { width: 16px; text-align: center; font-weight: 700; flex-shrink: 0; }
.fr-ok .fr-icon { color: #10b981; }
.fr-error .fr-icon { color: #f87171; }
.fr-name { flex: 1; color: #c0d0e8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fr-msg { color: #6b7a94; white-space: nowrap; flex-shrink: 0; }

.result-box { margin-top: 12px; padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.result-success { background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
.result-error { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }

.template-help { margin-top: 16px; font-size: 12px; color: #6b7a94; cursor: pointer; }
.template-help summary { margin-bottom: 8px; }
.template-help summary:hover { color: #8b98b0; }
.template-content { background: rgba(0, 0, 0, 0.2); border-radius: 8px; padding: 12px; }
.template-note { font-size: 11px; color: #8b98b0; margin-bottom: 10px; line-height: 1.5; }
.template-title { font-size: 11px; color: #00d4ff; margin: 6px 0 2px; }
.template-content code {
  display: block; font-size: 10px; color: #8b98b0;
  font-family: Consolas, monospace; word-break: break-all;
}

.modal-footer { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 14px 24px; border-top: 1px solid rgba(255, 255, 255, 0.06); flex-shrink: 0; }
.footer-right { display: flex; gap: 10px; }
.btn-cancel {
  padding: 8px 20px; background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1); color: #c0d0e8;
  border-radius: 8px; font-size: 13px; cursor: pointer; transition: background 0.2s;
}
.btn-cancel:hover { background: rgba(255, 255, 255, 0.1); }
.btn-cancel:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-reimport {
  padding: 8px 18px;
  background: rgba(0, 212, 255, 0.08);
  color: #00d4ff;
  border: 1px dashed rgba(0, 212, 255, 0.35);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.btn-reimport:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.15);
  border-color: #00d4ff;
  border-style: solid;
}
.btn-reimport:disabled { opacity: 0.35; cursor: not-allowed; }
.btn-upload {
  padding: 8px 24px; background: linear-gradient(135deg, #00d4ff, #009cbb);
  color: #fff; border: none; border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: opacity 0.2s; white-space: nowrap;
}
.btn-upload:hover:not(.disabled) { opacity: 0.85; }
.btn-upload.disabled { opacity: 0.4; cursor: not-allowed; }

.modal-enter-active, .modal-leave-active { transition: opacity 0.25s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
