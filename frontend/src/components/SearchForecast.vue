<template>
  <div>
    <p>Weather will go here</p>
    <button v-on:click="getWeather">Weather</button>
    <button v-on:click="getStars">Stars</button>
    {{ weather }}
    {{ stars }}
  </div>
</template>

<script>
import { getWeatherForecast, getStarForecast } from "../api.js";

export default {
  data() {
    return {
      weather: null,
      stars: null
    };
  },
  methods: {
    getWeather() {
      getWeatherForecast().then(response => {
        this.stars = null;
        this.weather = response.data;
      });
    },
    getStars() {
      getStarForecast().then(response => {
        this.weather = null;
        this.stars = response.data;
      });
    }
  }
};
</script>

<style>
</style>