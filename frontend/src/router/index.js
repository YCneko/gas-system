import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "dashboard",
    // 路由级懒加载：Dashboard 按需加载，减小首屏体积
    component: () => import("../views/DashboardView.vue"),
    meta: { title: "监控看板" },
  },
  {
    path: "/about",
    name: "about",
    component: () => import("../views/AboutView.vue"),
    meta: { title: "关于" },
  },
  {
    path: "/training",
    name: "training",
    component: () => import("../views/TrainingView.vue"),
    meta: { title: "模型训练" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  // 页面切换时滚动到顶部
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
