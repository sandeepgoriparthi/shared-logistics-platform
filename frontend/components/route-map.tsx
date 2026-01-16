"use client"

import { useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Truck, MapPin, ZoomIn, ZoomOut, Maximize2 } from "lucide-react"

interface ActiveRoute {
  id: string
  origin: { lat: number; lng: number; city: string }
  destination: { lat: number; lng: number; city: string }
  currentPosition: { lat: number; lng: number }
  status: "in-transit" | "pickup" | "delivery"
  truckId: string
}

const activeRoutes: ActiveRoute[] = [
  {
    id: "1",
    origin: { lat: 34.0522, lng: -118.2437, city: "Los Angeles, CA" },
    destination: { lat: 32.7767, lng: -96.797, city: "Dallas, TX" },
    currentPosition: { lat: 33.4484, lng: -112.074 },
    status: "in-transit",
    truckId: "TRK-1234",
  },
  {
    id: "2",
    origin: { lat: 41.8781, lng: -87.6298, city: "Chicago, IL" },
    destination: { lat: 33.749, lng: -84.388, city: "Atlanta, GA" },
    currentPosition: { lat: 39.7684, lng: -86.1581 },
    status: "in-transit",
    truckId: "TRK-5678",
  },
  {
    id: "3",
    origin: { lat: 47.6062, lng: -122.3321, city: "Seattle, WA" },
    destination: { lat: 39.7392, lng: -104.9903, city: "Denver, CO" },
    currentPosition: { lat: 43.615, lng: -116.2023 },
    status: "in-transit",
    truckId: "TRK-9012",
  },
]

export function RouteMap() {
  const mapRef = useRef<HTMLDivElement>(null)
  const [selectedRoute, setSelectedRoute] = useState<ActiveRoute | null>(null)
  const [zoom, setZoom] = useState(4)

  // Simplified US map with routes visualization
  return (
    <Card className="h-full min-h-[500px]">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-blue-500" />
          <CardTitle className="text-lg">Active Routes</CardTitle>
        </div>
        <Badge variant="secondary" className="bg-blue-500/10 text-blue-600">
          {activeRoutes.length} In Transit
        </Badge>
      </CardHeader>
      <CardContent className="p-0">
        {/* Map Container */}
        <div ref={mapRef} className="relative h-[400px] w-full overflow-hidden rounded-b-lg bg-slate-100">
          {/* SVG US Map Background */}
          <svg
            viewBox="0 0 960 600"
            className="absolute inset-0 h-full w-full"
            style={{ transform: `scale(${zoom / 4})` }}
          >
            {/* Simplified US outline */}
            <path
              d="M158,200 L220,180 L280,160 L350,150 L420,140 L500,135 L580,140 L650,150 L720,165 L780,180 L820,200 L850,230 L870,270 L880,320 L870,370 L850,410 L820,440 L780,460 L720,475 L650,485 L580,490 L500,492 L420,490 L350,485 L280,475 L220,460 L170,440 L140,410 L120,370 L110,320 L120,270 L140,230 Z"
              fill="#e2e8f0"
              stroke="#cbd5e1"
              strokeWidth="2"
            />

            {/* Route Lines */}
            {activeRoutes.map((route) => {
              const startX = ((route.origin.lng + 130) / 70) * 800 + 80
              const startY = ((50 - route.origin.lat) / 30) * 400 + 100
              const endX = ((route.destination.lng + 130) / 70) * 800 + 80
              const endY = ((50 - route.destination.lat) / 30) * 400 + 100
              const currentX = ((route.currentPosition.lng + 130) / 70) * 800 + 80
              const currentY = ((50 - route.currentPosition.lat) / 30) * 400 + 100

              return (
                <g key={route.id}>
                  {/* Route path */}
                  <line
                    x1={startX}
                    y1={startY}
                    x2={endX}
                    y2={endY}
                    stroke="#3b82f6"
                    strokeWidth="2"
                    strokeDasharray="8,4"
                    opacity="0.5"
                  />
                  {/* Completed portion */}
                  <line x1={startX} y1={startY} x2={currentX} y2={currentY} stroke="#3b82f6" strokeWidth="3" />
                  {/* Origin marker */}
                  <circle cx={startX} cy={startY} r="8" fill="#22c55e" stroke="#fff" strokeWidth="2" />
                  {/* Destination marker */}
                  <circle cx={endX} cy={endY} r="8" fill="#ef4444" stroke="#fff" strokeWidth="2" />
                  {/* Current position (truck) */}
                  <g transform={`translate(${currentX - 12}, ${currentY - 12})`}>
                    <rect width="24" height="24" rx="4" fill="#3b82f6" />
                    <path
                      d="M4,14 L4,10 L8,10 L8,8 L16,8 L16,10 L20,10 L20,14 L18,14 L18,16 L16,16 L16,14 L8,14 L8,16 L6,16 L6,14 Z"
                      fill="white"
                      transform="scale(0.8) translate(3, 3)"
                    />
                  </g>
                </g>
              )
            })}
          </svg>

          {/* Map Controls */}
          <div className="absolute right-4 top-4 flex flex-col gap-2">
            <Button
              size="icon"
              variant="secondary"
              className="h-8 w-8 bg-white shadow-md"
              onClick={() => setZoom((z) => Math.min(z + 1, 8))}
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              className="h-8 w-8 bg-white shadow-md"
              onClick={() => setZoom((z) => Math.max(z - 1, 2))}
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button size="icon" variant="secondary" className="h-8 w-8 bg-white shadow-md">
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 flex items-center gap-4 rounded-lg bg-white/90 px-3 py-2 shadow-md backdrop-blur">
            <div className="flex items-center gap-1.5">
              <div className="h-3 w-3 rounded-full bg-emerald-500" />
              <span className="text-xs text-muted-foreground">Origin</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-3 w-3 rounded-full bg-red-500" />
              <span className="text-xs text-muted-foreground">Destination</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-3 w-3 rounded bg-blue-500" />
              <span className="text-xs text-muted-foreground">In Transit</span>
            </div>
          </div>
        </div>

        {/* Route List */}
        <div className="border-t border-border p-4">
          <div className="grid gap-2 sm:grid-cols-3">
            {activeRoutes.map((route) => (
              <button
                key={route.id}
                onClick={() => setSelectedRoute(route)}
                className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all hover:border-primary/30 hover:bg-muted/50 ${
                  selectedRoute?.id === route.id ? "border-primary bg-primary/5" : "border-border"
                }`}
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                  <Truck className="h-5 w-5 text-blue-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{route.truckId}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {route.origin.city.split(",")[0]} → {route.destination.city.split(",")[0]}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
