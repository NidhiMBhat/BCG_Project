import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Heart, Lock, User } from 'lucide-react'

export default function LoginPage() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await login(form.username, form.password)
      navigate('/')
    } catch (e) {
      setError(e.message || 'Invalid credentials')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-cyan/5 rounded-full blur-3xl" />

      <div className="relative w-full max-w-md animate-slide-in">
        {/* Card */}
        <div className="glass-card p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-accent-cyan shadow-xl shadow-brand-500/30 mb-4">
              <Heart className="w-8 h-8 text-brand-900" />
            </div>
            <h1 className="text-2xl font-bold text-brand-900">BCG Healthcare</h1>
            <p className="text-brand-700/80 mt-1 text-sm">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-brand-700/80 uppercase tracking-wider mb-1.5">Username</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-700/60" />
                <input
                  id="username"
                  type="text"
                  className="input-field pl-10"
                  placeholder="Enter username"
                  value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-brand-700/80 uppercase tracking-wider mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-700/60" />
                <input
                  id="password"
                  type="password"
                  className="input-field pl-10"
                  placeholder="Enter password"
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  required
                />
              </div>
            </div>

            {error && (
              <div className="px-4 py-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm animate-fade-in">
                {error}
              </div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 text-base mt-2"
            >
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-6 pt-6 border-t border-brand-900/10">
            <p className="text-xs text-brand-700/60 text-center mb-3">Demo Credentials</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { u: 'admin', p: 'admin123', r: 'Admin' },
                { u: 'doctor1', p: 'doctor123', r: 'Doctor' },
              ].map(c => (
                <button
                  key={c.u}
                  onClick={() => setForm({ username: c.u, password: c.p })}
                  className="text-left px-3 py-2 rounded-lg bg-surface-600 hover:bg-surface-500 transition-colors border border-brand-900/10"
                >
                  <p className="text-xs font-semibold text-brand-800">{c.r}</p>
                  <p className="text-xs text-brand-700/60 font-mono">{c.u}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-4">
          BCG Healthcare Platform v1.0 — Research Demonstration
        </p>
      </div>
    </div>
  )
}
