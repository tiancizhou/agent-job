<template>
  <div class="bubble-row" :class="role === 'user' ? 'bubble-row--user' : 'bubble-row--assistant'">
    <div class="bubble" :class="role === 'user' ? 'bubble--user' : 'bubble--assistant'">
      <span v-if="role === 'assistant' && !content" class="bubble__placeholder">
        <span class="bubble__dot" />
        正在生成项目文件...
      </span>
      <div v-else-if="isCodeStream" class="bubble__code-shell">
        <div class="bubble__code-header">
          <span class="bubble__code-dot" />
          正在生成项目文件
        </div>
        <pre ref="codeStreamRef" class="bubble__code-stream">{{ content }}</pre>
      </div>
      <span v-else class="bubble__content">{{ content }}</span>
    </div>

    <details v-if="role === 'assistant' && resultStatus" class="result-panel" :open="resultStatus !== 'active'">
      <summary class="result-panel__summary">
        <span class="result-panel__status" :class="`result-panel__status--${resultStatus}`" />
        <span class="result-panel__title">{{ resultTitle }}</span>
        <span class="result-panel__toggle">{{ resultStatus === 'active' ? '展开' : '收起' }}</span>
      </summary>

      <div class="result-panel__body">
        <p>{{ resultDescription }}</p>
        <p v-if="resultError && resultStatus !== 'active'" class="result-panel__error">{{ resultError }}</p>
        <div v-if="resultUrl && resultStatus === 'active'" class="result-panel__actions">
          <a :href="resultUrl" target="_blank" rel="noopener noreferrer" class="result-panel__btn result-panel__btn--primary">
            预览应用
          </a>
          <button type="button" class="result-panel__btn" @click="copyResultUrl">
            {{ copyButtonText }}
          </button>
          <a :href="resultUrl" target="_blank" rel="noopener noreferrer" class="result-panel__btn">
            新窗口打开
          </a>
        </div>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue"

const props = defineProps<{
  role: "user" | "assistant"
  content: string
  resultUrl?: string | null
  resultStatus?: string | null
  resultError?: string | null
}>()

const codeStreamRef = ref<HTMLElement | null>(null)
const copyButtonText = ref("复制链接")

const isCodeStream = computed(() => (
  props.role === "assistant"
  && props.resultStatus !== "active"
  && (
    props.content.includes("```html")
    || props.content.includes("```json")
    || props.content.includes('"files"')
    || props.content.includes('"changes"')
  )
))

watch(
  () => props.content,
  async () => {
    if (!isCodeStream.value) return
    await nextTick()
    const el = codeStreamRef.value
    if (el) el.scrollTop = el.scrollHeight
  },
)

const resultTitle = computed(() => {
  if (props.resultStatus === "active") return "应用已生成"
  if (props.resultStatus === "busy") return "生成任务较多"
  if (props.resultStatus === "failed") return "应用生成失败"
  if (props.resultStatus === "edit_failed") return "应用修改失败"
  return "应用生成中"
})

const resultDescription = computed(() => {
  if (props.resultStatus === "active") return "生成结果已自动收起，可以在右侧预览，也可以打开链接使用。"
  if (props.resultStatus === "busy") return "当前同时生成的任务较多，请稍后重新发送需求。"
  if (props.resultStatus === "failed") return "请调整需求后重新发送，快搭会继续尝试生成。"
  if (props.resultStatus === "edit_failed") return "已保留上一个可用版本，请调整需求后重新发送。"
  return "模型回复会保留在上方，生成完成后这里会自动收起。"
})

async function copyResultUrl() {
  if (!props.resultUrl) return
  const fullUrl = new URL(props.resultUrl, window.location.origin).toString()
  await navigator.clipboard.writeText(fullUrl)
  copyButtonText.value = "已复制"
  window.setTimeout(() => {
    copyButtonText.value = "复制链接"
  }, 1600)
}
</script>

<style scoped>
.bubble-row {
  display: flex;
  flex-direction: column;
}

.bubble-row--user {
  align-items: flex-end;
}

.bubble-row--assistant {
  align-items: flex-start;
}

.bubble {
  max-width: min(680px, 78%);
  padding: 13px 16px;
  border-radius: 20px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
}

.bubble--user {
  background: linear-gradient(135deg, #475569, #6366f1);
  color: #ffffff;
  border-bottom-right-radius: 7px;
  box-shadow: 0 16px 36px rgba(79, 70, 229, 0.2);
}

.bubble--assistant {
  background: rgba(255, 255, 255, 0.86);
  color: #0f172a;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-bottom-left-radius: 7px;
  box-shadow: 0 14px 38px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}

.bubble__placeholder {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #64748b;
  font-weight: 650;
}

.bubble__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #22d3ee;
  box-shadow: 0 0 18px rgba(34, 211, 238, 0.72);
  animation: bubble-pulse 1.2s ease-in-out infinite;
}

@keyframes bubble-pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.62; }
  50% { transform: scale(1); opacity: 1; }
}

.bubble__content {
  white-space: pre-wrap;
}

.bubble__code-shell {
  width: min(620px, 100%);
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 15px;
  background: #0f172a;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.bubble__code-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 720;
}

.bubble__code-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #22d3ee;
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.7);
}

.bubble__code-stream {
  max-height: 220px;
  margin: 0;
  overflow: auto;
  padding: 12px;
  color: #dbeafe;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.bubble__code-stream::-webkit-scrollbar {
  width: 6px;
}

.bubble__code-stream::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.4);
}

.bubble__code-stream::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.42);
  border-radius: 999px;
}

.result-panel {
  margin-top: 10px;
  width: min(520px, 78%);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.07);
  overflow: hidden;
  backdrop-filter: blur(14px);
}

.result-panel__summary {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px 13px;
  cursor: pointer;
  list-style: none;
  color: #334155;
  font-size: 13px;
  font-weight: 720;
}

.result-panel__summary::-webkit-details-marker {
  display: none;
}

.result-panel__status {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #22d3ee;
  box-shadow: 0 0 18px rgba(34, 211, 238, 0.48);
}

.result-panel__status--active {
  background: #10b981;
  box-shadow: 0 0 18px rgba(16, 185, 129, 0.45);
}

.result-panel__status--failed,
.result-panel__status--edit_failed {
  background: #ef4444;
  box-shadow: 0 0 18px rgba(239, 68, 68, 0.35);
}

.result-panel__title {
  flex: 1;
}

.result-panel__toggle {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 650;
}

.result-panel__body {
  padding: 0 13px 13px;
  border-top: 1px solid rgba(226, 232, 240, 0.72);
}

.result-panel__body p {
  margin: 10px 0 12px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.65;
}

.result-panel__body .result-panel__error {
  color: #b45309;
  font-weight: 650;
}

.result-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.result-panel__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(14, 165, 233, 0.24);
  border-radius: 999px;
  padding: 8px 12px;
  background: rgba(240, 249, 255, 0.82);
  color: #0369a1;
  text-decoration: none;
  font-family: inherit;
  font-size: 12px;
  font-weight: 720;
  cursor: pointer;
  transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.result-panel__btn--primary {
  border-color: rgba(16, 185, 129, 0.28);
  background: linear-gradient(135deg, #10b981, #06b6d4);
  color: #ffffff;
}

.result-panel__btn:hover {
  transform: translateY(-1px);
  border-color: rgba(14, 165, 233, 0.42);
  box-shadow: 0 10px 22px rgba(14, 165, 233, 0.14);
}

@media (max-width: 768px) {
  .bubble {
    max-width: 92%;
    padding: 12px 14px;
    font-size: 13px;
  }

  .bubble__code-shell {
    width: min(100%, calc(100vw - 48px));
  }

  .bubble__code-stream {
    max-height: 180px;
    font-size: 11px;
  }

  .result-panel {
    width: 92%;
  }

  .result-panel__actions {
    flex-direction: column;
  }

  .result-panel__btn {
    width: 100%;
  }
}
</style>
