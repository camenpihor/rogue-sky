<template>
  <div>
    <p>Weather will go here</p>
    <button v-on:click="get">Greet</button>
    {{ weather }}
  </div>
</template>

<script>
import getWeatherForecast from "../api.js";

export default {
  data() {
    return {
      weather: null
    };
  },
  methods: {
    get() {
      getWeatherForecast().then(response => {
        this.weather = response.data;
      });
    }
  }
};
</script>

<style>
</style>