"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const stateData: Record<string, { volume: number; name: string }> = {
  CA: { volume: 850, name: "California" },
  TX: { volume: 720, name: "Texas" },
  FL: { volume: 580, name: "Florida" },
  NY: { volume: 520, name: "New York" },
  IL: { volume: 480, name: "Illinois" },
  PA: { volume: 380, name: "Pennsylvania" },
  OH: { volume: 350, name: "Ohio" },
  GA: { volume: 420, name: "Georgia" },
  NC: { volume: 340, name: "North Carolina" },
  MI: { volume: 320, name: "Michigan" },
  NJ: { volume: 290, name: "New Jersey" },
  VA: { volume: 270, name: "Virginia" },
  WA: { volume: 310, name: "Washington" },
  AZ: { volume: 280, name: "Arizona" },
  MA: { volume: 260, name: "Massachusetts" },
  TN: { volume: 240, name: "Tennessee" },
  IN: { volume: 220, name: "Indiana" },
  MO: { volume: 200, name: "Missouri" },
  MD: { volume: 190, name: "Maryland" },
  WI: { volume: 180, name: "Wisconsin" },
  CO: { volume: 250, name: "Colorado" },
  MN: { volume: 170, name: "Minnesota" },
  SC: { volume: 160, name: "South Carolina" },
  AL: { volume: 150, name: "Alabama" },
  LA: { volume: 140, name: "Louisiana" },
  KY: { volume: 130, name: "Kentucky" },
  OR: { volume: 190, name: "Oregon" },
  OK: { volume: 120, name: "Oklahoma" },
  CT: { volume: 110, name: "Connecticut" },
  UT: { volume: 100, name: "Utah" },
  NV: { volume: 160, name: "Nevada" },
  AR: { volume: 90, name: "Arkansas" },
  IA: { volume: 85, name: "Iowa" },
  MS: { volume: 80, name: "Mississippi" },
  KS: { volume: 95, name: "Kansas" },
  NM: { volume: 70, name: "New Mexico" },
  NE: { volume: 65, name: "Nebraska" },
  ID: { volume: 55, name: "Idaho" },
  WV: { volume: 50, name: "West Virginia" },
  HI: { volume: 45, name: "Hawaii" },
  NH: { volume: 40, name: "New Hampshire" },
  ME: { volume: 35, name: "Maine" },
  MT: { volume: 30, name: "Montana" },
  RI: { volume: 38, name: "Rhode Island" },
  DE: { volume: 42, name: "Delaware" },
  SD: { volume: 25, name: "South Dakota" },
  ND: { volume: 22, name: "North Dakota" },
  AK: { volume: 28, name: "Alaska" },
  VT: { volume: 20, name: "Vermont" },
  WY: { volume: 18, name: "Wyoming" },
}

const getColor = (volume: number) => {
  if (volume >= 700) return "bg-primary"
  if (volume >= 500) return "bg-primary/80"
  if (volume >= 300) return "bg-primary/60"
  if (volume >= 150) return "bg-primary/40"
  return "bg-primary/20"
}

export function DemandHeatmap() {
  const [selectedState, setSelectedState] = useState<string | null>(null)
  const sortedStates = Object.entries(stateData).sort((a, b) => b[1].volume - a[1].volume)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Demand Heatmap</CardTitle>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          <div className="grid grid-cols-10 gap-1">
            {sortedStates.map(([code, data]) => (
              <Tooltip key={code}>
                <TooltipTrigger asChild>
                  <button
                    className={`aspect-square rounded text-xs font-medium text-white flex items-center justify-center transition-transform hover:scale-110 ${getColor(data.volume)} ${selectedState === code ? "ring-2 ring-offset-2 ring-primary" : ""}`}
                    onClick={() => setSelectedState(selectedState === code ? null : code)}
                  >
                    {code}
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="font-semibold">{data.name}</p>
                  <p className="text-sm">{data.volume} shipments</p>
                </TooltipContent>
              </Tooltip>
            ))}
          </div>
        </TooltipProvider>
        <div className="flex items-center justify-center gap-4 mt-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary/20" />
            <span>&lt;150</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary/40" />
            <span>150-299</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary/60" />
            <span>300-499</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary/80" />
            <span>500-699</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary" />
            <span>700+</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
