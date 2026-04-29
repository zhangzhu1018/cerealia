#!/usr/bin/env node
/**
 * Caviar CRM 前端全面测试脚本
 * 测试所有页面模块
 */
const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:3004';

const pages = [
  { name: '仪表盘', path: '/' },
  { name: '客户列表', path: '/customers' },
  { name: '客户导入', path: '/customers/import' },
  { name: '搜索页面', path: '/search' },
  { name: '邮件生成', path: '/emails' },
  { name: '邮件设置', path: '/email-settings' },
  { name: '活动日志', path: '/activities' },
];

async function testPage(browser, pageInfo) {
  const { name, path } = pageInfo;
  const context = await browser.newContext();
  const page = await context.newPage();

  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  try {
    const response = await page.goto(`${BASE_URL}${path}`, {
      waitUntil: 'domcontentloaded',
      timeout: 15000
    });

    await page.waitForTimeout(2500);

    const title = await page.title();
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 150));

    const status = response ? response.status() : 0;
    const statusIcon = status >= 200 && status < 400 ? '✅' : status >= 400 && status < 500 ? '⚠️' : '❌';

    console.log(`  ${statusIcon} ${name} (${path}): HTTP ${status} | "${title}"`);
    console.log(`     内容: ${bodyText.replace(/\n/g, ' ').substring(0, 100)}`);

    if (consoleErrors.length > 0) {
      console.log(`     ⚠️  Console Errors (${consoleErrors.length}):`);
      consoleErrors.slice(0, 3).forEach(e => console.log(`       - ${e.substring(0, 100)}`));
    }

    await context.close();
    return { name, path, status, title, errors: consoleErrors.length };
  } catch (err) {
    console.log(`  ❌ ${name} (${path}): ${err.message.substring(0, 80)}`);
    await context.close();
    return { name, path, status: 0, error: err.message };
  }
}

async function main() {
  console.log('🚀 Caviar CRM 全面测试开始');
  console.log('='.repeat(60));

  const browser = await chromium.launch({ headless: true });

  const results = [];
  for (const pageInfo of pages) {
    const result = await testPage(browser, pageInfo);
    results.push(result);
  }

  console.log('\n' + '='.repeat(60));
  console.log('📊 测试结果汇总');
  console.log('='.repeat(60));

  const passCount = results.filter(r => r.status >= 200 && r.status < 500 && !r.error).length;
  const warnCount = results.filter(r => r.errors > 0 && !r.error).length;
  const failCount = results.filter(r => r.status === 0 || r.error).length;

  results.forEach(r => {
    const icon = r.status >= 200 && r.status < 400 && !r.error ? '✅' : r.status >= 400 && r.status < 500 ? '⚠️' : '❌';
    const errInfo = r.errors > 0 ? ` (${r.errors} console errors)` : '';
    const errorInfo = r.error ? ` ERROR: ${r.error.substring(0, 60)}` : '';
    console.log(`  ${icon} ${r.name}: HTTP ${r.status}${errInfo}${errorInfo}`);
  });

  console.log(`\n总计: ${passCount} 通过, ${warnCount} 警告, ${failCount} 失败`);

  await browser.close();
  process.exit(failCount > 0 ? 1 : 0);
}

main().catch(err => {
  console.error('测试脚本执行失败:', err);
  process.exit(1);
});
