import axios from "axios";

const backendUrl = 'http://127.0.0.1:5000'

function getWeatherForecast() {
  const url = `${backendUrl}/weather/47.6062,-122.3321`
  return axios.get(url)
}

export default getWeatherForecast
