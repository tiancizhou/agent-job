<template>
  <div class="ea">
    <div class="ea__aura" />
    <section class="ea__shell">

      <div class="ea__header">
        <div>
          <span class="ea__eyebrow">ADMIN ACCESS</span>
          <h2>后台管理</h2>
          <p>管理用户访问权限与应用生成风格库。</p>
        </div>
        <button class="ea__back" type="button" @click="emit('close')">返回应用生成</button>
      </div>

      <div class="ea__tabs">
        <button
          class="ea__tab"
          :class="{ 'ea__tab--active': tab === 'employees' }"
          type="button"
          @click="tab = 'employees'"
        >用户管理</button>
        <button
          class="ea__tab"
          :class="{ 'ea__tab--active': tab === 'styles' }"
          type="button"
          @click="tab = 'styles'"
        >风格管理</button>
      </div>

      <!-- ── Employee tab ── -->
      <template v-if="tab === 'employees'">
        <div class="ea__stats">
          <div class="ea__stat"><span>全部用户</span><strong>{{ employees.length }}</strong></div>
          <div class="ea__stat"><span>可用用户</span><strong>{{ activeCount }}</strong></div>
          <div class="ea__stat"><span>已禁用</span><strong>{{ disabledCount }}</strong></div>
        </div>

        <form class="ea__form" @submit.prevent="addEmployee">
          <div class="ea__field">
            <label>用户名</label>
            <input v-model="employeeNo" placeholder="例如 10001" inputmode="numeric" />
          </div>
          <div class="ea__field">
            <label>姓名</label>
            <input v-model="empName" placeholder="请输入用户姓名" />
          </div>
          <button class="ea__add" :disabled="!canAdd" type="submit">新增用户</button>
        </form>

        <div v-if="empError" class="ea__error">{{ empError }}</div>

        <div class="ea__list-card">
          <div class="ea__list-head">
            <h3>用户访问名单</h3>
            <p>禁用后该用户将不能继续登录 QuickDa。</p>
          </div>
          <div class="ea__list">
            <div v-for="employee in employees" :key="employee.employee_no" class="ea__item">
              <div class="ea__identity">
                <span class="ea__avatar">{{ employee.name.slice(0, 1) || employee.employee_no.slice(-1) }}</span>
                <div>
                  <strong>{{ employee.name }}</strong>
                  <span>用户名 {{ employee.employee_no }}</span>
                </div>
              </div>
              <div class="ea__actions">
                <span :class="`ea__status ea__status--${employee.status}`">
                  {{ employee.status === 'active' ? '可用' : '已禁用' }}
                </span>
                <button v-if="employee.status === 'active'" class="ea__btn--danger" type="button" @click="disable(employee.employee_no)">禁用</button>
              </div>
            </div>
            <div v-if="employees.length === 0" class="ea__empty">暂无用户，请先新增可登录用户。</div>
          </div>
        </div>
      </template>

      <!-- ── Styles tab ── -->
      <template v-if="tab === 'styles'">
        <form class="ea__form ea__form--col" @submit.prevent="addStyle">
          <div class="ea__row">
            <div class="ea__field">
              <label>风格名称</label>
              <input v-model="styleName" placeholder="例如：纸雕风格" />
            </div>
            <div class="ea__field ea__field--narrow">
              <label>排序</label>
              <input v-model.number="styleSortOrder" type="number" min="0" placeholder="0" />
            </div>
          </div>
          <div class="ea__field">
            <label>风格提示词</label>
            <textarea v-model="stylePrompt" class="ea__textarea" rows="6" placeholder="在此粘贴完整的风格提示词..." />
          </div>
          <button class="ea__add" :disabled="!canAddStyle" type="submit">新增风格</button>
        </form>

        <div v-if="styleError" class="ea__error">{{ styleError }}</div>

        <div class="ea__list-card">
          <div class="ea__list-head">
            <h3>风格库</h3>
            <p>仅「激活」状态的风格对普通用户可见。</p>
          </div>
          <div class="ea__list">
            <div v-for="style in adminStyles" :key="style.id" class="ea__item ea__item--style">
              <template v-if="editingStyleId === style.id">
                <div class="ea__inline-edit">
                  <div class="ea__row">
                    <div class="ea__field">
                      <label>名称</label>
                      <input v-model="editStyleName" />
                    </div>
                    <div class="ea__field ea__field--narrow">
                      <label>排序</label>
                      <input v-model.number="editStyleSortOrder" type="number" min="0" />
                    </div>
                  </div>
                  <div class="ea__field">
                    <label>提示词</label>
                    <textarea v-model="editStylePrompt" class="ea__textarea" rows="6" />
                  </div>
                  <div class="ea__inline-edit-actions">
                    <button class="ea__btn--save" type="button" @click="saveStyleEdit(style.id)">保存</button>
                    <button class="ea__btn--cancel" type="button" @click="editingStyleId = null">取消</button>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="ea__style-body">
                  <div class="ea__style-meta">
                    <strong>{{ style.name }}</strong>
                    <span class="ea__style-sort">排序 {{ style.sort_order }}</span>
                  </div>
                  <p class="ea__style-preview">{{ style.prompt.slice(0, 80) }}{{ style.prompt.length > 80 ? '…' : '' }}</p>
                </div>
                <div class="ea__actions">
                  <span
                    class="ea__status"
                    :class="style.is_active ? 'ea__status--active' : 'ea__status--disabled'"
                    style="cursor:pointer"
                    @click="toggleStyleActive(style)"
                  >
                    {{ style.is_active ? '激活' : '未激活' }}
                  </span>
                  <button type="button" @click="startEdit(style)">编辑</button>
                  <button class="ea__btn--danger" type="button" @click="removeStyle(style.id)">删除</button>
                </div>
              </template>
            </div>
            <div v-if="adminStyles.length === 0" class="ea__empty">暂无风格，请先新增。</div>
          </div>
        </div>
      </template>

    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import {
  createEmployee, disableEmployee, listEmployees, type Employee,
  createStyle, deleteStyle, listAdminStyles, updateStyle, type Style,
} from "../api/index"

const emit = defineEmits<{ close: [] }>()

const tab = ref<"employees" | "styles">("employees")

// ── Employees ──
const employees = ref<Employee[]>([])
const employeeNo = ref("")
const empName = ref("")
const empError = ref("")

const canAdd = computed(() => /^\d{5}$/.test(employeeNo.value.trim()) && empName.value.trim().length > 0)
const activeCount = computed(() => employees.value.filter((e) => e.status === "active").length)
const disabledCount = computed(() => employees.value.filter((e) => e.status === "disabled").length)

async function loadEmployees() {
  employees.value = await listEmployees()
}

async function addEmployee() {
  if (!canAdd.value) return
  empError.value = ""
  try {
    const employee = await createEmployee(employeeNo.value.trim(), empName.value.trim())
    employees.value = [employee, ...employees.value]
    employeeNo.value = ""
    empName.value = ""
  } catch {
    empError.value = "新增失败，用户名可能已存在。"
  }
}

async function disable(no: string) {
  const updated = await disableEmployee(no)
  employees.value = employees.value.map((e) => e.employee_no === no ? updated : e)
}

// ── Styles ──
const adminStyles = ref<Style[]>([])
const styleName = ref("")
const stylePrompt = ref("")
const styleSortOrder = ref(0)
const styleError = ref("")

const editingStyleId = ref<string | null>(null)
const editStyleName = ref("")
const editStylePrompt = ref("")
const editStyleSortOrder = ref(0)

const canAddStyle = computed(() => styleName.value.trim().length > 0 && stylePrompt.value.trim().length > 0)

async function loadAdminStyles() {
  adminStyles.value = await listAdminStyles()
}

async function addStyle() {
  if (!canAddStyle.value) return
  styleError.value = ""
  try {
    const style = await createStyle({
      name: styleName.value.trim(),
      prompt: stylePrompt.value.trim(),
      sort_order: styleSortOrder.value,
    })
    adminStyles.value = [style, ...adminStyles.value]
    styleName.value = ""
    stylePrompt.value = ""
    styleSortOrder.value = 0
  } catch {
    styleError.value = "新增失败，请稍后重试。"
  }
}

function startEdit(style: Style) {
  editingStyleId.value = style.id
  editStyleName.value = style.name
  editStylePrompt.value = style.prompt
  editStyleSortOrder.value = style.sort_order
}

async function saveStyleEdit(id: string) {
  const name = editStyleName.value.trim()
  const prompt = editStylePrompt.value.trim()
  if (!name || !prompt) return
  const updated = await updateStyle(id, { name, prompt, sort_order: editStyleSortOrder.value })
  adminStyles.value = adminStyles.value.map((s) => s.id === id ? updated : s)
  editingStyleId.value = null
}

async function toggleStyleActive(style: Style) {
  const updated = await updateStyle(style.id, { is_active: !style.is_active })
  adminStyles.value = adminStyles.value.map((s) => s.id === style.id ? updated : s)
}

async function removeStyle(id: string) {
  await deleteStyle(id)
  adminStyles.value = adminStyles.value.filter((s) => s.id !== id)
}

onMounted(() => {
  loadEmployees()
  loadAdminStyles()
})
</script>

<style scoped>
* { box-sizing: border-box; }

.ea {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  background:
    radial-gradient(circle at 14% 18%, rgba(56, 189, 248, 0.18) 0%, transparent 28%),
    radial-gradient(circle at 86% 16%, rgba(251, 146, 60, 0.16) 0%, transparent 26%),
    linear-gradient(135deg, #f8fbff 0%, #fff7ed 48%, #f0f9ff 100%);
  position: relative;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

.ea__aura {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 20% 20%, rgba(34, 211, 238, 0.12), transparent 30%),
    radial-gradient(circle at 80% 80%, rgba(251, 146, 60, 0.1), transparent 28%);
}

.ea__shell {
  position: relative;
  z-index: 1;
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.ea__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.ea__eyebrow {
  color: #0284c7;
  font-size: 11px;
  font-weight: 820;
  letter-spacing: 0.16em;
}

.ea__header h2 {
  margin: 8px 0 6px;
  color: #0f172a;
  font-size: 26px;
  letter-spacing: -0.04em;
}

.ea__header p {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

.ea__back {
  flex-shrink: 0;
  border: 1px solid rgba(14, 165, 233, 0.24);
  border-radius: 999px;
  padding: 10px 14px;
  background: rgba(240, 249, 255, 0.86);
  color: #0369a1;
  font: inherit;
  font-size: 13px;
  font-weight: 720;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.ea__back:hover {
  border-color: rgba(14, 165, 233, 0.44);
  box-shadow: 0 10px 22px rgba(14, 165, 233, 0.12);
}

.ea__tabs {
  display: flex;
  gap: 6px;
  padding: 5px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
  width: fit-content;
}

.ea__tab {
  border: none;
  border-radius: 13px;
  padding: 9px 16px;
  background: transparent;
  color: #64748b;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, box-shadow 0.15s;
}

.ea__tab--active {
  background: rgba(14, 165, 233, 0.12);
  color: #0284c7;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.1);
}

.ea__stats {
  display: flex;
  gap: 14px;
}

.ea__stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 16px;
  border: 1px solid rgba(226, 232, 240, 0.82);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 14px 38px rgba(15, 23, 42, 0.06);
}

.ea__stat span {
  color: #64748b;
  font-size: 12px;
}

.ea__stat strong {
  color: #0f172a;
  font-size: 22px;
  font-weight: 800;
}

.ea__form {
  display: grid;
  grid-template-columns: 180px 1fr auto;
  align-items: end;
  gap: 12px;
  padding: 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(18px);
}

.ea__form--col {
  grid-template-columns: 1fr;
}

.ea__row {
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: 12px;
}

.ea__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ea__field--narrow {
  min-width: 0;
}

.ea__field label {
  color: #334155;
  font-size: 12px;
  font-weight: 720;
}

.ea__field input,
.ea__textarea {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 10px 12px;
  font: inherit;
  font-size: 14px;
  color: #0f172a;
  outline: none;
  background: rgba(248, 250, 252, 0.9);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.ea__field input:focus,
.ea__textarea:focus {
  border-color: rgba(14, 165, 233, 0.62);
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.1);
}

.ea__textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.65;
}

.ea__add {
  border: none;
  border-radius: 999px;
  padding: 11px 18px;
  background: linear-gradient(135deg, #0284c7, #6366f1);
  color: #ffffff;
  font: inherit;
  font-size: 13px;
  font-weight: 760;
  cursor: pointer;
  box-shadow: 0 14px 32px rgba(2, 132, 199, 0.22);
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
  white-space: nowrap;
}

.ea__add:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 38px rgba(2, 132, 199, 0.3);
}

.ea__add:disabled {
  opacity: 0.42;
  cursor: not-allowed;
  box-shadow: none;
}

.ea__error {
  padding: 10px 12px;
  border: 1px solid rgba(248, 113, 113, 0.35);
  border-radius: 14px;
  background: #fff1f2;
  color: #dc2626;
  font-size: 13px;
}

.ea__list-card {
  border: 1px solid rgba(226, 232, 240, 0.82);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  backdrop-filter: blur(18px);
}

.ea__list-head {
  padding: 16px 18px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.72);
}

.ea__list-head h3 {
  margin: 0 0 4px;
  color: #0f172a;
  font-size: 16px;
  letter-spacing: -0.03em;
}

.ea__list-head p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.ea__list {
  display: flex;
  flex-direction: column;
}

.ea__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
}

.ea__item:last-child {
  border-bottom: none;
}

.ea__item--style {
  align-items: flex-start;
  flex-direction: column;
  gap: 12px;
}

.ea__item--style > * {
  width: 100%;
}

.ea__item--style .ea__actions {
  justify-content: flex-end;
}

.ea__style-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.ea__style-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ea__style-meta strong {
  color: #0f172a;
  font-size: 15px;
}

.ea__style-sort {
  color: #94a3b8;
  font-size: 12px;
}

.ea__style-preview {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.ea__inline-edit {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 18px;
  background: rgba(240, 249, 255, 0.7);
}

.ea__inline-edit-actions {
  display: flex;
  gap: 10px;
}

.ea__identity {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ea__avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: linear-gradient(135deg, #0284c7, #6366f1);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 760;
}

.ea__identity > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ea__identity strong {
  color: #0f172a;
  font-size: 14px;
}

.ea__identity span {
  color: #64748b;
  font-size: 12px;
}

.ea__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.ea__actions button {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 999px;
  padding: 7px 11px;
  background: rgba(248, 250, 252, 0.9);
  color: #475569;
  font: inherit;
  font-size: 12px;
  font-weight: 720;
  cursor: pointer;
  transition: border-color 0.15s;
}

.ea__actions button:hover {
  border-color: rgba(14, 165, 233, 0.38);
  color: #0369a1;
}

.ea__btn--danger {
  border-color: rgba(248, 113, 113, 0.3) !important;
  color: #dc2626 !important;
  background: rgba(255, 241, 242, 0.86) !important;
}

.ea__btn--save {
  background: linear-gradient(135deg, #0284c7, #6366f1) !important;
  color: #ffffff !important;
  border-color: transparent !important;
  box-shadow: 0 10px 24px rgba(2, 132, 199, 0.2);
}

.ea__btn--cancel {
  color: #64748b !important;
}

.ea__status {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 720;
  user-select: none;
}

.ea__status--active {
  background: #ecfdf5;
  color: #047857;
}

.ea__status--disabled {
  background: #f3f4f6;
  color: #6b7280;
}

.ea__empty {
  padding: 40px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}
</style>
