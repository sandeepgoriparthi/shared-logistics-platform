"use client"

import { KPICards } from "./kpi-cards"
import { RevenueChart } from "./revenue-chart"
import { PoolingPerformance } from "./pooling-performance"
import { TopLanesChart } from "./top-lanes-chart"
import { DemandHeatmap } from "./demand-heatmap"
import { SavingsTable } from "./savings-table"
import { CarrierLeaderboard } from "./carrier-leaderboard"

export function AnalyticsDashboard() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <p className="text-muted-foreground mt-1">Executive overview of platform performance</p>
      </div>

      {/* KPI Cards */}
      <KPICards />

      {/* Charts Grid */}
      <div className="grid gap-6 md:grid-cols-2 mt-8">
        <RevenueChart />
        <PoolingPerformance />
        <TopLanesChart />
        <DemandHeatmap />
      </div>

      {/* Tables Section */}
      <div className="grid gap-6 md:grid-cols-2 mt-8">
        <SavingsTable />
        <CarrierLeaderboard />
      </div>
    </div>
  )
}
