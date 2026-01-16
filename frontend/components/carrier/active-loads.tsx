"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, MapPin, Upload, CheckCircle2 } from "lucide-react"

const mockActiveLoads = {
  accepted: [
    {
      id: "LOAD-005",
      origin: "Houston, TX",
      destination: "New Orleans, LA",
      pickupTime: "Tomorrow, 8AM",
      status: "Awaiting Pickup",
    },
  ],
  inTransit: [
    {
      id: "LOAD-006",
      origin: "Miami, FL",
      destination: "Jacksonville, FL",
      eta: "Today, 6PM",
      progress: 65,
      status: "In Transit",
    },
    {
      id: "LOAD-007",
      origin: "Nashville, TN",
      destination: "Memphis, TN",
      eta: "Today, 4PM",
      progress: 82,
      status: "In Transit",
    },
  ],
  delivered: [
    {
      id: "LOAD-008",
      origin: "Charlotte, NC",
      destination: "Raleigh, NC",
      deliveredAt: "Jan 14, 2:30PM",
      podUploaded: true,
      status: "Delivered",
    },
    {
      id: "LOAD-009",
      origin: "San Antonio, TX",
      destination: "Austin, TX",
      deliveredAt: "Jan 13, 11:00AM",
      podUploaded: false,
      status: "Pending POD",
    },
  ],
}

export function ActiveLoads() {
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null)

  const handleStatusUpdate = (loadId: string) => {
    setUpdatingStatus(loadId)
    setTimeout(() => setUpdatingStatus(null), 1500)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Accepted Column */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <h3 className="font-semibold">Accepted</h3>
          <Badge variant="secondary">{mockActiveLoads.accepted.length}</Badge>
        </div>
        {mockActiveLoads.accepted.map((load) => (
          <Card key={load.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="font-mono">
                  {load.id}
                </Badge>
                <Badge className="bg-blue-500 text-white">{load.status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-emerald-500" />
                <span>{load.origin}</span>
                <ArrowRight className="h-4 w-4" />
                <MapPin className="h-4 w-4 text-red-500" />
                <span>{load.destination}</span>
              </div>
              <p className="text-sm text-muted-foreground">Pickup: {load.pickupTime}</p>
              <Button
                variant="outline"
                className="w-full bg-transparent"
                onClick={() => handleStatusUpdate(load.id)}
                disabled={updatingStatus === load.id}
              >
                {updatingStatus === load.id ? "Updating..." : "Mark Picked Up"}
              </Button>
            </CardContent>
          </Card>
        ))}
        {mockActiveLoads.accepted.length === 0 && (
          <Card className="py-8 text-center text-muted-foreground">No accepted loads</Card>
        )}
      </div>

      {/* In Transit Column */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <h3 className="font-semibold">In Transit</h3>
          <Badge variant="secondary">{mockActiveLoads.inTransit.length}</Badge>
        </div>
        {mockActiveLoads.inTransit.map((load) => (
          <Card key={load.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="font-mono">
                  {load.id}
                </Badge>
                <Badge className="bg-amber-500 text-white">{load.status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-emerald-500" />
                <span>{load.origin}</span>
                <ArrowRight className="h-4 w-4" />
                <MapPin className="h-4 w-4 text-red-500" />
                <span>{load.destination}</span>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">{load.progress}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: `${load.progress}%` }} />
                </div>
              </div>
              <p className="text-sm text-muted-foreground">ETA: {load.eta}</p>
              <Button
                variant="outline"
                className="w-full bg-transparent"
                onClick={() => handleStatusUpdate(load.id)}
                disabled={updatingStatus === load.id}
              >
                {updatingStatus === load.id ? "Updating..." : "Mark Delivered"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Delivered Column */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <h3 className="font-semibold">Delivered</h3>
          <Badge variant="secondary">{mockActiveLoads.delivered.length}</Badge>
        </div>
        {mockActiveLoads.delivered.map((load) => (
          <Card key={load.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="font-mono">
                  {load.id}
                </Badge>
                <Badge className={load.podUploaded ? "bg-emerald-500 text-white" : "bg-amber-500 text-white"}>
                  {load.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-emerald-500" />
                <span>{load.origin}</span>
                <ArrowRight className="h-4 w-4" />
                <MapPin className="h-4 w-4 text-red-500" />
                <span>{load.destination}</span>
              </div>
              <p className="text-sm text-muted-foreground">Delivered: {load.deliveredAt}</p>
              {load.podUploaded ? (
                <div className="flex items-center gap-2 text-sm text-emerald-600">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>POD Uploaded</span>
                </div>
              ) : (
                <Button variant="outline" className="w-full bg-transparent">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload POD
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
