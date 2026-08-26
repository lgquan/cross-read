<script setup lang="ts">
import { BookOpen, Monitor, Moon, Settings, Sun, X } from '@lucide/vue'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useRoute } from 'vue-router'

import {
  readThemePreference,
  setThemePreference,
  type ThemePreference,
} from '@/utils/theme'

const route = useRoute()
const isMarkdownReader = computed(
  () => route.name === 'preview' && route.query.kind === 'markdown',
)
const settingsOpen = ref(false)
const settingsTrigger = ref<HTMLButtonElement | null>(null)
const settingsPanel = ref<HTMLElement | null>(null)
const theme = ref<ThemePreference>(readThemePreference())
const themeOptions = [
  { value: 'system' as const, label: '跟随系统', icon: Monitor },
  { value: 'light' as const, label: '浅色', icon: Sun },
  { value: 'dark' as const, label: '深色', icon: Moon },
]

function openSettings(): void {
  settingsOpen.value = true
  void nextTick(() => settingsPanel.value?.querySelector<HTMLButtonElement>('.settings-close')?.focus())
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
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
