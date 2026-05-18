<template>
  <div class="container">
    <iframe 
       src="http://localhost:8190/iportal/apps/mapdashboard/v2/index.html?id=1329945243&action=view&mode=pc"
      
      frameborder="0" 
      class="full-screen-iframe">
    </iframe>
  </div>
</template>

<script setup lang="ts">
// 空的script标签，保留以满足.vue文件格式要求
</script>

<style scoped lang="scss">
.container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  padding: 0;
  margin: 0;
}

.full-screen-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>