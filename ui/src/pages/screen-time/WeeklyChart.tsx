import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface WeeklyChartProps {
  dailyTotals: Array<{
    date: string
    total_s: number
    breakdown: Record<string, number>
  }>
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function WeeklyChart({ dailyTotals }: WeeklyChartProps) {
  const data = dailyTotals.map((d, i) => ({
    day: DAYS[i] || d.date.slice(5),
    hours: Math.round((d.total_s / 3600) * 10) / 10,
    productive: Math.round(((d.breakdown?.Productive || 0) / 3600) * 10) / 10,
    neutral: Math.round(((d.breakdown?.Neutral || 0) / 3600) * 10) / 10,
    distracting: Math.round(((d.breakdown?.Distracting || 0) / 3600) * 10) / 10,
  }))

  return (
    <div>
      <h3 className="text-xs font-heading font-semibold text-text-muted uppercase tracking-wide mb-2">
        This Week
      </h3>
      <div className="bg-surface border border-border rounded-default p-3" style={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="day" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} unit="h" width={30} />
            <Tooltip
              formatter={(value) => [`${value}h`, '']}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Bar dataKey="productive" stackId="a" fill="var(--color-success)" radius={[0, 0, 0, 0]} />
            <Bar dataKey="neutral" stackId="a" fill="var(--color-border-hover)" />
            <Bar dataKey="distracting" stackId="a" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
