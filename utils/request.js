const axios = require('axios')

const http = axios.create({
  timeout: 10000,
  baseURL: 'http://localhost:8010'
})

http.interceptors.response.use((response) => {
  const { code, message } = response.data
  return response
}, err => {
  return Promise.reject(err)
})
const httpPost = http.post
const httpGet = http.get
async function post(url, params = {}, config = {}) {
  const validCode = params.validCode
  if (validCode) {
    delete params.validCode
  }

  const response = await httpPost(url, params, config)
  return response.data
}

function upload(url, params = {}, config = {}) {
  return httpPost(url, {
    params
  }, {
    ...config,
    ...{
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  })
}

async function get(url, params = {}, config = {}) {
  const response = await httpGet(url, { params, ...config })
  return response?.data
}

module.exports = {
  post,
  get,
  upload,
}