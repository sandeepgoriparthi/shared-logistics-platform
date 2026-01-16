"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"

const data = [
  { name: "Pooled", value: 68, color: "hsl(var(--primary))" },
  { name: "Individual", value: 32, color: "hsl(var(--muted))" },
]

export function PoolingPerformance() {
  const [savings, setSavings] = useState(0)

  useEffect(() => {
    const duration = 1500
    const target = 485000
    const steps = 60
    const increment = duration / steps
    let step = 0

    const timer = setInterval(() => {
      step++
      setSavings(Math.round((target * step) / steps))
      if (step >= steps) clearInterval(timer)
    }, increment)

    return () => clearInterval(timer)
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pooling Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-72 relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} cx="50%" cy="50%" innerRadius={80} outerRadius={110} paddingAngle={2} dataKey="value">
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <p className="text-sm text-muted-foreground">Total Savings</p>
            <p className="text-3xl font-bold text-primary">${(savings / 1000).toFixed(0)}K</p>
          </div>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4 text-sm">
          {data.map((item) => (
            <div key={item.name} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} />
              <span>
                {item.name} ({item.value}%)
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
