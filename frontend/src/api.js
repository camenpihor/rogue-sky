import axios from "axios";

const backendUrl = 'http://127.0.0.1:5000/api'

function getStarForecast(address) {
  const url = `${backendUrl}/stars/${address}`
  return axios.get(url)
}

export default getStarForecast
