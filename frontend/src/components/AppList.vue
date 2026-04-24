<template>
  <div class="app-list">
    <div class="app-list__header">
      <span class="app-list__title">QuickApp</span>
      <button class="app-list__new-btn" @click="emit('new-app')">
        + 新建应用
      </button>
    </div>

    <div class="app-list__items">
      <div
        v-for="app in apps"
        :key="app.id"
        class="app-list__item"
        :class="{ 'app-list__item--active': app.id === selectedAppId }"
        @click="selectApp(app.id)"
      >
        <template v-if="confirmingDeleteId === app.id">
          <span class="app-list__confirm-text">确认删除？</span>
          <button class="app-list__confirm-btn" type="button" @click.stop="confirmDelete(app.id)">确认</button>
          <button class="app-list__cancel-btn" type="button" @click.stop="confirmingDeleteId = null">取消</button>
        </template>
        <template v-else>
          <span class="app-list__item-name" :title="app.name">{{ app.name }}</span>
          <span
            class="app-list__badge"
            :class="`app-list__badge--${app.status}`"
          >{{ statusLabel(app.status) }}</span>
          <button class="app-list__delete-btn" type="button" @click.stop="confirmingDeleteId = app.id">删除</button>
        </template>
      </div>

      <div v-if="apps.length === 0" class="app-list__empty">
        暂无应用
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import type { App } from "../api/index"

defineProps<{
  apps: App[]
  selectedAppId: string | null
}>()

const emit = defineEmits<{
  select: [id: string]
  delete: [id: string]
  "new-app": []
}>()

const confirmingDeleteId = ref<string | null>(null)

function selectApp(id: string) {
  confirmingDeleteId.value = null
  emit("select", id)
}

function confirmDelete(id: string) {
  confirmingDeleteId.value = null
  emit("delete", id)
}

function statusLabel(status: App["status"]): string {
  switch (status) {
    case "creating": return "生成中"
    case "active": return "正常"
    case "failed": return "失败"
    default: return status
  }
}
</script>

<style scoped>
.app-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  color: #111827;
  background: #ffffff;
}

.app-list__header {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px 16px 18px;
  border-bottom: 1px solid #eef0f4;
}

.app-list__title {
  font-size: 18px;
  font-weight: 760;
  color: #111827;
  letter-spacing: -0.03em;
}

.app-list__new-btn {
  width: 100%;
  padding: 10px 12px;
  background: #111827;
  color: #ffffff;
  border: none;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
  text-align: center;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.14);
}

.app-list__new-btn:hover {
  background: #1f2937;
  box-shadow: 0 14px 28px rgba(17, 24, 39, 0.18);
  transform: translateY(-1px);
}

.app-list__items {
  flex: 1;
  overflow-y: auto;
  padding: 12px 10px;
}

.app-list__items::-webkit-scrollbar {
  width: 4px;
}

.app-list__items::-webkit-scrollbar-track {
  background: transparent;
}

.app-list__items::-webkit-scrollbar-thumb {
  background: rgba(17, 24, 39, 0.14);
  border-radius: 4px;
}

.app-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 11px 12px;
  border: 1px solid transparent;
  border-radius: 14px;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, box-shadow 0.12s;
  margin-bottom: 6px;
}

.app-list__item:hover {
  background: #f8faff;
  border-color: #eef2ff;
}

.app-list__item--active {
  background: #f5f7ff;
  border-color: #c7d2fe;
  box-shadow: 0 10px 24px rgba(79, 70, 229, 0.08);
}

.app-list__item--active:hover {
  background: #f5f7ff;
  border-color: #c7d2fe;
}

.app-list__item-name {
  font-size: 13px;
  font-weight: 620;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.app-list__confirm-text {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  font-weight: 650;
  color: #991b1b;
}

.app-list__delete-btn,
.app-list__confirm-btn,
.app-list__cancel-btn {
  flex-shrink: 0;
  border: none;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 650;
  cursor: pointer;
}

.app-list__delete-btn {
  display: none;
  color: #dc2626;
  background: #fef2f2;
}

.app-list__item:hover .app-list__delete-btn {
  display: inline-flex;
}

.app-list__confirm-btn {
  color: #ffffff;
  background: #dc2626;
}

.app-list__cancel-btn {
  color: #4b5563;
  background: #f3f4f6;
}

.app-list__badge {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 650;
  padding: 3px 8px;
  border-radius: 999px;
}

.app-list__badge--creating {
  background: #eef2ff;
  color: #4f46e5;
}

.app-list__badge--active {
  background: #ecfdf5;
  color: #047857;
}

.app-list__badge--failed {
  background: #fef2f2;
  color: #dc2626;
}

.app-list__empty {
  margin: 24px 8px;
  padding: 24px 12px;
  border: 1px dashed #e5e7eb;
  border-radius: 16px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
  background: #fafafa;
}

@media (max-width: 768px) {
  .app-list__header {
    padding: 18px 16px 14px;
  }

  .app-list__title {
    font-size: 20px;
  }

  .app-list__new-btn {
    padding: 12px 14px;
    font-size: 14px;
  }

  .app-list__items {
    padding: 12px;
  }

  .app-list__item {
    padding: 13px 12px;
    border-color: #eef2ff;
    border-radius: 16px;
  }

  .app-list__delete-btn {
    display: inline-flex;
  }
}
</style>
