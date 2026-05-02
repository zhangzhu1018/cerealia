import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API = 'https://1be7f8a2b839364c-218-104-202-62.serveousercontent.com/api'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!email.trim() || !password.trim()) {
      setError('请输入邮箱和密码')
      return
    }
    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      })
      const data = await res.json()
      if (data.code !== 200) {
        setError(data.message || '登录失败')
        return
      }

      localStorage.setItem('caviar_token', data.data.token)
      localStorage.setItem('caviar_user', JSON.stringify(data.data.user))
      navigate('/', { replace: true })
    } catch (err) {
      setError('网络错误，请检查连接')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-caviar-dark flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-wider text-caviar-gold">
            Cerealia Caviar
          </h1>
          <p className="text-caviar-muted mt-2 text-sm">CRM · 客户管理系统</p>
        </div>

        {/* 登录卡片 */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-8">
          <h2 className="text-lg font-medium text-caviar-text mb-6">登录</h2>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs text-caviar-muted mb-1.5">邮箱</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-caviar-text text-sm placeholder:text-caviar-muted/50 focus:border-caviar-gold/50 focus:outline-none transition-colors"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs text-caviar-muted mb-1.5">密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="输入密码"
                className="w-full bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-caviar-text text-sm placeholder:text-caviar-muted/50 focus:border-caviar-gold/50 focus:outline-none transition-colors"
              />
            </div>

            {error && (
              <div className="text-red-400 text-xs bg-red-900/20 border border-red-700/30 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-caviar-gold text-caviar-dark font-medium rounded-lg py-2.5 text-sm hover:bg-caviar-gold/90 disabled:opacity-50 transition-colors"
            >
              {loading ? '登录中...' : '登 录'}
            </button>
          </form>
        </div>

        <p className="text-center text-caviar-muted/40 text-xs mt-6">
          Cerealia Caviar © 2015-2026
        </p>
      </div>
    </div>
  )
}
