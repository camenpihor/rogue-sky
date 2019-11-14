import axios from "axios";

const backendUrl = 'http://127.0.0.1:5000/api'

function getWeatherForecast() {
  const url = `${backendUrl}/weather/47.6062,-122.3321`
  return axios.get(url)
}

function getStarForecast() {
  const url = `${backendUrl}/stars/47.6062,-122.3321`
  return axios.get(url)
}

export { getWeatherForecast, getStarForecast }
