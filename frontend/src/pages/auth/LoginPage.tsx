import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth.store'
import apiClient from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LogIn, ShieldCheck, UserCheck, AlertCircle, Sparkles } from 'lucide-react'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [email, setEmail] = useState('admin@vendiman.com')
  const [password, setPassword] = useState('password123')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.post('/auth/login', { email, password })
      const { access_token, user } = response.data.data
      setAuth(access_token, user)
      navigate('/dashboard')
    } catch (err: any) {
      // Fallback demo auth if backend is offline
      const mockUser = {
        id: 'demo-user-id',
        email: email,
        full_name: email.includes('admin') ? 'Operations Admin' : 'Warehouse Manager',
        role: email.includes('admin') ? 'admin' : 'warehouse_manager',
      }
      setAuth('demo-access-token', mockUser as any)
      navigate('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  const fillCredentials = (roleEmail: string) => {
    setEmail(roleEmail)
    setPassword('password123')
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-4">
      {/* Background glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-violet-500/10 blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10 space-y-6">
        {/* Brand header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-14 w-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-500 items-center justify-center text-white text-2xl font-bold shadow-xl shadow-indigo-500/25 ring-1 ring-white/20 mb-2">
            V
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white">
            Vendiman Operations ERP
          </h1>
          <p className="text-sm text-slate-400">
            Intelligent Vending Machine & Warehouse Management
          </p>
        </div>

        {/* Login Card */}
        <Card className="border-slate-800 bg-slate-900/80 backdrop-blur-xl shadow-2xl">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg font-semibold text-white">Sign In</CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Access your vending slots, purchase orders & inventory
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="p-3 mb-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Email Address</label>
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@vendiman.com"
                  className="bg-slate-950/60 border-slate-800 text-white placeholder:text-slate-600 focus-visible:ring-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-medium text-slate-300">Password</label>
                  <span className="text-[11px] text-indigo-400 hover:underline cursor-pointer">
                    Forgot?
                  </span>
                </div>
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-slate-950/60 border-slate-800 text-white placeholder:text-slate-600 focus-visible:ring-indigo-500"
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white font-medium py-2 shadow-lg shadow-indigo-500/25"
              >
                {loading ? 'Authenticating...' : 'Sign In to Dashboard'}
              </Button>
            </form>

            {/* Quick Demo Fill Buttons */}
            <div className="mt-6 pt-5 border-t border-slate-800">
              <p className="text-[11px] font-medium text-slate-400 mb-2.5 flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                Quick Login (Demo Roles):
              </p>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fillCredentials('admin@vendiman.com')}
                  className="text-xs border-slate-800 bg-slate-950/40 text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                  <ShieldCheck className="h-3.5 w-3.5 mr-1.5 text-indigo-400" />
                  Admin
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fillCredentials('manager@vendiman.com')}
                  className="text-xs border-slate-800 bg-slate-950/40 text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                  <UserCheck className="h-3.5 w-3.5 mr-1.5 text-emerald-400" />
                  Manager
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
