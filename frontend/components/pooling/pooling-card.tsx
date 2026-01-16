"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ArrowRight, Clock, Package, Truck } from "lucide-react"

interface PoolingCardProps {
  opportunity: {
    id: string
    matchScore: number
    shipmentsCount: number
    origin: { city: string; state: string }
    destination: { city: string; state: string }
    totalSavings: number
    savingsPercent: number
    individualCost: number
    pooledCost: number
    timeRemaining: number
    equipment: string
  }
  onViewDetails: () => void
}

export function PoolingCard({ opportunity, onViewDetails }: PoolingCardProps) {
  const [timeLeft, setTimeLeft] = useState(opportunity.timeRemaining)
  const [isExecuting, setIsExecuting] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1))
    }, 60000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-500"
    if (score >= 75) return "text-amber-500"
    return "text-red-500"
  }

  const handleExecute = () => {
    setIsExecuting(true)
    setTimeout(() => setIsExecuting(false), 2000)
  }

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Match Score Gauge */}
            <div className="relative w-14 h-14">
              <svg className="w-full h-full -rotate-90">
                <circle
                  cx="28"
                  cy="28"
                  r="24"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                  className="text-muted"
                />
                <circle
                  cx="28"
                  cy="28"
                  r="24"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                  strokeDasharray={`${(opportunity.matchScore / 100) * 151} 151`}
                  className={getScoreColor(opportunity.matchScore)}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`text-sm font-bold ${getScoreColor(opportunity.matchScore)}`}>
                  {opportunity.matchScore}
                </span>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                {Array.from({ length: opportunity.shipmentsCount }).map((_, i) => (
                  <Package key={i} className="h-4 w-4 text-primary" />
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-1">{opportunity.shipmentsCount} shipments</p>
            </div>
          </div>
          <Badge variant="outline" className="font-mono">
            {opportunity.equipment}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Route */}
        <div className="flex items-center gap-2 text-sm">
          <Badge variant="secondary">{opportunity.origin.state}</Badge>
          <span className="font-medium">{opportunity.origin.city}</span>
          <ArrowRight className="h-4 w-4 text-muted-foreground" />
          <Badge variant="secondary">{opportunity.destination.state}</Badge>
          <span className="font-medium">{opportunity.destination.city}</span>
        </div>

        {/* Savings */}
        <div className="bg-emerald-50 dark:bg-emerald-950/30 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Total Savings</span>
            <Badge className="bg-emerald-500 text-white">{opportunity.savingsPercent}% OFF</Badge>
          </div>
          <p className="text-3xl font-bold text-emerald-600">${opportunity.totalSavings.toLocaleString()}</p>
        </div>

        {/* Cost Comparison */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Individual</span>
            <span className="line-through text-muted-foreground">${opportunity.individualCost.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Pooled</span>
            <span className="font-semibold text-primary">${opportunity.pooledCost.toLocaleString()}</span>
          </div>
          <Progress value={(opportunity.pooledCost / opportunity.individualCost) * 100} className="h-2" />
        </div>

        {/* Time Remaining */}
        <div className="flex items-center gap-2 text-sm">
          <Clock className="h-4 w-4 text-amber-500" />
          <span className="text-muted-foreground">Time remaining:</span>
          <span className="font-semibold text-amber-500">{formatTime(timeLeft)}</span>
        </div>
      </CardContent>

      <CardFooter className="gap-2">
        <Button className="flex-1" onClick={handleExecute} disabled={isExecuting}>
          {isExecuting ? (
            <>
              <Truck className="h-4 w-4 mr-2 animate-pulse" />
              Processing...
            </>
          ) : (
            "Execute Pool"
          )}
        </Button>
        <Button variant="outline" onClick={onViewDetails}>
          View Details
        </Button>
      </CardFooter>
    </Card>
  )
}
