"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Truck, DollarSign, Package } from "lucide-react"

export function CarrierHeader() {
  const [performanceScore, setPerformanceScore] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => setPerformanceScore(94), 500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="space-y-6">
      {/* Carrier Info */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Swift Logistics LLC</h1>
          <div className="flex items-center gap-3 mt-2">
            <Badge variant="outline" className="font-mono">
              MC# 123456
            </Badge>
            <Badge variant="outline" className="font-mono">
              DOT# 7891011
            </Badge>
            <Badge className="bg-emerald-500 text-white">Verified Carrier</Badge>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Performance Score */}
        <Card className="bg-gradient-to-br from-primary/10 to-primary/5">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Performance Score</p>
                <p className="text-3xl font-bold text-primary">{performanceScore}%</p>
              </div>
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
                    strokeDasharray={`${(performanceScore / 100) * 176} 176`}
                    className="text-primary transition-all duration-1000"
                  />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Earnings This Month */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 dark:bg-emerald-900 rounded-lg">
                <DollarSign className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">This Month</p>
                <p className="text-2xl font-bold">$24,580</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Loads */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 dark:bg-amber-900 rounded-lg">
                <Truck className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Active Loads</p>
                <p className="text-2xl font-bold">3</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Available Capacity */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <Package className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Capacity</p>
                <p className="text-2xl font-bold">28 ft</p>
                <p className="text-xs text-muted-foreground">of 53 ft available</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
