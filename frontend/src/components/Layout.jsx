/**
 * Layout — 紧凑经典左右布局
 * 侧栏固定 + 紧凑顶栏 + 页面内容
 */
import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'

const pageTitles = {
  '/':                   { label: '总工作台',  desc: '全局数据概览' },
  '/customers':          { label: '客户管理',  desc: '客户列表与详情' },
  '/customers/import':   { label: '批量导入', desc: 'Excel/CSV 导入' },
  '/emails':             { label: '邮件生成',  desc: '生成并发送邮件' },
  '/email-settings':     { label: '邮件管理',  desc: '发件账号与任务' },
  '/search':             { label: '客户搜索',  desc: '全网搜索潜在客户' },
  '/activities':         { label: '操作日志',  desc: '系统操作记录' },
}

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [loading, setLoading]     = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  const getPageInfo = () => {
    if (
      location.pathname.startsWith('/customers/') &&
      location.pathname !== '/customers/import'
    ) {
      return { label: '客户详情', desc: '查看并编辑客户信息' }
    }
    return pageTitles[location.pathname] || { label: 'Cerealia CRM', desc: '' }
  }

  const pageInfo = getPageInfo()

  return (
    <div className="app-shell">

      {/* 左侧固定侧栏 */}
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      {/* 右侧主内容区 */}
      <div className={['app-main', collapsed ? 'sidebar-collapsed' : ''].filter(Boolean).join(' ')}>

        {/* 顶栏 */}
        <header className="topbar">
          <div className="topbar-breadcrumb">
            <span>{pageInfo.label}</span>
            {pageInfo.desc && (
              <>
                <span className="topbar-breadcrumb-sep">/</span>
                <span style={{ color: 'var(--color-text-secondary)' }}>{pageInfo.desc}</span>
              </>
            )}
          </div>
          <div className="topbar-actions">
            <button
              onClick={() => navigate('/customers')}
              className="btn btn-primary btn-sm"
            >
              + 新建客户
            </button>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="page-content">
          {loading ? (
            <div className="empty-state">
              <span className="spinner" />
              <span className="text-muted">加载中...</span>
            </div>
          ) : (
            <Outlet context={{ setLoading }} />
          )}
        </main>
      </div>
    </div>
  )
}
