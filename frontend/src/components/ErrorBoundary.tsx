import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/Button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI error boundary', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="bg-mesh flex min-h-screen items-center justify-center p-6">
          <div className="card-surface max-w-md rounded-3xl p-8 text-center">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-rose-600">
              页面异常
            </div>
            <h1 className="font-display text-xl font-semibold text-ink-900">出错了</h1>
            <p className="mt-2 text-sm text-muted">
              {this.state.error.message || '未知错误'}。可尝试刷新页面或重新登录。
            </p>
            <div className="mt-6 flex justify-center gap-2">
              <Button
                onClick={() => {
                  this.setState({ error: null })
                  window.location.assign('/')
                }}
              >
                返回首页
              </Button>
              <Button variant="outline" onClick={() => window.location.reload()}>
                刷新
              </Button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
