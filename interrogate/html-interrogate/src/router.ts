import { createRouter, createWebHistory } from 'vue-router'
import SimulationInterrogationView from '@/views/SimulationInterrogationView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/simulation/interrogation/1',
    },
    {
      component: SimulationInterrogationView,
      name: 'simulation-interrogation',
      path: '/simulation/interrogation/:caseId',
    },
  ],
})
