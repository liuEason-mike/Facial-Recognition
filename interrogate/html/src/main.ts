import 'element-plus/theme-chalk/index.css'
import 'uno.css'
import '@/styles/app.css'
import App from '@/App.vue'
import router from '@/router'

const app = createApp(App)

app.use(router)

app.mount('#app')
