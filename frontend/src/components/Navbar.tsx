interface NavbarProps {
  user?: {
    id: string
    username: string
    email: string
    role: string
  } | null
  onLogout?: () => void
}

export default function Navbar({ user, onLogout }: NavbarProps) {
  return (
    <nav className="h-14 bg-white/80 backdrop-blur-md border-b border-gray-200/50 flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/25">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="font-bold text-gray-900">CodeInsight</span>
          <span className="text-xs text-gray-400 hidden sm:inline">智能代码分析平台</span>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-gray-900">{user.username}</p>
              <p className="text-xs text-gray-500">{user.role === 'admin' ? '管理员' : '用户'}</p>
            </div>
          </div>
        )}
        
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-1.5"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="hidden sm:inline">API</span>
        </a>
        
        <div className="w-px h-5 bg-gray-200"></div>
        
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="hidden sm:inline">运行中</span>
        </div>
        
        {onLogout && (
          <>
            <div className="w-px h-5 bg-gray-200"></div>
            <button
              onClick={onLogout}
              className="text-sm text-gray-600 hover:text-red-600 transition-colors flex items-center gap-1.5"
              title="退出登录"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden sm:inline">退出</span>
            </button>
          </>
        )}
      </div>
    </nav>
  )
}
