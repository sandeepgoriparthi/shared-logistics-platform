"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts"

const lanesData = [
  { lane: "LA → Dallas", volume: 342, profit: 92 },
  { lane: "Chicago → Atlanta", volume: 298, profit: 88 },
  { lane: "Seattle → Phoenix", volume: 256, profit: 85 },
  { lane: "NY → Miami", volume: 234, profit: 91 },
  { lane: "Denver → Vegas", volume: 198, profit: 78 },
  { lane: "Houston → Orlando", volume: 176, profit: 82 },
  { lane: "Boston → DC", volume: 165, profit: 86 },
  { lane: "Detroit → Nashville", volume: 142, profit: 75 },
  { lane: "Portland → SLC", volume: 128, profit: 80 },
  { lane: "Memphis → KC", volume: 112, profit: 72 },
]

const getBarColor = (profit: number) => {
  if (profit >= 90) return "hsl(142, 76%, 36%)"
  if (profit >= 80) return "hsl(var(--primary))"
  return "hsl(45, 93%, 47%)"
}

export function TopLanesChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Lanes by Volume</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={lanesData} layout="vertical" margin={{ left: 80 }}>
              <XAxis type="number" className="text-xs" />
              <YAxis type="category" dataKey="lane" className="text-xs" width={80} />
              <Tooltip
                formatter={(value: number, name: string) => [value, name === "volume" ? "Shipments" : name]}
                contentStyle={{
                  backgroundColor: "hsl(var(--background))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Bar dataKey="volume" radius={[0, 4, 4, 0]}>
                {lanesData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.profit)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: "hsl(142, 76%, 36%)" }} />
            <span>High Profit (90%+)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-primary" />
            <span>Medium (80-90%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: "hsl(45, 93%, 47%)" }} />
            <span>Lower (&lt;80%)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
