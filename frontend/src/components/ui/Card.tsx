import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  padding?: boolean
  hover?: boolean
}

export default function Card({ children, className, padding = true, hover = false }: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn(
        'bg-white rounded-2xl border border-slate-100 shadow-card',
        padding && 'p-6',
        hover && 'hover:shadow-card-hover transition-shadow duration-300',
        className
      )}
    >
      {children}
    </motion.div>
  )
}
