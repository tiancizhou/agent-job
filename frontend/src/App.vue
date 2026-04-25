<template>
  <LoginPanel v-if="!currentUser && !isCheckingAuth" @authenticated="onAuthenticated" />

  <div v-else-if="currentUser" class="app-layout" :class="`app-layout--mobile-${mobileView}`">
    <aside class="sidebar">
      <AppList
        :apps="apps"
        :selected-app-id="selectedAppId"
        @select="onSelectApp"
        @delete="onDeleteApp"
        @new-app="onNewApp"
      />
    </aside>
    <main class="chat-area">
      <header class="topbar">
        <button v-if="currentUser.is_admin" type="button" @click="showAdmin = !showAdmin">
          {{ showAdmin ? "应用生成" : "工号管理" }}
        </button>
        <button type="button" class="topbar__usage" @click="isUsagePanelOpen = true">
          Token：{{ formatTokenCount(usageSummary?.total_tokens || 0) }}
        </button>
        <div class="topbar__user">
          <span>{{ currentUser.employee_no }}</span>
          <button type="button" @click="onLogout">退出登录</button>
        </div>
      </header>

      <UsagePanel v-if="isUsagePanelOpen" :summary="usageSummary" @close="isUsagePanelOpen = false" />
      <EmployeeAdmin v-if="showAdmin" @close="showAdmin = false" />
      <ChatPanel
        v-else
        :selected-app-id="selectedAppId"
        :styles="styles"
        :mobile-view="mobileView"
        @app-created="onAppCreated"
        @app-updated="onAppUpdated"
      />
    </main>
    <nav class="mobile-tabbar" aria-label="移动端导航">
      <button type="button" :class="{ 'mobile-tabbar__item--active': mobileView === 'apps' }" @click="mobileView = 'apps'">应用</button>
      <button type="button" :class="{ 'mobile-tabbar__item--active': mobileView === 'chat' }" @click="mobileView = 'chat'">生成</button>
      <button type="button" :class="{ 'mobile-tabbar__item--active': mobileView === 'preview' }" @click="mobileView = 'preview'">预览</button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import AppList from "./components/AppList.vue"
import ChatPanel from "./components/ChatPanel.vue"
import EmployeeAdmin from "./components/EmployeeAdmin.vue"
import LoginPanel from "./components/LoginPanel.vue"
import UsagePanel from "./components/UsagePanel.vue"
import { deleteApp, getCurrentUser, getUsageSummary, listApps, listStyles, logout, type App, type CurrentUser, type Style, type UsageSummary } from "./api/index"

const apps = ref<App[]>([])
const styles = ref<Style[]>([])
const selectedAppId = ref<string | null>(null)
const currentUser = ref<CurrentUser | null>(null)
const isCheckingAuth = ref(true)
const showAdmin = ref(false)
const mobileView = ref<"apps" | "chat" | "preview">("chat")
const usageSummary = ref<UsageSummary | null>(null)
const isUsagePanelOpen = ref(false)

onMounted(async () => {
  try {
    currentUser.value = await getCurrentUser()
    await Promise.all([loadInitialApps(), loadStyles(), refreshUsageSummary()])
  } catch {
    currentUser.value = null
  } finally {
    isCheckingAuth.value = false
  }
})

async function loadInitialApps() {
  await refreshApps()
  const savedAppId = window.localStorage.getItem("quickapp:selectedAppId")
  const creatingApp = apps.value.find((app) => app.status === "creating")
  if (savedAppId && apps.value.some((app) => app.id === savedAppId)) {
    selectedAppId.value = savedAppId
  } else if (creatingApp) {
    selectedAppId.value = creatingApp.id
    window.localStorage.setItem("quickapp:selectedAppId", creatingApp.id)
  }
}

async function onAuthenticated(user: CurrentUser) {
  currentUser.value = user
  showAdmin.value = false
  await Promise.all([loadInitialApps(), loadStyles(), refreshUsageSummary()])
}

async function refreshApps() {
  apps.value = await listApps()
}

async function loadStyles() {
  try {
    styles.value = await listStyles()
  } catch {
    styles.value = []
  }
}

async function refreshUsageSummary() {
  try {
    usageSummary.value = await getUsageSummary()
  } catch {
    usageSummary.value = null
  }
}

function onSelectApp(id: string) {
  selectedAppId.value = id
  showAdmin.value = false
  mobileView.value = "chat"
  window.localStorage.setItem("quickapp:selectedAppId", id)
}

function onNewApp() {
  selectedAppId.value = null
  showAdmin.value = false
  mobileView.value = "chat"
  window.localStorage.removeItem("quickapp:selectedAppId")
}

async function onDeleteApp(id: string) {
  await deleteApp(id)
  apps.value = apps.value.filter((app) => app.id !== id)
  if (selectedAppId.value === id) {
    selectedAppId.value = null
    window.localStorage.removeItem("quickapp:selectedAppId")
  }
}

function onAppCreated(app: App) {
  apps.value.push(app)
  selectedAppId.value = app.id
  mobileView.value = "chat"
  window.localStorage.setItem("quickapp:selectedAppId", app.id)
}

async function onAppUpdated(app: App) {
  await Promise.all([refreshApps(), refreshUsageSummary()])
  selectedAppId.value = app.id
  window.localStorage.setItem("quickapp:selectedAppId", app.id)
}

async function onLogout() {
  await logout()
  currentUser.value = null
  apps.value = []
  styles.value = []
  usageSummary.value = null
  selectedAppId.value = null
  showAdmin.value = false
  isUsagePanelOpen.value = false
  window.localStorage.removeItem("quickapp:selectedAppId")
}

function formatTokenCount(value: number): string {
  if (value >= 10000) return `${(value / 10000).toFixed(1)}万`
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return String(value)
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: #f3f4f6;
}

.sidebar {
  width: 272px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  box-shadow: 8px 0 30px rgba(15, 23, 42, 0.04);
  z-index: 1;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  min-height: 58px;
  padding: 0 22px;
  background: rgba(255, 255, 255, 0.86);
  border-bottom: 1px solid #e5e7eb;
  backdrop-filter: blur(16px);
  z-index: 1;
}

.topbar > button,
.topbar__user button {
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 8px 12px;
  background: #ffffff;
  color: #374151;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
}

.topbar__usage {
  border-color: rgba(14, 165, 233, 0.22) !important;
  background: rgba(240, 249, 255, 0.9) !important;
  color: #0369a1 !important;
}

.topbar__user {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #111827;
  font-size: 13px;
  font-weight: 650;
}

.mobile-tabbar {
  display: none;
}

@media (max-width: 768px) {
  .app-layout {
    position: relative;
    display: block;
    height: 100dvh;
    overflow: hidden;
    padding-bottom: calc(72px + env(safe-area-inset-bottom));
  }

  .sidebar {
    display: none;
    width: 100%;
    height: calc(100dvh - 72px - env(safe-area-inset-bottom));
    border-right: none;
    box-shadow: none;
  }

  .chat-area {
    height: calc(100dvh - 72px - env(safe-area-inset-bottom));
    min-height: 0;
  }

  .app-layout--mobile-apps .sidebar {
    display: flex;
  }

  .app-layout--mobile-apps .chat-area {
    display: none;
  }

  .topbar {
    min-height: 52px;
    padding: 0 14px;
    justify-content: space-between;
  }

  .topbar > button,
  .topbar__user button {
    padding: 7px 10px;
    font-size: 12px;
  }

  .topbar__user {
    margin-left: auto;
    gap: 8px;
    font-size: 12px;
  }

  .mobile-tabbar {
    position: fixed;
    left: 10px;
    right: 10px;
    bottom: max(8px, env(safe-area-inset-bottom));
    z-index: 20;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    padding: 8px;
    border: 1px solid rgba(226, 232, 240, 0.88);
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.16);
    backdrop-filter: blur(18px);
  }

  .mobile-tabbar button {
    border: none;
    border-radius: 16px;
    padding: 10px 8px;
    background: transparent;
    color: #64748b;
    font-size: 13px;
    font-weight: 760;
  }

  .mobile-tabbar__item--active {
    background: linear-gradient(135deg, #0284c7, #f97316) !important;
    color: #ffffff !important;
    box-shadow: 0 10px 24px rgba(2, 132, 199, 0.22);
  }
}
</style>
