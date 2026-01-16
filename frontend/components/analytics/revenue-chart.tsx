"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, ComposedChart } from "recharts"
import { useState } from "react"

const monthlyData = [
  { month: "Jul", revenue: 185000, prevYear: 162000, forecast: null },
  { month: "Aug", revenue: 198000, prevYear: 175000, forecast: null },
  { month: "Sep", revenue: 212000, prevYear: 189000, forecast: null },
  { month: "Oct", revenue: 228000, prevYear: 198000, forecast: null },
  { month: "Nov", revenue: 245000, prevYear: 215000, forecast: null },
  { month: "Dec", revenue: 268000, prevYear: 232000, forecast: null },
  { month: "Jan", revenue: 284000, prevYear: 248000, forecast: 284000 },
  { month: "Feb", revenue: null, prevYear: 258000, forecast: 298000 },
  { month: "Mar", revenue: null, prevYear: 272000, forecast: 312000 },
]

export function RevenueChart() {
  const [period, setPeriod] = useState("6m")

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Revenue Over Time</CardTitle>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-24">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="3m">3 months</SelectItem>
            <SelectItem value="6m">6 months</SelectItem>
            <SelectItem value="1y">1 year</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="month" className="text-xs" />
              <YAxis className="text-xs" tickFormatter={(value) => `$${value / 1000}k`} />
              <Tooltip
                formatter={(value: number | null, name: string) => {
                  if (value === null) return ["-", name]
                  const label = name === "revenue" ? "Current" : name === "prevYear" ? "Previous Year" : "Forecast"
                  return [`$${value.toLocaleString()}`, label]
                }}
                contentStyle={{
                  backgroundColor: "hsl(var(--background))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Area
                type="monotone"
                dataKey="prevYear"
                stroke="hsl(var(--muted-foreground))"
                fill="hsl(var(--muted)/0.3)"
                strokeWidth={1}
                strokeDasharray="5 5"
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="hsl(var(--primary))"
                fill="hsl(var(--primary)/0.2)"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                strokeDasharray="8 4"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-primary" />
            <span>Current</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-muted-foreground" />
            <span>Previous Year</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 border-t-2 border-dashed border-primary" />
            <span>Forecast</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
