"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Truck, Menu, X, User, Settings, LogOut } from "lucide-react"
import { useAuth } from "@/lib/auth-context"

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
  const router = useRouter()
  const { user, isAuthenticated, logout, isLoading } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    router.push("/")
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

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
          {isLoading ? (
            <div className="h-8 w-8 animate-pulse rounded-full bg-white/20" />
          ) : isAuthenticated && user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-10 w-10 rounded-full hover:bg-white/10">
                  <Avatar className="h-9 w-9 border-2 border-white/20">
                    <AvatarFallback className="bg-emerald-500 text-white">
                      {getInitials(user.full_name)}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user.full_name}</p>
                    <p className="text-xs leading-none text-muted-foreground">{user.email}</p>
                    <p className="text-xs leading-none text-muted-foreground capitalize">{user.role}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  <span>Profile</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600 focus:text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm" className="text-white/80 hover:bg-white/10 hover:text-white">
                <Link href="/auth/sign-in">Sign In</Link>
              </Button>
              <Button asChild size="sm" className="bg-emerald-500 text-white hover:bg-emerald-600">
                <Link href="/auth/register">Get Started</Link>
              </Button>
            </>
          )}
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
            {isAuthenticated && user ? (
              <>
                <div className="px-3 py-2 text-sm text-white/60">
                  Signed in as <span className="font-medium text-white">{user.full_name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="justify-start text-red-400 hover:bg-white/10 hover:text-red-300"
                  onClick={() => {
                    handleLogout()
                    setMobileMenuOpen(false)
                  }}
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </Button>
              </>
            ) : (
              <>
                <Button
                  asChild
                  variant="ghost"
                  size="sm"
                  className="justify-start text-white/80 hover:bg-white/10 hover:text-white"
                >
                  <Link href="/auth/sign-in" onClick={() => setMobileMenuOpen(false)}>Sign In</Link>
                </Button>
                <Button asChild size="sm" className="mt-2 bg-emerald-500 text-white hover:bg-emerald-600">
                  <Link href="/auth/register" onClick={() => setMobileMenuOpen(false)}>Get Started</Link>
                </Button>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
