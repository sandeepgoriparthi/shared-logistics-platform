"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Truck, Menu, X } from "lucide-react"

const navLinks = [
  { label: "Dashboard", href: "/" },
  { label: "New Shipment", href: "/shipment/new" },
  { label: "Track", href: "/tracking/SHP-2024-001234" },
  { label: "Pooling", href: "/pooling" },
  { label: "Analytics", href: "/analytics" },
  { label: "Carrier Portal", href: "/carrier" },
  { label: "Quote", href: "/quote" },
]

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white shadow-lg">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 backdrop-blur">
            <Truck className="h-6 w-6 text-emerald-400" />
          </div>
          <span className="text-xl font-bold tracking-tight">SharedLogistics</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-sm font-medium text-white/80 transition-colors hover:bg-white/10 hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Button asChild variant="ghost" size="sm" className="text-white/80 hover:bg-white/10 hover:text-white">
            <Link href="/auth/sign-in">Sign In</Link>
          </Button>
          <Button asChild size="sm" className="bg-emerald-500 text-white hover:bg-emerald-600">
            <Link href="/auth/register">Get Started</Link>
          </Button>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="rounded-md p-2 text-white/80 hover:bg-white/10 md:hidden"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="border-t border-white/10 bg-blue-900 md:hidden">
          <nav className="flex flex-col px-4 py-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-white/80 hover:bg-white/10 hover:text-white"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <hr className="my-2 border-white/10" />
            <Button
              asChild
              variant="ghost"
              size="sm"
              className="justify-start text-white/80 hover:bg-white/10 hover:text-white"
            >
              <Link href="/auth/sign-in">Sign In</Link>
            </Button>
            <Button asChild size="sm" className="mt-2 bg-emerald-500 text-white hover:bg-emerald-600">
              <Link href="/auth/register">Get Started</Link>
            </Button>
          </nav>
        </div>
      )}
    </header>
  )
}
