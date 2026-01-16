"use client"

import { useState } from "react"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { ArrowRight, MapPin, Clock, Package, Truck, DollarSign, Navigation } from "lucide-react"

const mockLoads = [
  {
    id: "LOAD-001",
    origin: { city: "Los Angeles", state: "CA" },
    destination: { city: "Dallas", state: "TX" },
    distance: 1435,
    hours: 22,
    rate: 3200,
    ratePerMile: 2.23,
    pickupWindow: "Jan 16, 8AM - 12PM",
    deliveryWindow: "Jan 17, 2PM - 6PM",
    weight: 18500,
    ft: 24,
    pallets: 18,
    matchScore: 95,
    equipment: "Dry Van",
    deadhead: 12,
  },
  {
    id: "LOAD-002",
    origin: { city: "Phoenix", state: "AZ" },
    destination: { city: "Denver", state: "CO" },
    distance: 602,
    hours: 9,
    rate: 1450,
    ratePerMile: 2.41,
    pickupWindow: "Jan 16, 2PM - 5PM",
    deliveryWindow: "Jan 17, 8AM - 12PM",
    weight: 12000,
    ft: 16,
    pallets: 12,
    matchScore: 88,
    equipment: "Reefer",
    deadhead: 45,
  },
  {
    id: "LOAD-003",
    origin: { city: "Seattle", state: "WA" },
    destination: { city: "San Francisco", state: "CA" },
    distance: 808,
    hours: 12,
    rate: 1920,
    ratePerMile: 2.38,
    pickupWindow: "Jan 17, 6AM - 10AM",
    deliveryWindow: "Jan 18, 10AM - 2PM",
    weight: 22000,
    ft: 32,
    pallets: 24,
    matchScore: 82,
    equipment: "Dry Van",
    deadhead: 28,
  },
  {
    id: "LOAD-004",
    origin: { city: "Chicago", state: "IL" },
    destination: { city: "Atlanta", state: "GA" },
    distance: 716,
    hours: 11,
    rate: 1680,
    ratePerMile: 2.35,
    pickupWindow: "Jan 16, 4PM - 8PM",
    deliveryWindow: "Jan 17, 6PM - 10PM",
    weight: 15800,
    ft: 20,
    pallets: 15,
    matchScore: 91,
    equipment: "Dry Van",
    deadhead: 8,
  },
]

export function AvailableLoads() {
  const [equipment, setEquipment] = useState("all")
  const [minRate, setMinRate] = useState([1.5])
  const [maxDeadhead, setMaxDeadhead] = useState([100])
  const [acceptingLoad, setAcceptingLoad] = useState<string | null>(null)

  const filteredLoads = mockLoads.filter((load) => {
    if (equipment !== "all" && load.equipment !== equipment) return false
    if (load.ratePerMile < minRate[0]) return false
    if (load.deadhead > maxDeadhead[0]) return false
    return true
  })

  const handleAccept = (loadId: string) => {
    setAcceptingLoad(loadId)
    setTimeout(() => setAcceptingLoad(null), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="space-y-2">
              <Label>Equipment Type</Label>
              <Select value={equipment} onValueChange={setEquipment}>
                <SelectTrigger>
                  <SelectValue placeholder="All Equipment" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Equipment</SelectItem>
                  <SelectItem value="Dry Van">Dry Van</SelectItem>
                  <SelectItem value="Reefer">Reefer</SelectItem>
                  <SelectItem value="Flatbed">Flatbed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Min Rate/Mile: ${minRate[0].toFixed(2)}</Label>
              <Slider value={minRate} onValueChange={setMinRate} min={1} max={4} step={0.1} className="mt-2" />
            </div>

            <div className="space-y-2">
              <Label>Max Deadhead: {maxDeadhead[0]} mi</Label>
              <Slider value={maxDeadhead} onValueChange={setMaxDeadhead} min={0} max={200} step={10} className="mt-2" />
            </div>

            <div className="space-y-2">
              <Label>Search</Label>
              <Input placeholder="City, State, Load ID..." />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loads Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {filteredLoads.map((load) => (
          <Card key={load.id} className="overflow-hidden hover:shadow-lg transition-shadow">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="font-mono">
                  {load.id}
                </Badge>
                <div className="flex items-center gap-2">
                  <Badge className="bg-primary/10 text-primary">{load.matchScore}% Match</Badge>
                  <Badge variant="secondary">{load.equipment}</Badge>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Route */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <MapPin className="h-4 w-4 text-emerald-500" />
                  <span className="font-medium">
                    {load.origin.city}, {load.origin.state}
                  </span>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <div className="flex items-center gap-1">
                  <MapPin className="h-4 w-4 text-red-500" />
                  <span className="font-medium">
                    {load.destination.city}, {load.destination.state}
                  </span>
                </div>
              </div>

              {/* Distance & Time */}
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Truck className="h-4 w-4" />
                  <span>{load.distance} mi</span>
                </div>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>{load.hours} hrs</span>
                </div>
                <div className="flex items-center gap-1 text-amber-600">
                  <Navigation className="h-4 w-4" />
                  <span>{load.deadhead} mi deadhead</span>
                </div>
              </div>

              {/* Rate Highlight */}
              <div className="bg-emerald-50 dark:bg-emerald-950/30 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Rate</p>
                    <p className="text-2xl font-bold text-emerald-600">${load.rate.toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Per Mile</p>
                    <p className="text-xl font-bold text-emerald-600">${load.ratePerMile.toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {/* Windows */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Pickup</p>
                  <p className="font-medium">{load.pickupWindow}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Delivery</p>
                  <p className="font-medium">{load.deliveryWindow}</p>
                </div>
              </div>

              {/* Freight Details */}
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Package className="h-4 w-4" />
                  <span>{load.weight.toLocaleString()} lbs</span>
                </div>
                <span className="text-muted-foreground">{load.ft} ft</span>
                <span className="text-muted-foreground">{load.pallets} pallets</span>
              </div>
            </CardContent>

            <CardFooter>
              <Button className="w-full" onClick={() => handleAccept(load.id)} disabled={acceptingLoad === load.id}>
                {acceptingLoad === load.id ? (
                  <>
                    <DollarSign className="h-4 w-4 mr-2 animate-spin" />
                    Accepting...
                  </>
                ) : (
                  "Accept Load"
                )}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
