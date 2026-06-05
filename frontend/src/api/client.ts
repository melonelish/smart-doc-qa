import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.response?.data?.error || err.message
    console.error('[API Error]', msg)
    return Promise.reject(err)
  },
)

export default client
