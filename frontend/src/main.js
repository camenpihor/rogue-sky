import Vue from 'vue'
import App from './App.vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const router = new VueRouter({
  mode: 'history',
  routes: [
    {
      path: '/',
      component: () =>
        import('./routes/Home.vue'),
    },
    {
      path: '/:latitude/:longitude',
      component: () =>
        import('./routes/Forecast.vue'),
    },
    {
      path: '/404',
      meta: { title: '404' },
      component: () =>
        import('./routes/Error.vue'),
    },
    {
      path: '*',
      redirect: '/404'
    },
  ],
});


new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
