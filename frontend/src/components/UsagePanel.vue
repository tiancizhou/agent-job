<template>
  <div class="usage-backdrop" @click.self="emit('close')">
    <section class="usage-panel" aria-label="Token 用量">
      <header class="usage-panel__header">
        <div>
          <p class="usage-panel__eyebrow">Token 用量</p>
          <h2>{{ formatTokenCount(summary?.total_tokens || 0) }}</h2>
        </div>
        <button type="button" class="usage-panel__close" @click="emit('close')">关闭</button>
      </header>

      <div class="usage-panel__stats">
        <div class="usage-panel__stat">
          <span>输入</span>
          <strong>{{ formatTokenCount(summary?.prompt_tokens || 0) }}</strong>
        </div>
        <div class="usage-panel__stat">
          <span>输出</span>
          <strong>{{ formatTokenCount(summary?.completion_tokens || 0) }}</strong>
        </div>
        <div class="usage-panel__stat">
          <span>记录</span>
          <strong>{{ summary?.record_count || 0 }}</strong>
        </div>
        <div class="usage-panel__stat">
          <span>估算</span>
          <strong>{{ summary?.estimated_record_count || 0 }}</strong>
        </div>
      </div>

      <div class="usage-panel__section-title">
        <span>最近记录</span>
        <button type="button" @click="loadRecords">刷新</button>
      </div>

      <p v-if="error" class="usage-panel__message">{{ error }}</p>
      <p v-else-if="isLoading" class="usage-panel__message">正在加载用量记录...</p>
      <p v-else-if="records.length === 0" class="usage-panel__message">暂无用量记录</p>

      <div v-else class="usage-panel__records">
        <article v-for="record in records" :key="record.id" class="usage-record">
          <div class="usage-record__main">
            <div>
              <strong>{{ actionLabel(record.action) }}</strong>
              <span>{{ record.app_name || (record.app_id ? "已删除应用" : "未关联应用") }}</span>
            </div>
            <b>{{ formatTokenCount(record.total_tokens) }}</b>
          </div>
          <div class="usage-record__meta">
            <span>{{ record.model }}</span>
            <span :class="`usage-record__status usage-record__status--${record.status}`">{{ statusLabel(record.status) }}</span>
            <span v-if="record.is_estimated">估算</span>
            <time>{{ formatDate(record.created_at) }}</time>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue"
import { listUsageRecords, type UsageRecord, type UsageSummary } from "../api/index"

const props = defineProps<{
  summary: UsageSummary | null
}>()

const emit = defineEmits<{
  close: []
}>()

const records = ref<UsageRecord[]>([])
const isLoading = ref(false)
const error = ref("")

onMounted(loadRecords)

async function loadRecords() {
  isLoading.value = true
  error.value = ""
  try {
    records.value = await listUsageRecords(20, 0)
  } catch {
    error.value = "用量记录加载失败，请稍后重试。"
  } finally {
    isLoading.value = false
  }
}

function formatTokenCount(value: number): string {
  if (value >= 10000) return `${(value / 10000).toFixed(1)}万`
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return String(value)
}

function actionLabel(action: string): string {
  if (action === "name") return "命名"
  if (action === "generate") return "生成"
  if (action === "edit") return "编辑"
  return action
}

function statusLabel(status: string): string {
  if (status === "success") return "成功"
  if (status === "failed") return "失败"
  return status
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })
}
</script>

<style scoped>
.usage-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  justify-content: flex-end;
  padding: 70px 22px 22px;
  background: rgba(15, 23, 42, 0.16);
}

.usage-panel {
  width: min(420px, 100%);
  height: fit-content;
  max-height: calc(100dvh - 92px);
  overflow: auto;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.2);
  backdrop-filter: blur(18px);
}

.usage-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.usage-panel__eyebrow {
  margin: 0 0 6px;
  color: #64748b;
  font-size: 12px;
  font-weight: 760;
}

.usage-panel__header h2 {
  margin: 0;
  color: #0f172a;
  font-size: 30px;
  line-height: 1;
}

.usage-panel__close,
.usage-panel__section-title button {
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 8px 12px;
  background: #ffffff;
  color: #475569;
  font-size: 12px;
  font-weight: 720;
  cursor: pointer;
}

.usage-panel__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 16px 20px;
}

.usage-panel__stat {
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 10px;
  background: #f8fafc;
}

.usage-panel__stat span {
  display: block;
  margin-bottom: 5px;
  color: #64748b;
  font-size: 11px;
  font-weight: 720;
}

.usage-panel__stat strong {
  color: #0f172a;
  font-size: 15px;
}

.usage-panel__section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px 12px;
  color: #334155;
  font-size: 13px;
  font-weight: 780;
}

.usage-panel__message {
  margin: 0;
  padding: 14px 20px 22px;
  color: #64748b;
  font-size: 13px;
}

.usage-panel__records {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 20px 20px;
}

.usage-record {
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 12px;
  background: #ffffff;
}

.usage-record__main,
.usage-record__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.usage-record__main strong {
  display: block;
  color: #0f172a;
  font-size: 14px;
}

.usage-record__main span,
.usage-record__meta {
  color: #64748b;
  font-size: 12px;
}

.usage-record__main b {
  color: #0284c7;
  font-size: 15px;
}

.usage-record__meta {
  flex-wrap: wrap;
  justify-content: flex-start;
  margin-top: 8px;
}

.usage-record__meta span,
.usage-record__meta time {
  border-radius: 999px;
  padding: 4px 7px;
  background: #f1f5f9;
}

.usage-record__status--success {
  color: #047857;
  background: #dcfce7 !important;
}

.usage-record__status--failed {
  color: #b91c1c;
  background: #fee2e2 !important;
}

@media (max-width: 768px) {
  .usage-backdrop {
    align-items: flex-end;
    padding: 12px;
  }

  .usage-panel {
    width: 100%;
    max-height: calc(100dvh - 24px);
    border-radius: 24px;
  }

  .usage-panel__stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
