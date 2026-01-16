"use client"

import { useEffect, useState } from "react"
import { DollarSign, Package, Leaf, Clock } from "lucide-react"

const stats = [
  {
    label: "Total Savings",
    value: 2400000,
    prefix: "$",
    suffix: "",
    format: "currency",
    icon: DollarSign,
    color: "text-emerald-500",
  },
  {
    label: "Shipments Pooled",
    value: 15420,
    prefix: "",
    suffix: "",
    format: "number",
    icon: Package,
    color: "text-blue-500",
  },
  {
    label: "CO2 Reduced",
    value: 450,
    prefix: "",
    suffix: " tons",
    format: "number",
    icon: Leaf,
    color: "text-emerald-500",
  },
  {
    label: "On-Time Rate",
    value: 97.3,
    prefix: "",
    suffix: "%",
    format: "percent",
    icon: Clock,
    color: "text-amber-500",
  },
]

function AnimatedNumber({
  value,
  prefix,
  suffix,
  format,
}: {
  value: number
  prefix: string
  suffix: string
  format: string
}) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    const duration = 2000
    const steps = 60
    const increment = value / steps
    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= value) {
        setDisplayValue(value)
        clearInterval(timer)
      } else {
        setDisplayValue(current)
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [value])

  const formatted =
    format === "currency"
      ? `${prefix}${(displayValue / 1000000).toFixed(1)}M${suffix}`
      : format === "percent"
        ? `${prefix}${displayValue.toFixed(1)}${suffix}`
        : `${prefix}${Math.round(displayValue).toLocaleString()}${suffix}`

  return <span>{formatted}</span>
}

export function StatsBar() {
  return (
    <section className="-mt-8 relative z-10 mx-auto max-w-6xl px-4 lg:px-8">
      <div className="grid grid-cols-2 gap-4 rounded-2xl border border-border bg-card p-6 shadow-xl lg:grid-cols-4 lg:gap-8">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="text-center">
              <div className="mb-2 flex items-center justify-center">
                <div className={`rounded-full p-2 ${stat.color} bg-current/10`}>
                  <Icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold text-card-foreground lg:text-3xl">
                <AnimatedNumber value={stat.value} prefix={stat.prefix} suffix={stat.suffix} format={stat.format} />
              </div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
