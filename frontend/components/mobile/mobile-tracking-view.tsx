"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area"
import {
  ArrowLeft,
  Share2,
  Phone,
  Star,
  Truck,
  Package,
  Scale,
  CheckCircle2,
  Circle,
  AlertCircle,
  Navigation,
} from "lucide-react"
import Link from "next/link"

interface MobileTrackingViewProps {
  shipmentId: string
}

const mockData = {
  id: "SHP-2024-001234",
  status: "in_transit",
  eta: { hours: 4, minutes: 23 },
  progress: 65,
  currentCity: "Palm Springs",
  currentState: "CA",
  driver: { name: "Mike Johnson", phone: "+1 (555) 123-4567" },
  carrier: { name: "Swift Logistics", rating: 4.8 },
  freight: { weight: 18500, dimensions: "48x40x48" },
  timeline: [
    { event: "In Transit - Palm Springs, CA", time: "2:45 PM", completed: true, current: true },
    { event: "Departed Los Angeles, CA", time: "8:30 AM", completed: true, current: false },
    { event: "Picked Up", time: "8:15 AM", completed: true, current: false },
    { event: "Driver Assigned", time: "7:45 AM", completed: true, current: false },
    { event: "Booking Confirmed", time: "Yesterday 4:30 PM", completed: true, current: false },
  ],
}

export function MobileTrackingView({ shipmentId }: MobileTrackingViewProps) {
  const [countdown, setCountdown] = useState(mockData.eta)

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev.minutes > 0) return { ...prev, minutes: prev.minutes - 1 }
        if (prev.hours > 0) return { hours: prev.hours - 1, minutes: 59 }
        return prev
      })
    }, 60000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost" size="icon" className="h-9 w-9">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <p className="font-semibold text-sm truncate max-w-[160px]">{mockData.id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-amber-500 text-white">In Transit</Badge>
            <Button variant="ghost" size="icon" className="h-9 w-9">
              <Share2 className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Hero - ETA */}
      <div className="bg-gradient-to-b from-primary/10 to-background px-4 py-6 text-center">
        <p className="text-sm text-muted-foreground mb-2">Arriving in</p>
        <h1 className="text-5xl font-bold text-primary mb-4">
          {countdown.hours}h {countdown.minutes}m
        </h1>
        {/* Progress Ring */}
        <div className="relative w-24 h-24 mx-auto mb-4">
          <svg className="w-full h-full -rotate-90">
            <circle cx="48" cy="48" r="44" stroke="currentColor" strokeWidth="6" fill="none" className="text-muted" />
            <circle
              cx="48"
              cy="48"
              r="44"
              stroke="currentColor"
              strokeWidth="6"
              fill="none"
              strokeDasharray={`${(mockData.progress / 100) * 276} 276`}
              className="text-primary"
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-bold">{mockData.progress}%</span>
          </div>
        </div>
        <p className="text-lg font-medium">
          {mockData.currentCity}, {mockData.currentState}
        </p>
      </div>

      {/* Map Section */}
      <div className="relative h-[40vh] bg-slate-100 dark:bg-slate-800">
        <img
          src="/us-map-route-from-los-angeles-to-phoenix-with-truc.jpg"
          alt="Tracking Map"
          className="w-full h-full object-cover"
        />
        {/* Truck marker */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/30 rounded-full animate-ping" />
            <div className="relative bg-primary text-primary-foreground p-3 rounded-full shadow-lg">
              <Truck className="h-6 w-6" />
            </div>
          </div>
        </div>
        {/* Recenter button */}
        <Button variant="secondary" size="icon" className="absolute bottom-4 right-4 h-10 w-10 rounded-full shadow-lg">
          <Navigation className="h-5 w-5" />
        </Button>
      </div>

      {/* Quick Info Cards - Horizontal Scroll */}
      <div className="px-4 -mt-6 relative z-10">
        <ScrollArea className="w-full whitespace-nowrap">
          <div className="flex gap-3 pb-4">
            {/* Driver Card */}
            <Card className="min-w-[200px] bg-background/95 backdrop-blur">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Truck className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{mockData.driver.name}</p>
                    <a href={`tel:${mockData.driver.phone}`} className="text-xs text-primary flex items-center gap-1">
                      <Phone className="h-3 w-3" />
                      Tap to call
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Carrier Card */}
            <Card className="min-w-[180px] bg-background/95 backdrop-blur">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900 flex items-center justify-center">
                    <Star className="h-5 w-5 text-amber-500" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{mockData.carrier.name}</p>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                      {mockData.carrier.rating} rating
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Freight Card */}
            <Card className="min-w-[180px] bg-background/95 backdrop-blur">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                    <Package className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm flex items-center gap-1">
                      <Scale className="h-3 w-3" />
                      {mockData.freight.weight.toLocaleString()} lbs
                    </p>
                    <p className="text-xs text-muted-foreground">{mockData.freight.dimensions} in</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </div>

      {/* Timeline */}
      <div className="flex-1 px-4 pb-24">
        <h2 className="font-semibold mb-4">Tracking Timeline</h2>
        <div className="space-y-1">
          {mockData.timeline.map((item, i) => (
            <div key={i} className="flex gap-3 pb-4">
              <div className="flex flex-col items-center">
                {item.current ? (
                  <div className="relative">
                    <div className="absolute inset-0 bg-primary/30 rounded-full animate-ping" />
                    <CheckCircle2 className="h-5 w-5 text-primary relative" />
                  </div>
                ) : item.completed ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground" />
                )}
                {i < mockData.timeline.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`font-medium text-sm ${item.current ? "text-primary" : ""}`}>{item.event}</p>
                <p className="text-xs text-muted-foreground">{item.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fixed Bottom Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t px-4 py-3 safe-area-pb">
        <div className="flex gap-3">
          <Button className="flex-1" asChild>
            <a href={`tel:${mockData.driver.phone}`}>
              <Phone className="h-4 w-4 mr-2" />
              Contact Driver
            </a>
          </Button>
          <Button variant="outline" className="flex-1 bg-transparent">
            <AlertCircle className="h-4 w-4 mr-2" />
            Report Issue
          </Button>
        </div>
      </div>
    </div>
  )
}
