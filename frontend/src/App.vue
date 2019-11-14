<template>
  <div id="app">
    <p>Hai</p>
    <SearchForecast />
  </div>
</template>

<script>
import SearchForecast from "./components/SearchForecast.vue";

export default {
  name: "app",
  components: {
    SearchForecast
  }
};
</script>

<style>
#app {
  font-family: "Avenir", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
