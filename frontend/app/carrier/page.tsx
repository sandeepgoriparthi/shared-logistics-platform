import { Navbar } from "@/components/navbar"
import { CarrierPortal } from "@/components/carrier/carrier-portal"

export default function CarrierPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <CarrierPortal />
    </div>
  )
}
