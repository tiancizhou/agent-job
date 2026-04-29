<template>
  <div
    class="login-page"
    :style="loginStyle"
    @pointermove="onLoginPointerMove"
    @pointerleave="resetLoginPointer"
  >
    <div class="login-page__aura" />
    <div class="login-page__decor login-page__decor--blue" />
    <div class="login-page__decor login-page__decor--orange" />
    <div class="login-page__grid" />

    <section class="login-hero">
      <div class="login-hero__badge">中天钢铁内部工具</div>
      <div class="login-hero__brand" aria-label="QuickDa 快搭">
        <svg class="login-hero__logo" viewBox="0 0 72 72" role="img" aria-hidden="true">
          <defs>
            <linearGradient id="qd-login-logo-gradient" x1="10" y1="8" x2="62" y2="64" gradientUnits="userSpaceOnUse">
              <stop stop-color="#0284c7" />
              <stop offset="1" stop-color="#f97316" />
            </linearGradient>
          </defs>
          <rect width="72" height="72" rx="24" fill="url(#qd-login-logo-gradient)" />
          <path d="M35.4 49C24.9 49 18 42.2 18 33.2C18 24.1 24.9 17.3 35.4 17.3C45.9 17.3 52.8 24.1 52.8 33.2C52.8 37.5 51.2 41.2 48.3 44L54.6 50.2L49.2 55.4L42.6 48.8C40.5 49 38.1 49 35.4 49ZM35.4 41.9C40.8 41.9 44.7 38.4 44.7 33.2C44.7 27.9 40.8 24.4 35.4 24.4C29.9 24.4 26.1 27.9 26.1 33.2C26.1 38.4 29.9 41.9 35.4 41.9Z" fill="white" />
        </svg>
        <h1 class="login-hero__title">QuickDa</h1>
      </div>
      <p class="login-hero__subtitle">快搭工作小应用生成器</p>
      <p class="login-hero__desc">登录后，用一句话生成登记页、活动页、看板和日常小工具。</p>

      <div class="login-hero__examples">
        <span>会议报名</span>
        <span>物品领用</span>
        <span>数据看板</span>
      </div>
    </section>

    <section class="login-card">
      <div class="login-card__spotlight" />
      <div class="login-card__header">
        <span class="login-card__eyebrow">EMPLOYEE ACCESS</span>
        <h2>{{ mode === "login" ? "登录 QuickDa" : "设置登录密码" }}</h2>
        <p>{{ mode === "login" ? "使用工号进入你的工作小应用空间" : "首次使用前，请为已开通的工号设置密码" }}</p>
      </div>

      <form class="form" @submit.prevent="submit">
        <div class="form__field">
          <label class="form__label">工号</label>
          <input
            v-model="employeeNo"
            class="form__input"
            placeholder="例如：64003"
            inputmode="numeric"
            autocomplete="username"
          />
        </div>
        <div class="form__field">
          <label class="form__label">密码</label>
          <input
            v-model="password"
            class="form__input"
            type="password"
            placeholder="至少 6 位"
            autocomplete="current-password"
          />
        </div>

        <div v-if="error" class="form__error">
          {{ error }}
        </div>

        <button class="form__btn" :disabled="isSubmitting || !canSubmit" type="submit">
          {{ isSubmitting ? "正在处理..." : mode === "login" ? "进入 QuickDa" : "完成设置" }}
        </button>
      </form>

      <button class="login-card__switch" type="button" @click="toggleMode">
        {{ mode === "login" ? "首次使用？设置登录密码" : "已有密码？返回登录" }}
      </button>

      <div class="login-card__footer">
        <span>QuickDa v1.0</span>
        <span>轻量生成日常工作页面</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue"
import { login, register, type CurrentUser } from "../api/index"

const emit = defineEmits<{
  authenticated: [user: CurrentUser]
}>()

const mode = ref<"login" | "register">("login")
const employeeNo = ref("")
const password = ref("")
const error = ref("")
const isSubmitting = ref(false)
const pointerX = ref(50)
const pointerY = ref(50)
const pointerTiltX = ref(0)
const pointerTiltY = ref(0)

const canSubmit = computed(() => /^\d{5}$/.test(employeeNo.value.trim()) && password.value.length >= 6)

const loginStyle = computed(() => ({
  "--pointer-x": `${pointerX.value}%`,
  "--pointer-y": `${pointerY.value}%`,
  "--tilt-x": `${pointerTiltX.value}deg`,
  "--tilt-y": `${pointerTiltY.value}deg`,
  "--shift-x": `${(pointerX.value - 50) / 7}px`,
  "--shift-y": `${(pointerY.value - 50) / 7}px`,
}))

function toggleMode() {
  mode.value = mode.value === "login" ? "register" : "login"
  error.value = ""
}

function onLoginPointerMove(event: PointerEvent) {
  if (event.pointerType !== "mouse") return
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width) * 100
  const y = ((event.clientY - rect.top) / rect.height) * 100
  pointerX.value = Math.min(100, Math.max(0, x))
  pointerY.value = Math.min(100, Math.max(0, y))
  pointerTiltX.value = (50 - pointerY.value) / 18
  pointerTiltY.value = (pointerX.value - 50) / 18
}

function resetLoginPointer() {
  pointerX.value = 50
  pointerY.value = 50
  pointerTiltX.value = 0
  pointerTiltY.value = 0
}

async function submit() {
  if (!canSubmit.value || isSubmitting.value) return
  error.value = ""
  isSubmitting.value = true
  try {
    const user = mode.value === "login"
      ? await login(employeeNo.value.trim(), password.value)
      : await register(employeeNo.value.trim(), password.value)
    emit("authenticated", user)
  } catch {
    error.value = mode.value === "login" ? "工号或密码错误" : "工号未开通或已设置密码"
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
* { box-sizing: border-box; }

.login-page {
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(380px, 460px);
  align-items: center;
  gap: 56px;
  padding: 64px clamp(28px, 7vw, 108px);
  overflow: hidden;
  background:
    radial-gradient(circle at 14% 18%, rgba(56, 189, 248, 0.24) 0%, transparent 28%),
    radial-gradient(circle at 86% 16%, rgba(251, 146, 60, 0.22) 0%, transparent 26%),
    linear-gradient(135deg, #f8fbff 0%, #fff7ed 48%, #eff6ff 100%);
  color: #0f172a;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

.login-page__aura {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at var(--pointer-x, 50%) var(--pointer-y, 50%), rgba(34, 211, 238, 0.2), transparent 18%),
    radial-gradient(circle at calc(var(--pointer-x, 50%) + 12%) calc(var(--pointer-y, 50%) + 8%), rgba(129, 140, 248, 0.14), transparent 24%);
  opacity: 0.8;
  transition: background 0.12s ease-out, opacity 0.2s ease-out;
  mix-blend-mode: multiply;
}

.login-page__decor {
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
}

.login-page__decor--blue {
  width: 260px;
  height: 260px;
  left: -80px;
  bottom: 12%;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.24), transparent 68%);
  transform: translate3d(calc(var(--shift-x, 0px) * -0.7), calc(var(--shift-y, 0px) * -0.7), 0);
  transition: transform 0.28s ease-out;
  will-change: transform;
}

.login-page__decor--orange {
  width: 300px;
  height: 300px;
  top: -100px;
  right: 10%;
  background: radial-gradient(circle, rgba(129, 140, 248, 0.2), transparent 68%);
  transform: translate3d(calc(var(--shift-x, 0px) * 0.75), calc(var(--shift-y, 0px) * 0.75), 0);
  transition: transform 0.28s ease-out;
  will-change: transform;
}

.login-page__grid {
  position: absolute;
  inset: auto -10% -18% -10%;
  height: 38%;
  background-image:
    linear-gradient(to right, rgba(14, 165, 233, 0.14) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(14, 165, 233, 0.14) 1px, transparent 1px);
  background-size: 42px 42px;
  transform: perspective(620px) rotateX(58deg) translate3d(calc(var(--shift-x, 0px) * -0.35), calc(var(--shift-y, 0px) * -0.2), 0);
  transform-origin: top center;
  opacity: 0.7;
  pointer-events: none;
  transition: transform 0.28s ease-out;
  will-change: transform;
}

.login-hero,
.login-card {
  position: relative;
  z-index: 1;
}

.login-hero {
  max-width: 640px;
}

.login-hero__badge {
  display: inline-flex;
  padding: 8px 14px;
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #0369a1;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 12px 30px rgba(14, 165, 233, 0.1);
}

.login-hero__brand {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-top: 24px;
  transform: translate3d(calc(var(--shift-x, 0px) * 0.16), calc(var(--shift-y, 0px) * 0.16), 0);
  transition: transform 0.24s ease-out;
  will-change: transform;
}

.login-hero__logo {
  width: clamp(54px, 7vw, 76px);
  height: clamp(54px, 7vw, 76px);
  flex-shrink: 0;
  border-radius: 24px;
  box-shadow: 0 24px 54px rgba(2, 132, 199, 0.24);
}

.login-hero__title {
  margin: 0;
  font-size: clamp(54px, 9vw, 92px);
  line-height: 0.95;
  letter-spacing: -0.08em;
  color: #0f172a;
  font-weight: 860;
}

.login-hero__subtitle {
  margin: 18px 0 0;
  font-size: clamp(24px, 4vw, 40px);
  line-height: 1.18;
  letter-spacing: -0.05em;
  font-weight: 820;
  background: linear-gradient(135deg, #0284c7, #f97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-hero__desc {
  max-width: 520px;
  margin: 22px 0 0;
  color: #64748b;
  font-size: 17px;
  line-height: 1.8;
}

.login-hero__examples {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 30px;
}

.login-hero__examples span {
  padding: 9px 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #475569;
  font-size: 13px;
  font-weight: 650;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.login-card {
  width: 100%;
  padding: 30px;
  border: 1px solid rgba(14, 165, 233, 0.24);
  border-radius: 30px;
  background:
    radial-gradient(circle at var(--pointer-x, 50%) var(--pointer-y, 50%), rgba(34, 211, 238, 0.18), transparent 34%),
    rgba(255, 255, 255, 0.86);
  box-shadow:
    0 30px 80px rgba(15, 23, 42, 0.14),
    0 0 0 1px rgba(255, 255, 255, 0.62) inset;
  backdrop-filter: blur(18px);
  overflow: hidden;
  transform: perspective(900px) rotateX(var(--tilt-x, 0deg)) rotateY(var(--tilt-y, 0deg)) translate3d(0, 0, 0);
  transform-style: preserve-3d;
  transition: transform 0.22s ease-out, box-shadow 0.22s ease-out, border-color 0.22s ease-out;
  will-change: transform;
}

.login-card:hover {
  border-color: rgba(6, 182, 212, 0.42);
  box-shadow:
    0 34px 90px rgba(15, 23, 42, 0.16),
    0 0 42px rgba(34, 211, 238, 0.16),
    0 0 0 1px rgba(255, 255, 255, 0.72) inset;
}

.login-card__spotlight {
  position: absolute;
  inset: -1px;
  pointer-events: none;
  background: radial-gradient(circle at var(--pointer-x, 50%) var(--pointer-y, 50%), rgba(129, 140, 248, 0.22), transparent 24%);
  opacity: 0;
  transition: opacity 0.2s ease-out;
  mix-blend-mode: screen;
}

.login-card:hover .login-card__spotlight {
  opacity: 1;
}

.login-card__header,
.form,
.login-card__switch,
.login-card__footer {
  position: relative;
  z-index: 1;
}

.login-card__header {
  margin-bottom: 24px;
}

.login-card__eyebrow {
  color: #0284c7;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.login-card__header h2 {
  margin: 10px 0 8px;
  color: #0f172a;
  font-size: 28px;
  letter-spacing: -0.04em;
}

.login-card__header p {
  margin: 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.7;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form__field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form__label {
  color: #334155;
  font-size: 13px;
  font-weight: 700;
}

.form__input {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 13px 15px;
  background: rgba(248, 250, 252, 0.86);
  color: #0f172a;
  outline: none;
  font: inherit;
  font-size: 15px;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.form__input::placeholder {
  color: #94a3b8;
}

.form__input:focus {
  border-color: rgba(14, 165, 233, 0.68);
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.12);
}

.form__error {
  padding: 11px 13px;
  border: 1px solid rgba(248, 113, 113, 0.35);
  border-radius: 14px;
  background: #fff1f2;
  color: #dc2626;
  font-size: 13px;
  font-weight: 650;
}

.form__btn {
  border: none;
  border-radius: 999px;
  padding: 13px 18px;
  background: linear-gradient(135deg, #0284c7, #f97316);
  color: #ffffff;
  font: inherit;
  font-size: 15px;
  font-weight: 780;
  cursor: pointer;
  box-shadow: 0 18px 38px rgba(2, 132, 199, 0.25);
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.form__btn:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 22px 44px rgba(2, 132, 199, 0.32);
}

.form__btn:not(:disabled):active {
  transform: scale(0.98);
}

.form__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.login-card__switch {
  display: block;
  width: 100%;
  margin-top: 18px;
  border: none;
  background: transparent;
  color: #0284c7;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  text-align: center;
}

.login-card__switch:hover {
  color: #0369a1;
}

.login-card__footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  color: #94a3b8;
  font-size: 12px;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    gap: 32px;
    padding: 36px 20px;
  }

  .login-hero {
    text-align: center;
    margin: 0 auto;
  }

  .login-hero__brand {
    justify-content: center;
  }

  .login-hero__desc {
    margin-left: auto;
    margin-right: auto;
  }

  .login-hero__examples {
    justify-content: center;
  }

  .login-card {
    max-width: 420px;
    justify-self: center;
    width: 100%;
  }
}

@media (hover: none) {
  .login-card {
    transform: none !important;
  }
}

@media (max-width: 600px) {
  .login-page {
    min-height: 100dvh;
    align-items: start;
    overflow-x: hidden;
    overflow-y: auto;
    gap: 16px;
    padding: 20px 16px max(32px, env(safe-area-inset-bottom));
    -webkit-overflow-scrolling: touch;
  }

  .login-hero {
    text-align: center;
  }

  .login-hero__badge {
    font-size: 11px;
    padding: 5px 10px;
  }

  .login-hero__brand {
    gap: 10px;
    margin-top: 14px;
  }

  .login-hero__logo {
    width: 42px;
    height: 42px;
    border-radius: 14px;
  }

  .login-hero__title {
    font-size: 40px;
  }

  .login-hero__subtitle {
    margin-top: 6px;
    font-size: 18px;
  }

  .login-hero__desc {
    display: none;
  }

  .login-hero__examples {
    margin-top: 10px;
    gap: 6px;
  }

  .login-hero__examples span {
    padding: 5px 10px;
    font-size: 11px;
  }

  .login-card {
    padding: 24px 20px;
    border-radius: 24px;
    max-width: none;
    margin-bottom: env(safe-area-inset-bottom);
  }

  .login-card__header h2 {
    font-size: 22px;
  }

  .login-card__header p {
    font-size: 13px;
  }

  .form {
    gap: 14px;
  }

  .form__input {
    padding: 14px 16px;
    font-size: 16px;
    border-radius: 14px;
  }

  .form__btn {
    padding: 15px 18px;
    font-size: 16px;
  }

  .login-card__switch {
    margin-top: 14px;
    padding: 8px;
  }

  .login-card__footer {
    flex-direction: column;
    align-items: center;
    gap: 4px;
    margin-top: 18px;
    padding-top: 14px;
  }
}
</style>
