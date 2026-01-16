"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { DollarSign, Package, Percent, Clock, Leaf, TrendingUp, TrendingDown } from "lucide-react"

const kpis = [
  {
    label: "Total Revenue",
    value: 2847500,
    prefix: "$",
    trend: 12.5,
    trendUp: true,
    icon: DollarSign,
    color: "text-emerald-500",
    bgColor: "bg-emerald-100 dark:bg-emerald-900",
  },
  {
    label: "Shipments This Month",
    value: 1842,
    prefix: "",
    trend: 8.3,
    trendUp: true,
    icon: Package,
    color: "text-blue-500",
    bgColor: "bg-blue-100 dark:bg-blue-900",
  },
  {
    label: "Pooling Rate",
    value: 68,
    prefix: "",
    suffix: "%",
    trend: 5.2,
    trendUp: true,
    icon: Percent,
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
  {
    label: "Avg Savings",
    value: 26,
    prefix: "",
    suffix: "%",
    trend: 2.1,
    trendUp: true,
    icon: TrendingUp,
    color: "text-amber-500",
    bgColor: "bg-amber-100 dark:bg-amber-900",
  },
  {
    label: "On-Time Delivery",
    value: 97.3,
    prefix: "",
    suffix: "%",
    trend: 0.8,
    trendUp: false,
    icon: Clock,
    color: "text-violet-500",
    bgColor: "bg-violet-100 dark:bg-violet-900",
  },
  {
    label: "Carbon Saved",
    value: 12450,
    prefix: "",
    suffix: " kg",
    trend: 15.4,
    trendUp: true,
    icon: Leaf,
    color: "text-emerald-600",
    bgColor: "bg-emerald-100 dark:bg-emerald-900",
  },
]

export function KPICards() {
  const [animatedValues, setAnimatedValues] = useState(kpis.map(() => 0))

  useEffect(() => {
    const duration = 1500
    const steps = 60
    const increment = duration / steps
    let step = 0

    const timer = setInterval(() => {
      step++
      const progress = step / steps
      setAnimatedValues(kpis.map((kpi) => Math.round(kpi.value * progress * 10) / 10))
      if (step >= steps) clearInterval(timer)
    }, increment)

    return () => clearInterval(timer)
  }, [])

  const formatValue = (value: number, prefix?: string, suffix?: string) => {
    if (value >= 1000000) {
      return `${prefix || ""}${(value / 1000000).toFixed(2)}M${suffix || ""}`
    }
    if (value >= 1000) {
      return `${prefix || ""}${(value / 1000).toFixed(1)}K${suffix || ""}`
    }
    return `${prefix || ""}${value.toLocaleString()}${suffix || ""}`
  }

  return (
    <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
      {kpis.map((kpi, i) => {
        const Icon = kpi.icon
        return (
          <Card key={kpi.label} className="overflow-hidden">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${kpi.bgColor}`}>
                  <Icon className={`h-5 w-5 ${kpi.color}`} />
                </div>
                <div
                  className={`flex items-center gap-1 text-xs font-medium ${kpi.trendUp ? "text-emerald-500" : "text-red-500"}`}
                >
                  {kpi.trendUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {kpi.trend}%
                </div>
              </div>
              <p className="text-2xl font-bold">{formatValue(animatedValues[i], kpi.prefix, kpi.suffix)}</p>
              <p className="text-xs text-muted-foreground mt-1">{kpi.label}</p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
