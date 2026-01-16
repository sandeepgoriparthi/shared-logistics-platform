import { RegisterForm } from "@/components/auth/register-form"
import { Truck, Shield, Zap, TrendingUp } from "lucide-react"
import Link from "next/link"

export default function RegisterPage() {
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

        <div className="space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-bold leading-tight text-white">
              Start shipping
              <br />
              <span className="text-emerald-400">smarter today.</span>
            </h1>
            <p className="max-w-md text-lg text-blue-200">
              Create your free account and discover how freight pooling can transform your logistics operations.
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Save up to 35%</h3>
                <p className="text-sm text-blue-300">
                  Intelligent pooling matches your freight with compatible shipments.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-500/20">
                <Zap className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Real-time tracking</h3>
                <p className="text-sm text-blue-300">
                  Monitor your shipments with live GPS updates and ETA predictions.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-500/20">
                <Shield className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Vetted carriers</h3>
                <p className="text-sm text-blue-300">All carriers are verified with insurance and safety records.</p>
              </div>
            </div>
          </div>
        </div>

        <p className="text-sm text-blue-300">&copy; {new Date().getFullYear()} SharedLogistics. All rights reserved.</p>
      </div>

      {/* Right Panel - Register Form */}
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
            <h2 className="text-3xl font-bold tracking-tight text-foreground">Create an account</h2>
            <p className="text-muted-foreground">Get started with SharedLogistics for free</p>
          </div>

          <RegisterForm />

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/auth/sign-in" className="font-medium text-blue-600 hover:text-blue-500">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
