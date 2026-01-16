"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Package, TruckIcon, CheckCircle2, MapPin, DollarSign, Clock } from "lucide-react"

interface Activity {
  id: string
  type: "shipment_created" | "pickup" | "in_transit" | "delivered" | "pooled" | "quote"
  title: string
  description: string
  timestamp: string
  amount?: number
}

const activities: Activity[] = [
  {
    id: "1",
    type: "delivered",
    title: "Shipment Delivered",
    description: "SHP-78234 delivered to Atlanta, GA",
    timestamp: "5 min ago",
  },
  {
    id: "2",
    type: "pooled",
    title: "Shipment Pooled",
    description: "SHP-78456 pooled with 2 other shipments",
    timestamp: "12 min ago",
    amount: 423,
  },
  {
    id: "3",
    type: "pickup",
    title: "Pickup Complete",
    description: "SHP-78567 picked up from Los Angeles, CA",
    timestamp: "28 min ago",
  },
  {
    id: "4",
    type: "in_transit",
    title: "In Transit",
    description: "SHP-78123 departed Chicago distribution center",
    timestamp: "45 min ago",
  },
  {
    id: "5",
    type: "quote",
    title: "Quote Accepted",
    description: "Quote #Q-89012 accepted - Seattle to Denver",
    timestamp: "1 hour ago",
    amount: 2847,
  },
  {
    id: "6",
    type: "shipment_created",
    title: "New Shipment",
    description: "SHP-78890 created - Miami to New York",
    timestamp: "1.5 hours ago",
  },
]

const typeConfig = {
  shipment_created: { icon: Package, color: "text-blue-500", bg: "bg-blue-500/10" },
  pickup: { icon: MapPin, color: "text-amber-500", bg: "bg-amber-500/10" },
  in_transit: { icon: TruckIcon, color: "text-blue-500", bg: "bg-blue-500/10" },
  delivered: { icon: CheckCircle2, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  pooled: { icon: DollarSign, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  quote: { icon: DollarSign, color: "text-primary", bg: "bg-primary/10" },
}

export function ActivityTimeline() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Recent Activity</CardTitle>
        </div>
        <Badge variant="outline">Live</Badge>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {activities.map((activity, index) => {
            const config = typeConfig[activity.type]
            const Icon = config.icon

            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 rounded-lg border border-border p-4 transition-all hover:border-primary/30 hover:bg-muted/30"
              >
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${config.bg}`}>
                  <Icon className={`h-5 w-5 ${config.color}`} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-medium text-card-foreground">{activity.title}</h4>
                    {activity.amount && (
                      <Badge variant="secondary" className="shrink-0 bg-emerald-500/10 text-emerald-600">
                        +${activity.amount}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-0.5 text-sm text-muted-foreground">{activity.description}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{activity.timestamp}</p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
