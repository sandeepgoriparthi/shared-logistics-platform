"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
  Truck,
  MapPin,
  Star,
  Thermometer,
  Clock,
  CheckCircle2,
  Circle,
  CloudSun,
  Car,
  Share2,
  Upload,
  FileText,
} from "lucide-react"

interface TrackingViewProps {
  shipmentId: string
}

const mockShipment = {
  id: "SHP-2024-001234",
  status: "in_transit",
  origin: { city: "Los Angeles", state: "CA", lat: 34.0522, lng: -118.2437 },
  destination: { city: "Phoenix", state: "AZ", lat: 33.4484, lng: -112.074 },
  currentLocation: { city: "Palm Springs", state: "CA", lat: 33.8303, lng: -116.5453 },
  eta: new Date(Date.now() + 4 * 60 * 60 * 1000 + 23 * 60 * 1000),
  progress: 65,
  driver: { name: "Mike Johnson", phone: "+1 (555) 123-4567", truckNumber: "TRK-4521" },
  carrier: { name: "Swift Logistics", rating: 4.8 },
  temperature: 34,
  timeline: [
    { event: "Shipment Delivered", time: null, location: "Phoenix, AZ", completed: false },
    { event: "In Transit", time: "2:45 PM", location: "Palm Springs, CA", completed: true },
    { event: "Departed Origin", time: "8:30 AM", location: "Los Angeles, CA", completed: true },
    { event: "Picked Up", time: "8:15 AM", location: "Los Angeles, CA", completed: true },
    { event: "Booking Confirmed", time: "Yesterday", location: "System", completed: true },
  ],
}

export function TrackingView({ shipmentId }: TrackingViewProps) {
  const [showWeather, setShowWeather] = useState(false)
  const [showTraffic, setShowTraffic] = useState(false)
  const [countdown, setCountdown] = useState({ hours: 4, minutes: 23, seconds: 0 })

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev.seconds > 0) return { ...prev, seconds: prev.seconds - 1 }
        if (prev.minutes > 0) return { ...prev, minutes: prev.minutes - 1, seconds: 59 }
        if (prev.hours > 0) return { hours: prev.hours - 1, minutes: 59, seconds: 59 }
        return prev
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const statusColors: Record<string, string> = {
    booked: "bg-slate-500",
    picked_up: "bg-blue-500",
    in_transit: "bg-amber-500",
    delivered: "bg-emerald-500",
  }

  const steps = [
    { label: "Booked", status: "completed" },
    { label: "Picked Up", status: "completed" },
    { label: "In Transit", status: "current" },
    { label: "Delivered", status: "pending" },
  ]

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-4rem)]">
      {/* Left Panel */}
      <div className="w-full lg:w-[40%] p-6 overflow-y-auto border-r border-border">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{mockShipment.id}</h1>
              <Badge className={`${statusColors[mockShipment.status]} text-white`}>In Transit</Badge>
            </div>
            <p className="text-muted-foreground mt-1">
              {mockShipment.origin.city}, {mockShipment.origin.state} → {mockShipment.destination.city},{" "}
              {mockShipment.destination.state}
            </p>
          </div>
          <Button variant="outline" size="icon">
            <Share2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Progress Stepper */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex justify-between mb-2">
              {steps.map((step, i) => (
                <div key={step.label} className="flex flex-col items-center flex-1">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 ${
                      step.status === "completed"
                        ? "bg-emerald-500 text-white"
                        : step.status === "current"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {step.status === "completed" ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <span className="text-sm font-medium">{i + 1}</span>
                    )}
                  </div>
                  <span className="text-xs text-center">{step.label}</span>
                </div>
              ))}
            </div>
            <Progress value={mockShipment.progress} className="h-2" />
          </CardContent>
        </Card>

        {/* ETA Countdown */}
        <Card className="mb-6 bg-primary/5 border-primary/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-5 w-5 text-primary" />
              <span className="text-sm font-medium">Estimated Arrival</span>
            </div>
            <div className="text-4xl font-bold text-primary">
              {countdown.hours}h {countdown.minutes}m {countdown.seconds}s
            </div>
          </CardContent>
        </Card>

        {/* Current Location */}
        <Card className="mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Current Location
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-semibold">
              {mockShipment.currentLocation.city}, {mockShipment.currentLocation.state}
            </p>
            <p className="text-xs text-muted-foreground">
              {mockShipment.currentLocation.lat.toFixed(4)}, {mockShipment.currentLocation.lng.toFixed(4)}
            </p>
          </CardContent>
        </Card>

        {/* Driver Info */}
        <Card className="mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Truck className="h-4 w-4" />
              Driver Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Driver</span>
              <span className="font-medium">{mockShipment.driver.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Phone</span>
              <a href={`tel:${mockShipment.driver.phone}`} className="font-medium text-primary">
                {mockShipment.driver.phone}
              </a>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Truck #</span>
              <span className="font-medium">{mockShipment.driver.truckNumber}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Carrier</span>
              <span className="font-medium">{mockShipment.carrier.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Rating</span>
              <span className="font-medium flex items-center gap-1">
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                {mockShipment.carrier.rating}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Temperature (Reefer) */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Thermometer className="h-5 w-5 text-blue-500" />
                <span className="font-medium">Temperature</span>
              </div>
              <span className="text-2xl font-bold">{mockShipment.temperature}°F</span>
            </div>
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Tracking Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockShipment.timeline.map((item, i) => (
                <div key={i} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    {item.completed ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    ) : (
                      <Circle className="h-5 w-5 text-muted-foreground" />
                    )}
                    {i < mockShipment.timeline.length - 1 && <div className="w-px h-full bg-border my-1" />}
                  </div>
                  <div className="flex-1 pb-4">
                    <p className={`font-medium ${!item.completed && "text-muted-foreground"}`}>{item.event}</p>
                    <p className="text-sm text-muted-foreground">
                      {item.time || "Pending"} • {item.location}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Right Panel - Map */}
      <div className="flex-1 relative">
        {/* Map Controls */}
        <div className="absolute top-4 right-4 z-10 bg-background/95 backdrop-blur rounded-lg p-4 shadow-lg space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <CloudSun className="h-4 w-4" />
              <Label htmlFor="weather" className="text-sm">
                Weather
              </Label>
            </div>
            <Switch id="weather" checked={showWeather} onCheckedChange={setShowWeather} />
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Car className="h-4 w-4" />
              <Label htmlFor="traffic" className="text-sm">
                Traffic
              </Label>
            </div>
            <Switch id="traffic" checked={showTraffic} onCheckedChange={setShowTraffic} />
          </div>
        </div>

        {/* Map Placeholder */}
        <div className="w-full h-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center relative overflow-hidden">
          <img src="/us-map-route-from-los-angeles-to-phoenix-with-truc.jpg" alt="Tracking Map" className="w-full h-full object-cover" />
          {/* Animated truck marker overlay */}
          <div className="absolute" style={{ left: "45%", top: "40%" }}>
            <div className="relative">
              <div className="absolute inset-0 bg-primary/30 rounded-full animate-ping" />
              <div className="relative bg-primary text-primary-foreground p-2 rounded-full shadow-lg">
                <Truck className="h-6 w-6" />
              </div>
            </div>
          </div>
          {/* Origin marker */}
          <div className="absolute" style={{ left: "20%", top: "35%" }}>
            <div className="bg-emerald-500 text-white p-2 rounded-full shadow-lg">
              <MapPin className="h-5 w-5" />
            </div>
          </div>
          {/* Destination marker */}
          <div className="absolute" style={{ left: "70%", top: "45%" }}>
            <div className="bg-red-500 text-white p-2 rounded-full shadow-lg">
              <MapPin className="h-5 w-5" />
            </div>
          </div>
        </div>

        {/* Bottom Documents Section */}
        <div className="absolute bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <span className="font-medium">Delivery Documents</span>
              </div>
              <Badge variant="outline">2 files</Badge>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Upload className="h-4 w-4 mr-2" />
                Upload POD
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="h-4 w-4 mr-2" />
                Share Link
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
