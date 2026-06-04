import { Loader2 } from 'lucide-react'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  text?: string
}

const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' }

export function LoadingSpinner({ size = 'md', text }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <Loader2 className={`${sizes[size]} text-primary-500 animate-spin`} />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  )
}
