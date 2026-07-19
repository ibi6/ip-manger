import { ArrowLeft, LayoutDashboard, SearchX } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

export function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-[62vh] items-center justify-center py-8">
      <Card className="relative w-full max-w-2xl overflow-hidden px-6 py-12 text-center sm:px-12">
        <div
          className="absolute inset-x-20 top-0 h-32 rounded-full bg-teal-500/10 blur-3xl"
          aria-hidden="true"
        />
        <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-surface-muted text-teal-700 ring-1 ring-line">
          <SearchX className="h-8 w-8" aria-hidden="true" />
        </div>
        <p className="relative mt-6 text-xs font-semibold uppercase tracking-[0.24em] text-teal-700">
          404 · Page not found
        </p>
        <h1 className="relative mt-3 font-display text-3xl font-semibold text-ink-950 sm:text-4xl">
          没有找到这个页面
        </h1>
        <p className="relative mx-auto mt-4 max-w-md text-sm leading-7 text-muted">
          地址可能已变更或输入有误。你可以返回上一页，或从工作台重新进入需要的功能。
        </p>
        <div className="relative mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <Button onClick={() => navigate('/')}>
            <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
            返回工作台
          </Button>
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            返回上一页
          </Button>
        </div>
      </Card>
    </div>
  )
}
