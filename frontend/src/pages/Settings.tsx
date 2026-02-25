import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

interface Settings {
  apiKey: string
  model: string
  customModel: string
  baseUrl: string
  temperature: number
  maxTokens: number
}

const DEFAULT_SETTINGS: Settings = {
  apiKey: '',
  model: 'deepseek-chat',
  customModel: '',
  baseUrl: 'https://api.deepseek.com',
  temperature: 0.7,
  maxTokens: 2000,
}

const MODELS = [
  { value: 'deepseek-chat', label: 'DeepSeek Chat', baseUrl: 'https://api.deepseek.com' },
  { value: 'gpt-4', label: 'GPT-4', baseUrl: 'https://api.openai.com' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', baseUrl: 'https://api.openai.com' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', baseUrl: 'https://api.openai.com' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus', baseUrl: 'https://api.anthropic.com' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet', baseUrl: 'https://api.anthropic.com' },
  { value: 'claude-3-haiku', label: 'Claude 3 Haiku', baseUrl: 'https://api.anthropic.com' },
  { value: 'custom', label: '其他 (自定义)' },
]

export default function Settings() {
  const navigate = useNavigate()
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)
  const [saved, setSaved] = useState(false)
  const [showKey, setShowKey] = useState(false)

  useEffect(() => {
    const savedSettings = localStorage.getItem('user_settings')
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings)
        setSettings({ ...DEFAULT_SETTINGS, ...parsed })
      } catch (e) {
        console.error('Failed to parse settings:', e)
      }
    }
  }, [])

  const handleSave = () => {
    localStorage.setItem('user_settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    if (confirm('确定要重置所有设置为默认值吗？')) {
      setSettings(DEFAULT_SETTINGS)
      localStorage.removeItem('user_settings')
    }
  }

  const handleChange = (field: keyof Settings, value: string | number) => {
    setSettings(prev => ({ ...prev, [field]: value }))
  }

  const handleModelChange = (modelValue: string) => {
    const model = MODELS.find(m => m.value === modelValue)
    if (model && modelValue !== 'custom' && model.baseUrl) {
      setSettings(prev => ({
        ...prev,
        model: modelValue,
        baseUrl: model.baseUrl || ''
      }))
    } else {
      setSettings(prev => ({ ...prev, model: modelValue }))
    }
  }

  const getCurrentModel = () => {
    if (settings.model === 'custom') {
      return settings.customModel || '自定义模型'
    }
    const model = MODELS.find(m => m.value === settings.model)
    return model?.label || settings.model
  }

  const showBaseUrl = settings.model === 'custom'

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">设置</h1>
          <p className="text-gray-500 mt-1">配置您的AI模型和API设置</p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200/50 p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">API 配置</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                模型 API Key
              </label>
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={settings.apiKey}
                  onChange={(e) => handleChange('apiKey', e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-4 py-2.5 pr-10 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showKey ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                您的API密钥将仅保存在浏览器本地，不会发送到服务器
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  模型选择
                </label>
                <select
                  value={settings.model}
                  onChange={(e) => handleModelChange(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {MODELS.map(model => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </select>
              </div>

              {settings.model === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    自定义模型名称
                  </label>
                  <input
                    type="text"
                    value={settings.customModel}
                    onChange={(e) => handleChange('customModel', e.target.value)}
                    placeholder="例如: my-model-v1"
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}
            </div>

            {showBaseUrl && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API 端点
                </label>
                <input
                  type="text"
                  value={settings.baseUrl}
                  onChange={(e) => handleChange('baseUrl', e.target.value)}
                  placeholder="https://api.example.com"
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex items-center gap-2 text-blue-800">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm font-medium">
                  当前使用: {getCurrentModel()}
                  {showBaseUrl && settings.baseUrl && ` (${settings.baseUrl})`}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={handleReset}
          className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          重置为默认
        </button>
        
        <button
          onClick={handleSave}
          className={`px-6 py-2.5 rounded-xl font-medium transition-all ${
            saved
              ? 'bg-green-600 text-white'
              : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/25'
          }`}
        >
          {saved ? '✓ 已保存' : '保存设置'}
        </button>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <h3 className="text-sm font-medium text-yellow-800">注意</h3>
            <p className="text-xs text-yellow-700 mt-1">
              当前设置仅保存在浏览器本地。如果清除浏览器数据，设置将被重置。
              生产环境建议通过环境变量配置。
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
