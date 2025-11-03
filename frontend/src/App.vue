<template>
  <div id="app">
    <Chat />
  </div>
</template>

<script setup lang="ts">
import Chat from './views/Chat.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f5f5;
}

#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>
