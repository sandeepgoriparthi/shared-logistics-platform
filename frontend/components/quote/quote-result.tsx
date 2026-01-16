"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, TrendingDown, Bookmark, ArrowRight, Sparkles } from "lucide-react"

interface QuoteResultProps {
  quote: {
    baseRate: number
    fuelSurcharge: number
    poolingDiscount: number
    total: number
    marketAverage: number
    poolingProbability: number
    additionalSavings: number
  } | null
  isCalculating: boolean
}

export function QuoteResult({ quote, isCalculating }: QuoteResultProps) {
  const [animatedValues, setAnimatedValues] = useState({
    baseRate: 0,
    fuelSurcharge: 0,
    poolingDiscount: 0,
    total: 0,
    probability: 0,
  })

  useEffect(() => {
    if (!quote) return

    const duration = 800
    const steps = 40
    const increment = duration / steps
    let step = 0

    const timer = setInterval(() => {
      step++
      const progress = step / steps
      setAnimatedValues({
        baseRate: Math.round(quote.baseRate * progress),
        fuelSurcharge: Math.round(quote.fuelSurcharge * progress),
        poolingDiscount: Math.round(quote.poolingDiscount * progress),
        total: Math.round(quote.total * progress),
        probability: Math.round(quote.poolingProbability * progress),
      })
      if (step >= steps) clearInterval(timer)
    }, increment)

    return () => clearInterval(timer)
  }, [quote])

  if (!quote && !isCalculating) {
    return (
      <Card className="flex items-center justify-center min-h-[400px] bg-muted/30">
        <CardContent className="text-center">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Ready to Calculate</h3>
          <p className="text-muted-foreground text-sm">Fill in the form to get your instant quote</p>
        </CardContent>
      </Card>
    )
  }

  if (isCalculating) {
    return (
      <Card className="flex items-center justify-center min-h-[400px]">
        <CardContent className="text-center">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <div className="w-12 h-12 rounded-full border-4 border-primary border-t-transparent animate-spin" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Calculating Your Quote</h3>
          <p className="text-muted-foreground text-sm">Finding the best rates for you...</p>
        </CardContent>
      </Card>
    )
  }

  if (!quote) return null

  const savingsPercent = Math.round(((quote.marketAverage - quote.total) / quote.marketAverage) * 100)

  return (
    <Card className="overflow-hidden">
      <CardContent className="pt-6 space-y-6">
        {/* Price Breakdown */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">Base Rate</span>
            <span className="font-medium">${animatedValues.baseRate.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground">Fuel Surcharge</span>
            <span className="font-medium">${animatedValues.fuelSurcharge.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center text-emerald-600">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Est. Pooling Discount
            </span>
            <span className="font-medium">-${animatedValues.poolingDiscount.toLocaleString()}</span>
          </div>
          <Separator />
          <div className="flex justify-between items-center">
            <span className="text-lg font-semibold">TOTAL</span>
            <span className="text-3xl font-bold text-primary">${animatedValues.total.toLocaleString()}</span>
          </div>
        </div>

        {/* Comparison Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Our Price</span>
            <span className="text-muted-foreground">Market Average</span>
          </div>
          <div className="relative h-8 bg-muted rounded-full overflow-hidden">
            <div
              className="absolute inset-y-0 left-0 bg-primary rounded-full flex items-center justify-end pr-3"
              style={{ width: `${(quote.total / quote.marketAverage) * 100}%` }}
            >
              <span className="text-xs font-medium text-primary-foreground">${quote.total.toLocaleString()}</span>
            </div>
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              <span className="text-xs font-medium text-muted-foreground">${quote.marketAverage.toLocaleString()}</span>
            </div>
          </div>
          <div className="flex justify-center">
            <Badge className="bg-emerald-500 text-white">
              <TrendingDown className="h-3 w-3 mr-1" />
              {savingsPercent}% Below Market
            </Badge>
          </div>
        </div>

        {/* Pooling Indicator */}
        <div className="bg-primary/5 rounded-lg p-4">
          <div className="flex items-center gap-4">
            <div className="relative w-16 h-16">
              <svg className="w-full h-full -rotate-90">
                <circle
                  cx="32"
                  cy="32"
                  r="28"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                  className="text-muted"
                />
                <circle
                  cx="32"
                  cy="32"
                  r="28"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                  strokeDasharray={`${(animatedValues.probability / 100) * 176} 176`}
                  className="text-primary transition-all duration-500"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-bold">{animatedValues.probability}%</span>
              </div>
            </div>
            <div>
              <p className="font-semibold text-primary">High Pooling Probability</p>
              <p className="text-sm text-muted-foreground">
                Could save additional <span className="text-emerald-600 font-medium">${quote.additionalSavings}</span>
              </p>
            </div>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="space-y-3">
          <Button className="w-full" size="lg">
            Book Now
            <ArrowRight className="h-5 w-5 ml-2" />
          </Button>
          <div className="grid grid-cols-2 gap-3">
            <Button variant="outline">Get Detailed Quote</Button>
            <Button variant="outline">
              <Bookmark className="h-4 w-4 mr-2" />
              Save Quote
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
