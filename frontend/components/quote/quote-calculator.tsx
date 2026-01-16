"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { MapPin, Scale, Truck, Calculator } from "lucide-react"
import { QuoteResult } from "./quote-result"

export function QuoteCalculator() {
  const [originZip, setOriginZip] = useState("")
  const [destZip, setDestZip] = useState("")
  const [weight, setWeight] = useState("")
  const [linearFeet, setLinearFeet] = useState([20])
  const [equipment, setEquipment] = useState("dry-van")
  const [isCalculating, setIsCalculating] = useState(false)
  const [quote, setQuote] = useState<{
    baseRate: number
    fuelSurcharge: number
    poolingDiscount: number
    total: number
    marketAverage: number
    poolingProbability: number
    additionalSavings: number
  } | null>(null)

  const handleCalculate = () => {
    setIsCalculating(true)
    // Simulate API call
    setTimeout(() => {
      const baseRate = 1800 + Math.random() * 800
      const fuelSurcharge = baseRate * 0.18
      const poolingDiscount = baseRate * 0.22
      const total = baseRate + fuelSurcharge - poolingDiscount
      const marketAverage = total * 1.35
      const poolingProbability = 65 + Math.random() * 25
      const additionalSavings = baseRate * 0.12 + Math.random() * 100

      setQuote({
        baseRate: Math.round(baseRate),
        fuelSurcharge: Math.round(fuelSurcharge),
        poolingDiscount: Math.round(poolingDiscount),
        total: Math.round(total),
        marketAverage: Math.round(marketAverage),
        poolingProbability: Math.round(poolingProbability),
        additionalSavings: Math.round(additionalSavings),
      })
      setIsCalculating(false)
    }, 1500)
  }

  const isFormValid = originZip.length >= 5 && destZip.length >= 5 && weight

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Form */}
      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Origin ZIP */}
          <div className="space-y-2">
            <Label htmlFor="originZip" className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-emerald-500" />
              Origin ZIP Code
            </Label>
            <Input
              id="originZip"
              placeholder="90210"
              value={originZip}
              onChange={(e) => setOriginZip(e.target.value)}
              maxLength={5}
            />
          </div>

          {/* Destination ZIP */}
          <div className="space-y-2">
            <Label htmlFor="destZip" className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-red-500" />
              Destination ZIP Code
            </Label>
            <Input
              id="destZip"
              placeholder="75201"
              value={destZip}
              onChange={(e) => setDestZip(e.target.value)}
              maxLength={5}
            />
          </div>

          {/* Weight */}
          <div className="space-y-2">
            <Label htmlFor="weight" className="flex items-center gap-2">
              <Scale className="h-4 w-4" />
              Weight (lbs)
            </Label>
            <Input
              id="weight"
              type="number"
              placeholder="10000"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
            />
          </div>

          {/* Linear Feet */}
          <div className="space-y-4">
            <Label className="flex items-center justify-between">
              <span>Linear Feet</span>
              <span className="font-bold text-primary">{linearFeet[0]} ft</span>
            </Label>
            <Slider value={linearFeet} onValueChange={setLinearFeet} min={1} max={53} step={1} />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1 ft</span>
              <span>53 ft</span>
            </div>
          </div>

          {/* Equipment Type */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Truck className="h-4 w-4" />
              Equipment Type
            </Label>
            <Select value={equipment} onValueChange={setEquipment}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="dry-van">Dry Van</SelectItem>
                <SelectItem value="reefer">Reefer</SelectItem>
                <SelectItem value="flatbed">Flatbed</SelectItem>
                <SelectItem value="step-deck">Step Deck</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Submit Button */}
          <Button className="w-full" size="lg" onClick={handleCalculate} disabled={!isFormValid || isCalculating}>
            {isCalculating ? (
              <>
                <Calculator className="h-5 w-5 mr-2 animate-spin" />
                Calculating...
              </>
            ) : (
              <>
                <Calculator className="h-5 w-5 mr-2" />
                Get Instant Quote
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      <QuoteResult quote={quote} isCalculating={isCalculating} />
    </div>
  )
}
