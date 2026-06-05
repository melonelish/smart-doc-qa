<template>
  <div class="domain-home">
    <DomainIntro />
  </div>
</template>

<script setup lang="ts">
import DomainIntro from '../components/domain/DomainIntro.vue'
</script>

<style scoped>
.domain-home {
  max-width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 20px;
}
</style>
