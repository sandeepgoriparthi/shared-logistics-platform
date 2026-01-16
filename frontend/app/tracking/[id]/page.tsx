import { Suspense } from "react"
import { Navbar } from "@/components/navbar"
import { TrackingView } from "@/components/tracking/tracking-view"

export default function TrackingPage({ params }: { params: { id: string } }) {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <Suspense fallback={<div className="flex items-center justify-center h-96">Loading...</div>}>
        <TrackingView shipmentId={params.id} />
      </Suspense>
    </div>
  )
}
