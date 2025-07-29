import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path:'/',
        name:'login',
        component:()=> import('../components/Login.vue'),
    },
    {
      path:'/main',
      name:'main',
      component:()=> import('../components/Main.vue'),  
    },
    {
        path:'/multi',
        name:'multi',
        component:()=> import('../components/Multi.vue'),
    },
    {
        path:'/single/:id',
        name:'single',
        component:()=> import('../components/Single.vue'),
    }
]
const router = createRouter({
    routes,
    history:createWebHistory(),
});

export default router;