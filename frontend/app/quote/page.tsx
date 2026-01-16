import { Navbar } from "@/components/navbar"
import { QuoteCalculator } from "@/components/quote/quote-calculator"

export default function QuotePage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">Instant Quote Calculator</h1>
            <p className="text-muted-foreground mt-2">Get an instant freight quote in seconds</p>
          </div>
          <QuoteCalculator />
        </div>
      </div>
    </div>
  )
}
