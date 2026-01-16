"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, DollarSign, Leaf, Percent } from "lucide-react"

export function PoolingStats() {
  const [stats, setStats] = useState({
    successRate: 0,
    avgSavings: 0,
    monthTotal: 0,
  })

  useEffect(() => {
    const animate = () => {
      const duration = 1500
      const steps = 60
      const increment = duration / steps
      let step = 0

      const timer = setInterval(() => {
        step++
        const progress = step / steps
        setStats({
          successRate: Math.round(92 * progress),
          avgSavings: Math.round(26 * progress),
          monthTotal: Math.round(48500 * progress),
        })
        if (step >= steps) clearInterval(timer)
      }, increment)

      return () => clearInterval(timer)
    }
    animate()
  }, [])

  const topLanes = [
    { lane: "LA → Dallas", volume: 142, savings: 18200 },
    { lane: "Chicago → Atlanta", volume: 98, savings: 12400 },
    { lane: "Seattle → Phoenix", volume: 76, savings: 9800 },
    { lane: "NY → Miami", volume: 65, savings: 8200 },
  ]

  return (
    <>
      {/* Stats Cards */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Percent className="h-4 w-4 text-primary" />
            Success Rate
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-primary">{stats.successRate}%</p>
          <p className="text-xs text-muted-foreground mt-1">of pooling attempts</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-500" />
            Avg Savings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-emerald-500">{stats.avgSavings}%</p>
          <p className="text-xs text-muted-foreground mt-1">per pooled shipment</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-amber-500" />
            This Month
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-amber-500">${stats.monthTotal.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground mt-1">total savings</p>
        </CardContent>
      </Card>

      {/* Top Lanes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Best Performing Lanes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {topLanes.map((lane, i) => (
            <div key={lane.lane} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{lane.lane}</span>
                <span className="text-emerald-500 font-semibold">${lane.savings.toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 bg-primary/20 rounded-full flex-1" style={{ maxWidth: "100%" }}>
                  <div className="h-full bg-primary rounded-full" style={{ width: `${(lane.volume / 142) * 100}%` }} />
                </div>
                <span className="text-xs text-muted-foreground w-12 text-right">{lane.volume} loads</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Environmental Impact */}
      <Card className="bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
            <Leaf className="h-4 w-4" />
            Environmental Impact
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-emerald-600">12.4 tons</p>
          <p className="text-xs text-emerald-600/80 mt-1">CO2 saved this month</p>
        </CardContent>
      </Card>
    </>
  )
}
