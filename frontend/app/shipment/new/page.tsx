import { Navbar } from "@/components/navbar"
import { ShipmentForm } from "@/components/shipment/shipment-form"

export default function NewShipmentPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <ShipmentForm />
      </main>
    </div>
  )
}
