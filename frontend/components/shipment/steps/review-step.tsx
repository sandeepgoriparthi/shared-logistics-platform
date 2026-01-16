"use client"

import { useEffect, useState } from "react"
import { useFormContext } from "react-hook-form"
import {
  MapPin,
  Calendar,
  Package,
  Truck,
  DollarSign,
  ArrowLeft,
  CheckCircle,
  TrendingDown,
  Loader2,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { format } from "date-fns"
import type { ShipmentFormData } from "../shipment-form"

interface ReviewStepProps {
  onBack: () => void
}

export function ReviewStep({ onBack }: ReviewStepProps) {
  const form = useFormContext<ShipmentFormData>()
  const data = form.getValues()

  const [isCalculating, setIsCalculating] = useState(true)
  const [quote, setQuote] = useState({
    baseRate: 0,
    fuelSurcharge: 0,
    poolingDiscount: 0,
    finalPrice: 0,
    marketRate: 0,
    poolingProbability: 0,
    potentialSavings: 0,
  })

  // Simulate quote calculation
  useEffect(() => {
    const timer = setTimeout(() => {
      const baseRate = 850 + Math.random() * 400
      const fuelSurcharge = baseRate * 0.18
      const poolingDiscount = baseRate * 0.23
      const finalPrice = baseRate + fuelSurcharge - poolingDiscount
      const marketRate = baseRate * 1.35

      setQuote({
        baseRate: Math.round(baseRate),
        fuelSurcharge: Math.round(fuelSurcharge),
        poolingDiscount: Math.round(poolingDiscount),
        finalPrice: Math.round(finalPrice),
        marketRate: Math.round(marketRate),
        poolingProbability: 78,
        potentialSavings: Math.round(poolingDiscount * 1.5),
      })
      setIsCalculating(false)
    }, 2000)

    return () => clearTimeout(timer)
  }, [])

  const getEquipmentLabel = (value: string) => {
    const labels: Record<string, string> = {
      "dry-van": "Dry Van",
      reefer: "Refrigerated",
      flatbed: "Flatbed",
      "step-deck": "Step Deck",
      conestoga: "Conestoga",
    }
    return labels[value] || value
  }

  const getCommodityLabel = (value: string) => {
    const labels: Record<string, string> = {
      general: "General Merchandise",
      food: "Food & Beverage",
      electronics: "Electronics",
      machinery: "Machinery",
      automotive: "Automotive Parts",
      chemicals: "Chemicals",
      construction: "Construction Materials",
    }
    return labels[value] || value
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <MapPin className="w-5 h-5 text-primary" />
              Origin
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="font-medium">{data.originAddress}</p>
            <p className="text-muted-foreground">
              {data.originCity}, {data.originState} {data.originZip}
            </p>
            <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2">
              <Calendar className="w-4 h-4" />
              {data.pickupDate ? format(data.pickupDate, "PPP") : "Not set"}
              <span>•</span>
              {data.pickupTimeFrom} - {data.pickupTimeTo}
            </div>
            <p className="text-sm">
              <span className="text-muted-foreground">Contact:</span> {data.originContact} • {data.originPhone}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <MapPin className="w-5 h-5 text-secondary" />
              Destination
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="font-medium">{data.destAddress}</p>
            <p className="text-muted-foreground">
              {data.destCity}, {data.destState} {data.destZip}
            </p>
            <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2">
              <Calendar className="w-4 h-4" />
              {data.deliveryDate ? format(data.deliveryDate, "PPP") : "Not set"}
              <span>•</span>
              {data.deliveryTimeFrom} - {data.deliveryTimeTo}
            </div>
            <div className="flex gap-2 pt-2">
              {data.appointmentRequired && <Badge variant="secondary">Appointment</Badge>}
              {data.liftgateRequired && <Badge variant="secondary">Liftgate</Badge>}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Package className="w-5 h-5 text-accent" />
            Freight Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Weight</p>
              <p className="font-semibold">{data.weight.toLocaleString()} lbs</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Dimensions</p>
              <p className="font-semibold">
                {data.length}" x {data.width}" x {data.height}"
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Linear Feet</p>
              <p className="font-semibold">{data.linearFeet} ft</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Pallets</p>
              <p className="font-semibold">{data.palletCount}</p>
            </div>
          </div>
          <Separator className="my-4" />
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Truck className="w-3 h-3" />
              {getEquipmentLabel(data.equipmentType)}
            </Badge>
            <Badge variant="outline">{getCommodityLabel(data.commodityType)}</Badge>
            {data.stackable && <Badge variant="secondary">Stackable</Badge>}
            {data.hazmat && <Badge variant="destructive">Hazmat</Badge>}
          </div>
        </CardContent>
      </Card>

      {/* Quote Card */}
      <Card className="border-2 border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <DollarSign className="w-5 h-5 text-primary" />
            Your Quote
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isCalculating ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
              <p className="text-muted-foreground">Calculating best rates...</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Price Breakdown */}
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Base Rate</span>
                    <span className="font-medium">${quote.baseRate.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fuel Surcharge (18%)</span>
                    <span className="font-medium">+${quote.fuelSurcharge.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-secondary">
                    <span>Pooling Discount (23%)</span>
                    <span className="font-medium">-${quote.poolingDiscount.toLocaleString()}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between text-lg">
                    <span className="font-semibold">Final Price</span>
                    <span className="font-bold text-primary">${quote.finalPrice.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Market Rate</span>
                    <span className="line-through">${quote.marketRate.toLocaleString()}</span>
                  </div>
                </div>

                {/* Pooling Probability */}
                <div className="flex flex-col items-center justify-center p-4 bg-muted rounded-lg">
                  <div className="relative w-32 h-32">
                    <svg className="w-32 h-32 -rotate-90" viewBox="0 0 120 120">
                      <circle
                        cx="60"
                        cy="60"
                        r="50"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="10"
                        className="text-muted-foreground/20"
                      />
                      <circle
                        cx="60"
                        cy="60"
                        r="50"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="10"
                        strokeDasharray={`${quote.poolingProbability * 3.14} 314`}
                        className="text-secondary transition-all duration-1000"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-3xl font-bold">{quote.poolingProbability}%</span>
                      <span className="text-xs text-muted-foreground">Pooling Match</span>
                    </div>
                  </div>
                  <p className="text-center text-sm text-muted-foreground mt-2">
                    High probability of finding a pooling partner
                  </p>
                </div>
              </div>

              {/* Savings Banner */}
              <div className="flex items-center justify-between p-4 bg-secondary/10 rounded-lg border border-secondary/20">
                <div className="flex items-center gap-3">
                  <TrendingDown className="w-6 h-6 text-secondary" />
                  <div>
                    <p className="font-medium text-secondary">Potential Additional Savings</p>
                    <p className="text-sm text-muted-foreground">If pooled with another shipment</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-secondary">+${quote.potentialSavings.toLocaleString()}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button type="button" variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button type="submit" className="px-8 bg-secondary hover:bg-secondary/90" disabled={isCalculating}>
          <CheckCircle className="w-4 h-4 mr-2" />
          Book Shipment
        </Button>
      </div>
    </div>
  )
}
