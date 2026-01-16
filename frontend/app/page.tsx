import { Navbar } from "@/components/navbar"
import { HeroSection } from "@/components/hero-section"
import { StatsBar } from "@/components/stats-bar"
import { QuickActions } from "@/components/quick-actions"
import { DashboardContent } from "@/components/dashboard-content"

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        <HeroSection />
        <StatsBar />
        <QuickActions />
        <DashboardContent />
      </main>
    </div>
  )
}
