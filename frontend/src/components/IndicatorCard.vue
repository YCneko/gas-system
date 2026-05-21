<template>
  <div class="indicator-card">
    <div class="card-header">
      <span class="card-icon">{{ iconMap[data.icon] || "📊" }}</span>
      <span class="card-title">{{ data.title }}</span>
    </div>
    <div class="card-value">
      {{ data.value }} <span class="unit">{{ data.unit }}</span>
    </div>
    <div class="card-bg-glow"></div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Object, required: true } });
const iconMap = { air: "🌫️", thermometer: "🌡️", droplet: "💧", wind: "💨" };
</script>

<style scoped>
.indicator-card {
  position: relative;
  background: linear-gradient(
    135deg,
    rgba(21, 35, 66, 0.8) 0%,
    rgba(15, 23, 42, 0.8) 100%
  );
  border-radius: 16px;
  padding: 20px 24px;
  color: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(46, 123, 207, 0.2);
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
}
.indicator-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0, 212, 255, 0.15);
  border-color: rgba(0, 212, 255, 0.4);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.card-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  background: rgba(0, 212, 255, 0.12);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-title {
  font-size: 15px;
  color: #9aa4bf;
  font-weight: 500;
}
.card-value {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #fff;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}
.unit {
  font-size: 18px;
  font-weight: 500;
  color: #6b7a94;
  margin-left: 4px;
}
.card-bg-glow {
  position: absolute;
  top: -30%;
  right: -20%;
  width: 100px;
  height: 100px;
  background: radial-gradient(
    circle,
    rgba(0, 212, 255, 0.15) 0%,
    transparent 70%
  );
  border-radius: 50%;
}
</style>
