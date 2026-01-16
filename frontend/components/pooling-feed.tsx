"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowRight, TrendingUp, Clock, Sparkles } from "lucide-react"

interface PoolingOpportunity {
  id: string
  origin: string
  destination: string
  savings: number
  savingsPercent: number
  shipmentCount: number
  expiresIn: number
  matchScore: number
}

const initialOpportunities: PoolingOpportunity[] = [
  {
    id: "1",
    origin: "Los Angeles, CA",
    destination: "Dallas, TX",
    savings: 847,
    savingsPercent: 28,
    shipmentCount: 3,
    expiresIn: 45,
    matchScore: 94,
  },
  {
    id: "2",
    origin: "Chicago, IL",
    destination: "Atlanta, GA",
    savings: 623,
    savingsPercent: 22,
    shipmentCount: 2,
    expiresIn: 120,
    matchScore: 87,
  },
  {
    id: "3",
    origin: "Seattle, WA",
    destination: "Denver, CO",
    savings: 512,
    savingsPercent: 19,
    shipmentCount: 4,
    expiresIn: 30,
    matchScore: 91,
  },
  {
    id: "4",
    origin: "Miami, FL",
    destination: "New York, NY",
    savings: 956,
    savingsPercent: 32,
    shipmentCount: 2,
    expiresIn: 90,
    matchScore: 96,
  },
]

export function PoolingFeed() {
  const [opportunities, setOpportunities] = useState(initialOpportunities)

  // Simulate countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setOpportunities((prev) =>
        prev.map((opp) => ({
          ...opp,
          expiresIn: Math.max(0, opp.expiresIn - 1),
        })),
      )
    }, 60000) // Update every minute

    return () => clearInterval(timer)
  }, [])

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-amber-500" />
          <CardTitle className="text-lg">Live Pooling Opportunities</CardTitle>
        </div>
        <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-600">
          {opportunities.length} Active
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        {opportunities.map((opp) => (
          <div
            key={opp.id}
            className="group rounded-lg border border-border bg-muted/30 p-4 transition-all hover:border-primary/30 hover:bg-muted/50"
          >
            {/* Route */}
            <div className="mb-3 flex items-center gap-2 text-sm">
              <span className="font-medium text-foreground">{opp.origin}</span>
              <ArrowRight className="h-3 w-3 text-muted-foreground" />
              <span className="font-medium text-foreground">{opp.destination}</span>
            </div>

            {/* Stats Row */}
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                {/* Savings */}
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                  <span className="font-bold text-emerald-600">${opp.savings}</span>
                  <Badge variant="outline" className="ml-1 border-emerald-500/30 text-emerald-600 text-xs">
                    {opp.savingsPercent}%
                  </Badge>
                </div>
              </div>

              {/* Match Score */}
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="text-xs text-muted-foreground">{opp.matchScore}% match</span>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>Expires in {formatTime(opp.expiresIn)}</span>
              </div>
              <Button size="sm" variant="ghost" className="h-7 text-xs text-primary hover:bg-primary/10">
                View Details
              </Button>
            </div>
          </div>
        ))}

        <Button variant="outline" className="w-full mt-2 bg-transparent">
          View All Opportunities
        </Button>
      </CardContent>
    </Card>
  )
}
