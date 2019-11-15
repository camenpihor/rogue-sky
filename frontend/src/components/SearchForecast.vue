<template>
  <div>
    <div>
      <h1> {{ city }} {{ state }} </h1>
    </div>
    Star Visibility Forecast
    <input
      v-on:keyup.enter="getStars"
      v-model="latitude"
      placeholder="47.61,-122.33 or Seattle, WA"
    />
    <button v-on:click="getStars">Submit</button>
    <div>
      {{ star_forecast }}
    </div>
  </div>
</template>

<script>
import getStarForecast from "../api.js";

export default {
  data() {
    return {
      latitude: null,
      longitude: null,
      city: null,
      state: null,
      star_forecast: null
    };
  },
  methods: {
    getStars() {
      this.city = null;
      this.state = null;
      this.star_forecast = null;
      getStarForecast(this.latitude, this.longitude).then(response => {
        this.city = response.data.city;
        this.state = response.data.state;
        this.star_forecast = response.data;
      });
    }
  }
};
</script>

<style>
</style>