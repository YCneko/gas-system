<template>
  <div class="vocs-chart">
    <h2>VOC 预测数据</h2>
    <ul v-if="predictionsData.length">
      <li v-for="(item, index) in predictionsData" :key="index">
        <strong>{{ item.name || item.id }}</strong
        >：{{ item.value || item.prediction }}
      </li>
    </ul>
    <p v-else>暂无数据或加载中...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import request from "@/utils/request";

const predictionsData = ref([]);

onMounted(async () => {
  try {
    const data = await request.get("/api/vocs/prediction");
    predictionsData.value = data;
  } catch (error) {
    console.error("获取 VOC 预测数据失败：", error);
  }
});
</script>

<style scoped>
.vocs-chart {
  padding: 1rem;
}
ul {
  list-style: none;
  padding: 0;
}
li {
  margin-bottom: 0.5em;
  border-bottom: 1px solid #eee;
  padding: 0.5em 0;
}
</style>
