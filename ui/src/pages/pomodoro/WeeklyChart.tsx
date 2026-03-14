import { BarChart, Bar, XAxis, ResponsiveContainer, Cell } from 'recharts'

interface WeeklyChartProps {
  daily: Record<string, number>
}

function getLast7Days(): string[] {
  const days: string[] = []
  const now = new Date()
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    days.push(d.toISOString().split('T')[0])
  }
  return days
}

function shortDay(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en', { weekday: 'short' }).slice(0, 2)
}

export function WeeklyChart({ daily }: WeeklyChartProps) {
  const days = getLast7Days()
  const data = days.map((date) => ({
    name: shortDay(date),
    count: daily[date] ?? 0,
  }))

  return (
    <ResponsiveContainer width="100%" height={120}>
      <BarChart data={data} barCategoryGap="30%">
        <XAxis
          dataKey="name"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={24}>
          {data.map((entry, index) => (
            <Cell
              key={index}
              fill={entry.count > 0 ? 'var(--color-primary)' : 'var(--color-border)'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
