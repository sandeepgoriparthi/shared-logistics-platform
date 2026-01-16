import { SignInForm } from "@/components/auth/sign-in-form"
import { Truck } from "lucide-react"
import Link from "next/link"

export default function SignInPage() {
  return (
    <div className="flex min-h-screen">
      {/* Left Panel - Branding */}
      <div className="hidden w-1/2 bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 backdrop-blur">
            <Truck className="h-7 w-7 text-emerald-400" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-white">SharedLogistics</span>
        </Link>

        <div className="space-y-6">
          <h1 className="text-4xl font-bold leading-tight text-white">
            Ship Smarter.
            <br />
            <span className="text-emerald-400">Save More.</span>
          </h1>
          <p className="max-w-md text-lg text-blue-200">
            Join thousands of shippers saving up to 35% on freight costs through intelligent pooling and route
            optimization.
          </p>
          <div className="flex gap-8 pt-4">
            <div>
              <p className="text-3xl font-bold text-white">$2.4M+</p>
              <p className="text-sm text-blue-300">Total Savings</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-white">15,420</p>
              <p className="text-sm text-blue-300">Shipments Pooled</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-white">97.3%</p>
              <p className="text-sm text-blue-300">On-Time Rate</p>
            </div>
          </div>
        </div>

        <p className="text-sm text-blue-300">&copy; {new Date().getFullYear()} SharedLogistics. All rights reserved.</p>
      </div>

      {/* Right Panel - Sign In Form */}
      <div className="flex w-full items-center justify-center bg-background p-8 lg:w-1/2">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile Logo */}
          <div className="flex justify-center lg:hidden">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
                <Truck className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-foreground">SharedLogistics</span>
            </Link>
          </div>

          <div className="space-y-2 text-center lg:text-left">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">Welcome back</h2>
            <p className="text-muted-foreground">Sign in to your account to continue</p>
          </div>

          <SignInForm />

          <p className="text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link href="/auth/register" className="font-medium text-blue-600 hover:text-blue-500">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
