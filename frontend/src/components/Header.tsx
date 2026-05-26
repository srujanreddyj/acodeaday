import { Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import {
  BookOpen,
  Brain,
  ChevronDown,
  LogOut,
  Map,
  Menu,
  Trophy,
  TrendingUp,
  X,
} from 'lucide-react'
import { useAuth } from '@/hooks'

const primaryNav = [
  { to: '/roadmap' as const, label: 'Roadmap', icon: Map },
  { to: '/progress' as const, label: 'Progress Overview', icon: TrendingUp },
  { to: '/flashcards' as const, label: 'Daily Flashcard', icon: Brain },
]

export default function Header() {
  const [isOpen, setIsOpen] = useState(false)
  const { logout, email } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    setIsOpen(false)
    navigate({ to: '/login' })
  }

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-white/8 bg-[#1c1d22]/96 text-white backdrop-blur-xl">
        <div className="flex items-center justify-between gap-4 px-5 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsOpen(true)}
              className="rounded-xl p-2 text-gray-300 transition hover:bg-white/5 hover:text-white md:hidden"
              aria-label="Open menu"
            >
              <Menu size={22} />
            </button>

            <Link to="/roadmap" className="flex items-center gap-4 transition-opacity hover:opacity-90">
              <span className="grid h-12 w-12 place-items-center rounded-full bg-[radial-gradient(circle_at_30%_30%,#d899c3,#925586)] shadow-[0_10px_30px_rgba(0,0,0,0.25)]">
                <Trophy size={21} className="text-[#2e1f26]" />
              </span>
              <div className="flex flex-col leading-none">
                <span className="text-[18px] font-bold tracking-tight text-white sm:text-[20px]">acodeaday</span>
                <span className="hidden text-[11px] uppercase tracking-[0.22em] text-[#a7aab3] sm:block">Personal DSA Notes</span>
              </div>
            </Link>
          </div>

          <nav className="hidden items-center gap-2 lg:flex">
            {primaryNav.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className="inline-flex items-center gap-2 rounded-2xl border border-transparent px-5 py-3 text-[15px] font-semibold text-[#c8cbd4] transition hover:border-white/8 hover:bg-white/[0.03] hover:text-white"
                activeProps={{
                  className:
                    'inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-3 text-[15px] font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]',
                }}
              >
                <Icon size={18} />
                <span>{label}</span>
              </Link>
            ))}
            <button className="inline-flex items-center gap-2 rounded-2xl px-4 py-3 text-[15px] font-semibold text-[#aeb2bc] transition hover:bg-white/[0.03] hover:text-white">
              <span>More</span>
              <ChevronDown size={16} />
            </button>
          </nav>

          <div className="flex items-center gap-3">
            {email && <div className="hidden text-sm text-[#afb2bb] xl:block">{email}</div>}
            <button
              onClick={() => setIsOpen(true)}
              className="hidden rounded-xl p-2 text-gray-300 transition hover:bg-white/5 hover:text-white md:inline-flex"
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
          </div>
        </div>
      </header>

      <aside
        className={`fixed left-0 top-0 z-[70] flex h-full w-80 transform flex-col border-r border-white/8 bg-[#1c1d22]/98 text-white shadow-2xl shadow-black/40 backdrop-blur-xl transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between border-b border-white/8 p-4">
          <h2 className="text-lg font-semibold text-white">Navigation</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="rounded-lg p-2 text-gray-300 transition hover:bg-white/5 hover:text-white"
            aria-label="Close menu"
          >
            <X size={22} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-4">
          <a
            href="https://acodeaday.vercel.app"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setIsOpen(false)}
            className="mb-2 flex items-center gap-3 rounded-xl p-3 text-[#d6d9df] transition hover:bg-white/5 hover:text-white"
          >
            <BookOpen size={20} />
            <span className="font-medium">Documentation</span>
          </a>

          <div className="my-4 border-t border-white/8" />

          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl p-3 text-[#ef8188] transition hover:bg-[#ef3537]/10 hover:text-[#ff9aa1]"
          >
            <LogOut size={20} />
            <span className="font-medium">Logout</span>
          </button>
        </nav>
      </aside>
    </>
  )
}
