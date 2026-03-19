import { Construction } from 'lucide-react'
import { motion } from 'framer-motion'

export function PlaceholderPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col items-center justify-center h-full gap-3 text-center p-4"
    >
      <Construction size={40} className="text-text-muted" />
      <h2 className="font-heading text-lg font-bold text-text">Coming Soon</h2>
      <p className="text-sm text-text-muted max-w-[240px]">
        This feature is being built. Check back soon!
      </p>
    </motion.div>
  )
}
