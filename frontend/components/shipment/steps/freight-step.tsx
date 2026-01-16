"use client"

import { useFormContext } from "react-hook-form"
import { Package, Scale, Ruler, Truck, AlertTriangle, ArrowLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form"
import type { ShipmentFormData } from "../shipment-form"

const EQUIPMENT_TYPES = [
  { value: "dry-van", label: "Dry Van" },
  { value: "reefer", label: "Refrigerated (Reefer)" },
  { value: "flatbed", label: "Flatbed" },
  { value: "step-deck", label: "Step Deck" },
  { value: "conestoga", label: "Conestoga" },
]

const COMMODITY_TYPES = [
  { value: "general", label: "General Merchandise" },
  { value: "food", label: "Food & Beverage" },
  { value: "electronics", label: "Electronics" },
  { value: "machinery", label: "Machinery" },
  { value: "automotive", label: "Automotive Parts" },
  { value: "chemicals", label: "Chemicals" },
  { value: "construction", label: "Construction Materials" },
]

interface FreightStepProps {
  onNext: () => void
  onBack: () => void
}

export function FreightStep({ onNext, onBack }: FreightStepProps) {
  const form = useFormContext<ShipmentFormData>()
  const hazmat = form.watch("hazmat")

  const handleNext = async () => {
    const isValid = await form.trigger([
      "weight",
      "length",
      "width",
      "height",
      "linearFeet",
      "palletCount",
      "equipmentType",
      "commodityType",
    ])
    if (isValid) {
      onNext()
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-accent" />
            Weight & Dimensions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FormField
            control={form.control}
            name="weight"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Total Weight (lbs)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="Enter weight"
                    {...field}
                    onChange={(e) => field.onChange(Number.parseFloat(e.target.value) || 0)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="grid grid-cols-3 gap-4">
            <FormField
              control={form.control}
              name="length"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    <Ruler className="w-4 h-4" />
                    Length (in)
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="L"
                      {...field}
                      onChange={(e) => field.onChange(Number.parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="width"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Width (in)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="W"
                      {...field}
                      onChange={(e) => field.onChange(Number.parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="height"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Height (in)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="H"
                      {...field}
                      onChange={(e) => field.onChange(Number.parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <FormField
            control={form.control}
            name="linearFeet"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Linear Feet: {field.value} ft</FormLabel>
                <FormControl>
                  <Slider
                    min={1}
                    max={53}
                    step={1}
                    value={[field.value]}
                    onValueChange={(value) => field.onChange(value[0])}
                    className="py-4"
                  />
                </FormControl>
                <FormDescription>Trailer space needed (1-53 linear feet)</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="palletCount"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Number of Pallets</FormLabel>
                <Select
                  onValueChange={(value) => field.onChange(Number.parseInt(value))}
                  defaultValue={field.value?.toString()}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select pallet count" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {Array.from({ length: 26 }, (_, i) => i + 1).map((count) => (
                      <SelectItem key={count} value={count.toString()}>
                        {count} {count === 1 ? "pallet" : "pallets"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Truck className="w-5 h-5 text-accent" />
            Equipment & Commodity
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FormField
            control={form.control}
            name="equipmentType"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Equipment Type</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select equipment type" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {EQUIPMENT_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="commodityType"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Commodity Type</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select commodity type" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {COMMODITY_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="w-5 h-5 text-accent" />
            Cargo Options
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="stackable"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border border-border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Stackable</FormLabel>
                    <FormDescription>Freight can be stacked</FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="hazmat"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border border-border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Hazmat</FormLabel>
                    <FormDescription>Contains hazardous materials</FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />
          </div>

          {hazmat && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Hazardous Materials</AlertTitle>
              <AlertDescription>
                This shipment contains hazardous materials. Additional documentation, certified carriers, and special
                handling fees may apply. Our team will contact you to verify hazmat classification and requirements.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button type="button" variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button type="button" onClick={handleNext} className="px-8">
          Continue to Review
        </Button>
      </div>
    </div>
  )
}
