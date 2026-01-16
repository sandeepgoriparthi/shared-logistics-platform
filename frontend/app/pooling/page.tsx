import { Navbar } from "@/components/navbar"
import { PoolingDashboard } from "@/components/pooling/pooling-dashboard"

export default function PoolingPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <PoolingDashboard />
    </div>
  )
}
