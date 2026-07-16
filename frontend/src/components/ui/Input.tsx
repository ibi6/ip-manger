import { cn } from '@/lib/cn'
import {
  Children,
  cloneElement,
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactElement,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from 'react'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
  return (
    <input
      ref={ref}
      className={cn(
        'min-h-11 w-full rounded-2xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink-900 outline-none transition placeholder:text-muted focus:border-teal-500 focus:ring-4 focus:ring-teal-500/12',
        className,
      )}
      {...props}
    />
  )
  },
)

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        'min-h-11 w-full rounded-2xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink-900 outline-none transition focus:border-teal-500 focus:ring-4 focus:ring-teal-500/12',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  )
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        'w-full resize-y rounded-2xl border border-line bg-surface px-3.5 py-2.5 text-sm text-ink-900 outline-none transition placeholder:text-muted focus:border-teal-500 focus:ring-4 focus:ring-teal-500/12',
        className,
      )}
      {...props}
    />
  )
}

export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-xs font-medium tracking-wide text-ink-700">
      {children}
    </label>
  )
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string
  children: ReactNode
  hint?: string
}) {
  const generatedId = useId().replaceAll(':', '')
  const control = Children.only(children) as ReactElement<{
    id?: string
    'aria-describedby'?: string
  }>
  const controlId = control.props.id || `field-${generatedId}`
  const hintId = hint ? `${controlId}-hint` : undefined
  const describedBy = [control.props['aria-describedby'], hintId].filter(Boolean).join(' ')

  return (
    <div>
      <Label htmlFor={controlId}>{label}</Label>
      {cloneElement(control, {
        id: controlId,
        'aria-describedby': describedBy || undefined,
      })}
      {hint ? (
        <p id={hintId} className="mt-1 text-xs text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  )
}
