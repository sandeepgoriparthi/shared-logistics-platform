import { PoolingFeed } from "@/components/pooling-feed"
import { RouteMap } from "@/components/route-map"
import { ActivityTimeline } from "@/components/activity-timeline"

export function DashboardContent() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-16 lg:px-8">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Pooling Feed - Takes 1 column */}
        <div className="lg:col-span-1">
          <PoolingFeed />
        </div>

        {/* Map - Takes 2 columns */}
        <div className="lg:col-span-2">
          <RouteMap />
        </div>

        {/* Activity Timeline - Full width on mobile, sidebar on desktop */}
        <div className="lg:col-span-3">
          <ActivityTimeline />
        </div>
      </div>
    </section>
  )
}
