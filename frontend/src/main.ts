import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './styles/main.css'
import { applyThemePreference, readThemePreference } from './utils/theme'

applyThemePreference(readThemePreference())

createApp(App).use(router).mount('#app')
