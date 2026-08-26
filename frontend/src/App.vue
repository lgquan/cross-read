<script setup lang="ts">
import { BookOpen, Monitor, Moon, Power, Settings, Sun, X } from '@lucide/vue'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useRoute } from 'vue-router'

import {
  readThemePreference,
  setThemePreference,
  type ThemePreference,
} from '@/utils/theme'
import { getStartupSetting, setStartupSetting } from '@/api/client'

const route = useRoute()
const isMarkdownReader = computed(
  () => route.name === 'preview' && route.query.kind === 'markdown',
)
const settingsOpen = ref(false)
const settingsTrigger = ref<HTMLButtonElement | null>(null)
const settingsPanel = ref<HTMLElement | null>(null)
const theme = ref<ThemePreference>(readThemePreference())
const startupEnabled = ref(false)
const startupAvailable = ref(false)
const startupLoading = ref(false)
const startupError = ref('')
const themeOptions = [
  { value: 'system' as const, label: '跟随系统', icon: Monitor },
  { value: 'light' as const, label: '浅色', icon: Sun },
  { value: 'dark' as const, label: '深色', icon: Moon },
]

function openSettings(): void {
  settingsOpen.value = true
  void loadStartupSetting()
  void nextTick(() => settingsPanel.value?.querySelector<HTMLButtonElement>('.settings-close')?.focus())
}

async function loadStartupSetting(): Promise<void> {
  startupLoading.value = true
  startupError.value = ''
  try {
    const setting = await getStartupSetting()
    startupEnabled.value = setting.enabled
    startupAvailable.value = setting.available
    if (setting.message) startupError.value = setting.message
  } catch (reason) {
    startupAvailable.value = false
    startupError.value = reason instanceof Error ? reason.message : '无法读取开机自启动设置'
  } finally {
    startupLoading.value = false
  }
}

async function toggleStartup(): Promise<void> {
  if (!startupAvailable.value || startupLoading.value) return
  const nextValue = !startupEnabled.value
  startupLoading.value = true
  startupError.value = ''
  try {
    const setting = await setStartupSetting(nextValue)
    startupEnabled.value = setting.enabled
  } catch (reason) {
    startupError.value = reason instanceof Error ? reason.message : '无法更新开机自启动设置'
  } finally {
    startupLoading.value = false
  }
}

function closeSettings(restoreFocus = true): void {
  settingsOpen.value = false
  if (restoreFocus) void nextTick(() => settingsTrigger.value?.focus())
}

function selectTheme(value: ThemePreference): void {
  theme.value = value
  setThemePreference(value)
}

function handleSettingsKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    closeSettings()
    return
  }
  if (event.key !== 'Tab' || !settingsPanel.value) return

  const focusable = Array.from(settingsPanel.value.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'))
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (!first || !last) return
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(settingsOpen, (open) => document.documentElement.classList.toggle('settings-open', open))
onBeforeUnmount(() => document.documentElement.classList.remove('settings-open'))
</script>

<template>
  <div class="app-shell">
    <header class="top-bar">
      <RouterLink to="/" class="brand" aria-label="返回 Cross Read 首页">
        <span class="brand-mark"><BookOpen :size="19" :stroke-width="2.1" /></span>
        <span>Cross Read</span>
      </RouterLink>
      <div class="top-bar-actions">
        <span v-if="!isMarkdownReader" class="connection-pill">
          <span class="connection-dot" aria-hidden="true"></span>
          局域网
        </span>
        <button
          ref="settingsTrigger"
          class="top-bar-icon"
          type="button"
          aria-label="打开设置"
          aria-controls="app-settings"
          :aria-expanded="settingsOpen"
          title="设置"
          @click="openSettings"
        >
          <Settings :size="20" />
        </button>
      </div>
    </header>

    <main class="page-container">
      <RouterView />
    </main>

    <Teleport to="body">
      <Transition name="settings-sheet">
        <div v-if="settingsOpen" class="settings-overlay" @click.self="closeSettings()">
          <section
            id="app-settings"
            ref="settingsPanel"
            class="settings-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
            @keydown="handleSettingsKeydown"
          >
            <div class="settings-handle" aria-hidden="true"></div>
            <header class="settings-header">
              <h2 id="settings-title">设置</h2>
              <button
                class="settings-close"
                type="button"
                aria-label="关闭设置"
                title="关闭"
                @click="closeSettings()"
              >
                <X :size="20" />
              </button>
            </header>
            <div class="settings-content">
              <h3>外观</h3>
              <div class="theme-options" role="radiogroup" aria-label="主题颜色">
                <button
                  v-for="option in themeOptions"
                  :key="option.value"
                  class="theme-option"
                  :class="{ 'theme-option--active': theme === option.value }"
                  type="button"
                  role="radio"
                  :aria-checked="theme === option.value"
                  @click="selectTheme(option.value)"
                >
                  <component :is="option.icon" :size="19" />
                  <span>{{ option.label }}</span>
                </button>
              </div>
              <h3 class="settings-section-title">系统</h3>
              <div class="startup-setting">
                <span class="startup-setting-icon"><Power :size="19" /></span>
                <span class="startup-setting-copy">
                  <strong>开机自启动</strong>
                  <small>{{ startupError || '登录 Windows 后自动启动 Cross Read' }}</small>
                </span>
                <button
                  class="switch"
                  :class="{ 'switch--on': startupEnabled }"
                  type="button"
                  role="switch"
                  :aria-checked="startupEnabled"
                  :aria-label="startupEnabled ? '关闭开机自启动' : '开启开机自启动'"
                  :disabled="!startupAvailable || startupLoading"
                  @click="toggleStartup"
                >
                  <span class="switch-thumb" aria-hidden="true"></span>
                </button>
              </div>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
