/**
 * Netlify Function: API 反向代理
 * 将所有 /api/* 请求转发到后端服务
 * 环境变量: BACKEND_URL（可选，默认指向 serveo 隧道）
 */
const https = require('https');
const http = require('http');

const BACKEND_HOST = '028662142bd97438-153-254-110-180.serveousercontent.com';

module.exports = async (event, context) => {
  const { path, httpMethod, headers, body, queryStringParameters } = event;

  // path 形如 "/api/health"，去掉 /api 前缀
  const apiPath = path.startsWith('/api') ? path.slice(4) : path;
  const targetPath = `/api${apiPath}`;

  // 构建查询字符串
  const qs = queryStringParameters
    ? '?' + Object.entries(queryStringParameters).map(([k, v]) => `${k}=${v}`).join('&')
    : '';

  const targetUrl = `https://${BACKEND_HOST}${targetPath}${qs}`;

  return new Promise((resolve, reject) => {
    const urlObj = new URL(targetUrl);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 443,
      path: urlObj.pathname + urlObj.search,
      method: httpMethod,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'caviar-crm-proxy/1.0',
        ...Object.fromEntries(
          Object.entries(headers || {}).filter(([k]) =>
            !['host', 'connection', 'content-length', 'accept-encoding'].includes(k.toLowerCase())
          )
        ),
      },
    };

    const protocol = urlObj.protocol === 'https:' ? https : http;
    const req = protocol.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: {
            'Content-Type': res.headers['content-type'] || 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*',
          },
          body: data,
        });
      });
    });

    req.on('error', (err) => {
      resolve({
        statusCode: 503,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: 503, message: '后端服务不可用: ' + err.message }),
      });
    });

    if (body && ['POST', 'PUT', 'PATCH'].includes(httpMethod)) {
      req.write(body);
    }
    req.end();
  });
};
