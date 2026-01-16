"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CarrierHeader } from "./carrier-header"
import { AvailableLoads } from "./available-loads"
import { ActiveLoads } from "./active-loads"
import { CarrierEarnings } from "./carrier-earnings"
import { CarrierProfile } from "./carrier-profile"

export function CarrierPortal() {
  const [activeTab, setActiveTab] = useState("loads")

  return (
    <div className="container mx-auto px-4 py-8">
      <CarrierHeader />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-8">
        <TabsList className="grid w-full max-w-2xl grid-cols-4">
          <TabsTrigger value="loads">Available Loads</TabsTrigger>
          <TabsTrigger value="active">My Active Loads</TabsTrigger>
          <TabsTrigger value="earnings">Earnings</TabsTrigger>
          <TabsTrigger value="profile">Profile</TabsTrigger>
        </TabsList>

        <TabsContent value="loads" className="mt-6">
          <AvailableLoads />
        </TabsContent>

        <TabsContent value="active" className="mt-6">
          <ActiveLoads />
        </TabsContent>

        <TabsContent value="earnings" className="mt-6">
          <CarrierEarnings />
        </TabsContent>

        <TabsContent value="profile" className="mt-6">
          <CarrierProfile />
        </TabsContent>
      </Tabs>
    </div>
  )
}
