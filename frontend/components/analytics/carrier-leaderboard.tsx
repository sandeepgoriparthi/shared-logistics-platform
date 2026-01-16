"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Trophy, Clock, Shield } from "lucide-react"

const carriers = [
  { name: "Swift Logistics", onTime: 98.5, damageFree: 99.8, loads: 156, rank: 1 },
  { name: "Prime Freight", onTime: 97.2, damageFree: 99.5, loads: 142, rank: 2 },
  { name: "Atlas Transport", onTime: 96.8, damageFree: 99.2, loads: 128, rank: 3 },
  { name: "Eagle Carriers", onTime: 95.4, damageFree: 98.9, loads: 115, rank: 4 },
  { name: "Pacific Haul", onTime: 94.9, damageFree: 98.6, loads: 98, rank: 5 },
]

export function CarrierLeaderboard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Trophy className="h-5 w-5 text-amber-500" />
          Carrier Leaderboard
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {carriers.map((carrier) => (
            <div
              key={carrier.name}
              className={`flex items-center gap-4 p-3 rounded-lg ${carrier.rank <= 3 ? "bg-muted/50" : ""}`}
            >
              <div className="flex items-center justify-center w-8 h-8">
                {carrier.rank === 1 ? (
                  <Trophy className="h-6 w-6 text-amber-500" />
                ) : carrier.rank === 2 ? (
                  <Trophy className="h-5 w-5 text-slate-400" />
                ) : carrier.rank === 3 ? (
                  <Trophy className="h-5 w-5 text-amber-700" />
                ) : (
                  <span className="text-lg font-bold text-muted-foreground">{carrier.rank}</span>
                )}
              </div>
              <Avatar>
                <AvatarFallback className="bg-primary/10 text-primary text-sm">
                  {carrier.name
                    .split(" ")
                    .map((w) => w[0])
                    .join("")}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{carrier.name}</p>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {carrier.onTime}%
                  </span>
                  <span className="flex items-center gap-1">
                    <Shield className="h-3 w-3" />
                    {carrier.damageFree}%
                  </span>
                </div>
              </div>
              <Badge variant="secondary">{carrier.loads} loads</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
