// 最小测试函数 — 验证 Netlify Function 是否能正常响应
exports.handler = async (event, context) => {
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    body: JSON.stringify({
      ok: true,
      message: 'Netlify Function 正常',
      path: event.path,
      method: event.httpMethod,
    }),
  };
};
