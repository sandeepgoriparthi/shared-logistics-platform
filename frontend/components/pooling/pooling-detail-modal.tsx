"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { MapPin, Package, Truck, Leaf, ArrowRight, Scale, Ruler } from "lucide-react"

interface PoolingDetailModalProps {
  opportunity: {
    id: string
    matchScore: number
    shipmentsCount: number
    origin: { city: string; state: string }
    destination: { city: string; state: string }
    totalSavings: number
    savingsPercent: number
    individualCost: number
    pooledCost: number
    timeRemaining: number
    equipment: string
    shipments: Array<{
      id: string
      weight: number
      ft: number
      origin: string
      dest: string
    }>
  }
  open: boolean
  onClose: () => void
}

export function PoolingDetailModal({ opportunity, open, onClose }: PoolingDetailModalProps) {
  const co2Saved = Math.round(opportunity.totalSavings * 0.08)

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span>Pooling Opportunity {opportunity.id}</span>
            <Badge className="bg-emerald-500 text-white">{opportunity.savingsPercent}% Savings</Badge>
          </DialogTitle>
        </DialogHeader>

        {/* Map Preview */}
        <div className="h-48 bg-slate-100 dark:bg-slate-800 rounded-lg overflow-hidden relative">
          <img src="/us-map-with-multiple-routes-overlaid-showing-pooli.jpg" alt="Route Map" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
          <div className="absolute bottom-4 left-4 flex items-center gap-2">
            <Badge variant="secondary" className="flex items-center gap-1">
              <MapPin className="h-3 w-3 text-emerald-500" />
              {opportunity.origin.city}, {opportunity.origin.state}
            </Badge>
            <ArrowRight className="h-4 w-4" />
            <Badge variant="secondary" className="flex items-center gap-1">
              <MapPin className="h-3 w-3 text-red-500" />
              {opportunity.destination.city}, {opportunity.destination.state}
            </Badge>
          </div>
        </div>

        {/* Shipments Accordion */}
        <div className="space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Package className="h-5 w-5" />
            Shipments in Pool ({opportunity.shipmentsCount})
          </h3>
          <Accordion type="single" collapsible className="w-full">
            {opportunity.shipments.map((shipment, i) => (
              <AccordionItem key={shipment.id} value={shipment.id}>
                <AccordionTrigger className="hover:no-underline">
                  <div className="flex items-center gap-4">
                    <Badge variant="outline">{shipment.id}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {shipment.origin} → {shipment.dest}
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Scale className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        <span className="text-muted-foreground">Weight:</span>{" "}
                        <span className="font-medium">{shipment.weight.toLocaleString()} lbs</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Ruler className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        <span className="text-muted-foreground">Linear Feet:</span>{" "}
                        <span className="font-medium">{shipment.ft} ft</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-emerald-500" />
                      <span className="text-sm">
                        <span className="text-muted-foreground">Origin:</span>{" "}
                        <span className="font-medium">{shipment.origin}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-red-500" />
                      <span className="text-sm">
                        <span className="text-muted-foreground">Destination:</span>{" "}
                        <span className="font-medium">{shipment.dest}</span>
                      </span>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>

        <Separator />

        {/* Savings Breakdown */}
        <div className="space-y-4">
          <h3 className="font-semibold">Cost Comparison</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Individual Shipping Cost</span>
              <span className="font-medium line-through text-muted-foreground">
                ${opportunity.individualCost.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Pooled Shipping Cost</span>
              <span className="font-semibold text-primary">${opportunity.pooledCost.toLocaleString()}</span>
            </div>
            <Separator />
            <div className="flex justify-between items-center">
              <span className="font-semibold text-emerald-600">Total Savings</span>
              <span className="text-2xl font-bold text-emerald-600">${opportunity.totalSavings.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Environmental Impact */}
        <div className="bg-emerald-50 dark:bg-emerald-950/30 rounded-lg p-4 flex items-center gap-4">
          <div className="p-3 bg-emerald-100 dark:bg-emerald-900 rounded-full">
            <Leaf className="h-6 w-6 text-emerald-600" />
          </div>
          <div>
            <p className="font-semibold text-emerald-700 dark:text-emerald-300">Environmental Impact</p>
            <p className="text-sm text-emerald-600">
              This pool will save approximately <span className="font-bold">{co2Saved} kg</span> of CO2 emissions
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <Button className="flex-1" size="lg">
            <Truck className="h-5 w-5 mr-2" />
            Confirm Pooling
          </Button>
          <Button variant="outline" size="lg" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
