import { Card, CardContent } from "@/components/ui/card"
import { Calculator, MapPin, BarChart3, Users } from "lucide-react"
import Link from "next/link"

const actions = [
  {
    title: "Get Quote",
    description: "Instant freight pricing with pooling savings",
    icon: Calculator,
    href: "/quote",
    color: "bg-emerald-500",
  },
  {
    title: "Track Shipment",
    description: "Real-time location and ETA updates",
    icon: MapPin,
    href: "/tracking",
    color: "bg-blue-500",
  },
  {
    title: "View Analytics",
    description: "Performance metrics and cost insights",
    icon: BarChart3,
    href: "/analytics",
    color: "bg-amber-500",
  },
  {
    title: "Carrier Portal",
    description: "Find loads and manage capacity",
    icon: Users,
    href: "/carriers",
    color: "bg-blue-600",
  },
]

export function QuickActions() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-12 lg:px-8">
      <h2 className="mb-6 text-xl font-semibold text-foreground">Quick Actions</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {actions.map((action) => {
          const Icon = action.icon
          return (
            <Link key={action.title} href={action.href}>
              <Card className="group h-full cursor-pointer transition-all hover:shadow-lg hover:-translate-y-1">
                <CardContent className="flex items-start gap-4 p-5">
                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${action.color} text-white shadow-lg`}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-card-foreground group-hover:text-primary">{action.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{action.description}</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
