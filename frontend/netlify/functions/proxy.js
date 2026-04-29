/**
 * Netlify Edge Function: API 反向代理
 * 将所有 /api/* 请求转发到后端服务
 * 环境变量: BACKEND_URL（如 https://028662142bd97438-153-254-110-180.serveousercontent.com）
 */
export default async (request, context) => {
  const BACKEND_URL = Deno.env.get('BACKEND_URL') || 'https://028662142bd97438-153-254-110-180.serveousercontent.com';

  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/api/, ''); // 去掉 /api 前缀

  const targetUrl = `${BACKEND_URL}/api${path}${url.search}`;

  try {
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': request.headers.get('User-Agent') || 'caviar-crm-proxy/1.0',
        'Accept': 'application/json',
        ...Object.fromEntries(
          [...request.headers.entries()].filter(([k]) =>
            !['host', 'connection', 'content-length'].includes(k.toLowerCase())
          )
        ),
      },
      body: ['POST', 'PUT', 'PATCH'].includes(request.method)
        ? await request.text()
        : undefined,
    });

    const data = await response.text();
    const contentType = response.headers.get('content-type') || 'application/json';

    return new Response(data, {
      status: response.status,
      headers: {
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': '*',
      },
    });
  } catch (err) {
    return new Response(JSON.stringify({ code: 503, message: '后端服务不可用: ' + err.message }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};