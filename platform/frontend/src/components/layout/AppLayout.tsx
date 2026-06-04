/**
 * AppLayout — Main application shell with sidebar navigation.
 * Sidebar shows on desktop; collapses to hamburger on mobile.
 */
import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, User, Briefcase, TrendingUp, Star,
  BarChart3, LogOut, Menu, X, Map, BarChart2
} from 'lucide-react'
import { useAuthContext } from '@/contexts/AuthContext'

const navItems = [
  { path: '/dashboard',       label: 'Dashboard',       icon: LayoutDashboard },
  { path: '/profile',         label: 'My Profile',      icon: User },
  { path: '/jobs',            label: 'Job Explorer',    icon: Briefcase },
  { path: '/roadmap',         label: 'Roadmap',         icon: Map },
  { path: '/recommendations', label: 'Recommendations', icon: Star },
  { path: '/skills',          label: 'Skill Analysis',  icon: TrendingUp },
  { path: '/market',          label: 'Market',          icon: BarChart2 },
]

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuthContext()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-primary-50 text-primary-700 border border-primary-100'
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
    }`

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-100">
        <div className="flex items-center justify-center w-9 h-9 bg-primary-600 rounded-lg shadow-sm">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-gray-900 text-lg">CareerGraph</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={navLinkClass}
            onClick={() => setMobileOpen(false)}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <span className="text-primary-700 text-sm font-semibold">
              {user?.name?.charAt(0).toUpperCase() ?? 'U'}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.name ?? 'User'}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email ?? ''}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 rounded-lg hover:bg-red-50 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-64 flex-col bg-white border-r border-gray-200 flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="fixed left-0 top-0 h-full w-64 bg-white z-50 shadow-xl">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile topbar */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-gray-900">CareerGraph</span>
          </div>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
