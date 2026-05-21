import { Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'

export default function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-20"
    >
      <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      <p className="mt-3 text-sm text-slate-400">{message}</p>
    </motion.div>
  )
}
