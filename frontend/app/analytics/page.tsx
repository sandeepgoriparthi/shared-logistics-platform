import { Navbar } from "@/components/navbar"
import { AnalyticsDashboard } from "@/components/analytics/analytics-dashboard"

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <AnalyticsDashboard />
    </div>
  )
}
