"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Truck, MapPin, FileText, Save, Upload } from "lucide-react"

export function CarrierProfile() {
  const [equipmentTypes, setEquipmentTypes] = useState(["Dry Van", "Reefer"])
  const [preferredLanes, setPreferredLanes] = useState(["CA → TX", "TX → FL", "IL → GA"])
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = () => {
    setIsSaving(true)
    setTimeout(() => setIsSaving(false), 1500)
  }

  const toggleEquipment = (type: string) => {
    setEquipmentTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]))
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Equipment Types */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Truck className="h-5 w-5" />
            Equipment Types
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {["Dry Van", "Reefer", "Flatbed", "Step Deck", "Power Only"].map((type) => (
            <div key={type} className="flex items-center space-x-3">
              <Checkbox
                id={type}
                checked={equipmentTypes.includes(type)}
                onCheckedChange={() => toggleEquipment(type)}
              />
              <Label htmlFor={type} className="cursor-pointer">
                {type}
              </Label>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Preferred Lanes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Preferred Lanes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            {preferredLanes.map((lane) => (
              <Badge key={lane} variant="secondary" className="px-3 py-1">
                {lane}
                <button
                  className="ml-2 text-muted-foreground hover:text-foreground"
                  onClick={() => setPreferredLanes((prev) => prev.filter((l) => l !== lane))}
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input placeholder="Add lane (e.g. NY → FL)" className="flex-1" />
            <Button variant="outline">Add</Button>
          </div>
        </CardContent>
      </Card>

      {/* Rate Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>Rate Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="minRate">Min Rate/Mile ($)</Label>
              <Input id="minRate" type="number" defaultValue="2.00" step="0.10" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="maxDeadhead">Max Deadhead (mi)</Label>
              <Input id="maxDeadhead" type="number" defaultValue="75" step="5" />
            </div>
          </div>
          <Separator />
          <div className="space-y-2">
            <Label htmlFor="targetWeekly">Weekly Target ($)</Label>
            <Input id="targetWeekly" type="number" defaultValue="6000" step="500" />
          </div>
        </CardContent>
      </Card>

      {/* Documents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Insurance & Documents
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {[
              { name: "Certificate of Insurance", status: "valid", expires: "Dec 2024" },
              { name: "Authority Letter", status: "valid", expires: "N/A" },
              { name: "W-9 Form", status: "pending", expires: "Upload Required" },
            ].map((doc) => (
              <div key={doc.name} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div>
                  <p className="font-medium">{doc.name}</p>
                  <p className="text-xs text-muted-foreground">{doc.expires}</p>
                </div>
                <Badge variant={doc.status === "valid" ? "default" : "destructive"}>
                  {doc.status === "valid" ? "Valid" : "Required"}
                </Badge>
              </div>
            ))}
          </div>
          <Button variant="outline" className="w-full bg-transparent">
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="md:col-span-2">
        <Button onClick={handleSave} disabled={isSaving} className="w-full md:w-auto">
          <Save className="h-4 w-4 mr-2" />
          {isSaving ? "Saving..." : "Save Profile"}
        </Button>
      </div>
    </div>
  )
}
