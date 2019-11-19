<template>
  <div>
    <div v-if="star_forecast !== null">
      <h1>{{ city }}, {{ state }}</h1>
    </div>
    <div>
      <div v-for="day in star_forecast" v-bind:key="day.weather_date_utc">
        <ul>
          {{ day.weather_date_utc }}
          <li>Star Visibility: {{ day.star_visibility }}</li>
          <li>Sunset: {{ day.sunset_time_utc }}</li>
          <li>Moon Phase: {{ day.moon_phase_pct }}</li>
          <li>Rain: {{ day.precip_probability }}</li>
          <li>Cloud Cover: {{ day.cloud_cover_pct }}</li>
          <li>Min Temperature: {{ day.temperature_min_f }}</li>
          <li>Max Temperature: {{ day.temperature_max_f }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { getStarForecast } from "../api.js";

export default {
  name: "forecast",
  data() {
    return {
      star_forecast: null,
      city: null,
      state: null
    };
  },
  methods: {
    getForecast(latitude, longitude) {
      getStarForecast(latitude, longitude).then(response => {
        this.star_forecast = response.data.daily_forecast;
        this.city = response.data.city;
        this.state = response.data.state;
      });
    }
  },
  mounted() {
    this.getForecast(this.$route.params.latitude, this.$route.params.longitude);
  },
  watch: {
    $route() {
      this.getForecast(
        this.$route.params.latitude,
        this.$route.params.longitude
      );
    }
  }
};
</script>

<style>
</style>