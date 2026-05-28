import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

// core-js 已通过 @vue/cli-plugin-babel/preset 自动按需 polyfill
// 无需额外配置

createApp(App).use(router).mount("#app");
