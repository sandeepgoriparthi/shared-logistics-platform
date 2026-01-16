"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Search, Info, Truck } from "lucide-react"
import { PoolingCard } from "./pooling-card"
import { PoolingStats } from "./pooling-stats"
import { PoolingDetailModal } from "./pooling-detail-modal"

const mockOpportunities = [
  {
    id: "POOL-001",
    matchScore: 92,
    shipmentsCount: 3,
    origin: { city: "Los Angeles", state: "CA" },
    destination: { city: "Dallas", state: "TX" },
    totalSavings: 1240,
    savingsPercent: 28,
    individualCost: 4428,
    pooledCost: 3188,
    timeRemaining: 45,
    equipment: "Dry Van",
    shipments: [
      { id: "SHP-001", weight: 12000, ft: 18, origin: "Los Angeles, CA", dest: "Dallas, TX" },
      { id: "SHP-002", weight: 8500, ft: 12, origin: "San Diego, CA", dest: "Austin, TX" },
      { id: "SHP-003", weight: 6200, ft: 10, origin: "Riverside, CA", dest: "Houston, TX" },
    ],
  },
  {
    id: "POOL-002",
    matchScore: 87,
    shipmentsCount: 2,
    origin: { city: "Chicago", state: "IL" },
    destination: { city: "Atlanta", state: "GA" },
    totalSavings: 890,
    savingsPercent: 24,
    individualCost: 3708,
    pooledCost: 2818,
    timeRemaining: 120,
    equipment: "Reefer",
    shipments: [
      { id: "SHP-004", weight: 15000, ft: 22, origin: "Chicago, IL", dest: "Atlanta, GA" },
      { id: "SHP-005", weight: 9800, ft: 14, origin: "Milwaukee, WI", dest: "Birmingham, AL" },
    ],
  },
  {
    id: "POOL-003",
    matchScore: 78,
    shipmentsCount: 4,
    origin: { city: "Seattle", state: "WA" },
    destination: { city: "Phoenix", state: "AZ" },
    totalSavings: 1580,
    savingsPercent: 32,
    individualCost: 4937,
    pooledCost: 3357,
    timeRemaining: 30,
    equipment: "Dry Van",
    shipments: [
      { id: "SHP-006", weight: 7200, ft: 10, origin: "Seattle, WA", dest: "Phoenix, AZ" },
      { id: "SHP-007", weight: 5400, ft: 8, origin: "Portland, OR", dest: "Tucson, AZ" },
      { id: "SHP-008", weight: 8900, ft: 12, origin: "Tacoma, WA", dest: "Mesa, AZ" },
      { id: "SHP-009", weight: 4100, ft: 6, origin: "Spokane, WA", dest: "Scottsdale, AZ" },
    ],
  },
  {
    id: "POOL-004",
    matchScore: 95,
    shipmentsCount: 2,
    origin: { city: "New York", state: "NY" },
    destination: { city: "Miami", state: "FL" },
    totalSavings: 1120,
    savingsPercent: 26,
    individualCost: 4307,
    pooledCost: 3187,
    timeRemaining: 90,
    equipment: "Dry Van",
    shipments: [
      { id: "SHP-010", weight: 18000, ft: 26, origin: "New York, NY", dest: "Miami, FL" },
      { id: "SHP-011", weight: 11000, ft: 16, origin: "Newark, NJ", dest: "Fort Lauderdale, FL" },
    ],
  },
  {
    id: "POOL-005",
    matchScore: 81,
    shipmentsCount: 3,
    origin: { city: "Denver", state: "CO" },
    destination: { city: "Las Vegas", state: "NV" },
    totalSavings: 720,
    savingsPercent: 22,
    individualCost: 3272,
    pooledCost: 2552,
    timeRemaining: 60,
    equipment: "Flatbed",
    shipments: [
      { id: "SHP-012", weight: 20000, ft: 24, origin: "Denver, CO", dest: "Las Vegas, NV" },
      { id: "SHP-013", weight: 12500, ft: 18, origin: "Boulder, CO", dest: "Henderson, NV" },
      { id: "SHP-014", weight: 8000, ft: 10, origin: "Colorado Springs, CO", dest: "Reno, NV" },
    ],
  },
  {
    id: "POOL-006",
    matchScore: 89,
    shipmentsCount: 2,
    origin: { city: "Boston", state: "MA" },
    destination: { city: "Philadelphia", state: "PA" },
    totalSavings: 480,
    savingsPercent: 18,
    individualCost: 2666,
    pooledCost: 2186,
    timeRemaining: 180,
    equipment: "Reefer",
    shipments: [
      { id: "SHP-015", weight: 9500, ft: 14, origin: "Boston, MA", dest: "Philadelphia, PA" },
      { id: "SHP-016", weight: 7200, ft: 10, origin: "Providence, RI", dest: "Trenton, NJ" },
    ],
  },
]

export function PoolingDashboard() {
  const [autoPool, setAutoPool] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [originState, setOriginState] = useState("all")
  const [destState, setDestState] = useState("all")
  const [equipment, setEquipment] = useState("all")
  const [selectedPool, setSelectedPool] = useState<(typeof mockOpportunities)[0] | null>(null)

  const filteredOpportunities = mockOpportunities.filter((opp) => {
    if (originState !== "all" && opp.origin.state !== originState) return false
    if (destState !== "all" && opp.destination.state !== destState) return false
    if (equipment !== "all" && opp.equipment !== equipment) return false
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        opp.origin.city.toLowerCase().includes(query) ||
        opp.destination.city.toLowerCase().includes(query) ||
        opp.id.toLowerCase().includes(query)
      )
    }
    return true
  })

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold">Smart Pooling Engine</h1>
          <p className="text-muted-foreground mt-1">Optimize your shipments with intelligent load pooling</p>
        </div>
        <div className="flex items-center gap-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2">
                  <Switch id="auto-pool" checked={autoPool} onCheckedChange={setAutoPool} />
                  <Label htmlFor="auto-pool" className="font-medium cursor-pointer">
                    Auto-Pool
                  </Label>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </div>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>
                  Automatically pool your shipments when a high-confidence match is found. You&apos;ll be notified
                  before execution.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-8">
        <CardContent className="pt-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by city, shipment ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={originState} onValueChange={setOriginState}>
              <SelectTrigger className="w-full lg:w-40">
                <SelectValue placeholder="Origin State" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Origins</SelectItem>
                <SelectItem value="CA">California</SelectItem>
                <SelectItem value="IL">Illinois</SelectItem>
                <SelectItem value="WA">Washington</SelectItem>
                <SelectItem value="NY">New York</SelectItem>
                <SelectItem value="CO">Colorado</SelectItem>
                <SelectItem value="MA">Massachusetts</SelectItem>
              </SelectContent>
            </Select>
            <Select value={destState} onValueChange={setDestState}>
              <SelectTrigger className="w-full lg:w-40">
                <SelectValue placeholder="Dest State" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Destinations</SelectItem>
                <SelectItem value="TX">Texas</SelectItem>
                <SelectItem value="GA">Georgia</SelectItem>
                <SelectItem value="AZ">Arizona</SelectItem>
                <SelectItem value="FL">Florida</SelectItem>
                <SelectItem value="NV">Nevada</SelectItem>
                <SelectItem value="PA">Pennsylvania</SelectItem>
              </SelectContent>
            </Select>
            <Select value={equipment} onValueChange={setEquipment}>
              <SelectTrigger className="w-full lg:w-40">
                <SelectValue placeholder="Equipment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Equipment</SelectItem>
                <SelectItem value="Dry Van">Dry Van</SelectItem>
                <SelectItem value="Reefer">Reefer</SelectItem>
                <SelectItem value="Flatbed">Flatbed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main Content */}
        <div className="flex-1">
          <div className="grid gap-6 md:grid-cols-2">
            {filteredOpportunities.map((opp) => (
              <PoolingCard key={opp.id} opportunity={opp} onViewDetails={() => setSelectedPool(opp)} />
            ))}
          </div>
          {filteredOpportunities.length === 0 && (
            <Card className="py-12">
              <CardContent className="flex flex-col items-center justify-center text-center">
                <Truck className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No matching opportunities</h3>
                <p className="text-muted-foreground">Try adjusting your filters to find more pooling matches</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="w-full lg:w-80 space-y-6">
          <PoolingStats />
        </div>
      </div>

      {/* Detail Modal */}
      {selectedPool && (
        <PoolingDetailModal opportunity={selectedPool} open={!!selectedPool} onClose={() => setSelectedPool(null)} />
      )}
    </div>
  )
}
