<template>
  <div>
    <input v-on:keyup.enter="search" v-model="input" placeholder="47.61,-122.33 or Seattle, WA" />
    <button v-on:click="search">Submit</button>
  </div>
</template>

<script>
import { getCoordinates } from "../api.js";

export default {
  data() {
    return {
      input: null
    };
  },
  methods: {
    search() {
      getCoordinates(this.input).then(response => {
        this.input = null;
        this.$router.push(
          `/${response.data.latitude}/${response.data.longitude}`
        );
      });
    }
  }
};
</script>

<style>
</style>