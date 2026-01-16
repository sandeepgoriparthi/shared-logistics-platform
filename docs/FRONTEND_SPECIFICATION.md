# Frontend Specification for v0 by Vercel

## Overview

This document provides complete specifications for building the Shared Logistics Platform frontend using v0 by Vercel. Copy each section as a prompt to v0 to generate the components.

**Tech Stack:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- MapLibre GL JS for maps
- React Query for data fetching
- Zustand for state management

---

## 🎨 Design System

### Color Palette
```
Primary: #2563EB (Blue-600)
Secondary: #10B981 (Emerald-500)
Accent: #F59E0B (Amber-500)
Success: #22C55E (Green-500)
Warning: #EAB308 (Yellow-500)
Error: #EF4444 (Red-500)
Background: #F8FAFC (Slate-50)
Surface: #FFFFFF
Text Primary: #1E293B (Slate-800)
Text Secondary: #64748B (Slate-500)
```

### Typography
```
Headings: Inter (Bold)
Body: Inter (Regular)
Monospace: JetBrains Mono (for data)
```

---

## 📱 Page Specifications

### 1. Landing Page / Dashboard

**v0 Prompt:**
```
Create a logistics platform dashboard with:
- Dark blue gradient header with logo "SharedLogistics" and navigation
- Hero section with headline "Ship Smarter. Save More." and subtext about 35% savings
- Stats bar showing: Total Savings ($2.4M), Shipments Pooled (15,420), CO2 Reduced (450 tons), On-Time Rate (97.3%)
- Quick actions grid: "Get Quote", "Track Shipment", "View Analytics", "Carrier Portal"
- Live pooling opportunities feed showing potential matches with savings %
- Interactive US map showing active routes with animated truck icons
- Recent activity timeline on the right sidebar
Use Tailwind CSS, shadcn/ui components, dark mode support
```

### 2. Shipment Creation Flow (Multi-Step Form)

**v0 Prompt:**
```
Create a multi-step shipment booking form with progress indicator:

Step 1 - Origin:
- Address autocomplete input
- City, State, ZIP fields
- Pickup date/time range pickers
- Contact name and phone
- Special instructions textarea
- Map preview showing location

Step 2 - Destination:
- Same fields as origin
- Delivery date/time range
- Appointment required toggle
- Liftgate required toggle

Step 3 - Freight Details:
- Weight input (lbs)
- Dimensions (L x W x H)
- Linear feet slider (1-53)
- Pallet count selector
- Equipment type dropdown (Dry Van, Reefer, Flatbed)
- Commodity type selector
- Stackable toggle
- Hazmat toggle with warning

Step 4 - Review & Quote:
- Summary card with all details
- Animated quote calculation
- Show: Base Rate, Fuel Surcharge, Pooling Discount, Final Price
- Pooling probability indicator (circular progress)
- "Potential savings if pooled: $XXX"
- Compare with market rate
- Book Now button

Use Tailwind, shadcn/ui, react-hook-form, zod validation
```

### 3. Real-Time Shipment Tracking

**v0 Prompt:**
```
Create a shipment tracking page with:

Left Panel (40%):
- Shipment ID and status badge (color-coded)
- Progress stepper: Booked → Picked Up → In Transit → Delivered
- ETA countdown timer
- Current location card with lat/lng
- Driver info (name, phone, truck #)
- Carrier rating stars
- Temperature reading (for reefer)
- Timeline of all tracking events with timestamps

Right Panel (60%):
- Full-screen MapLibre map
- Animated truck marker showing current position
- Origin marker (green)
- Destination marker (red)
- Route polyline (blue, dashed for remaining)
- Geofence circles around pickup/delivery
- Weather overlay toggle
- Traffic layer toggle

Bottom:
- Delivery documents section
- POD upload area
- Share tracking link button

Use MapLibre GL JS, real-time WebSocket updates simulation
```

### 4. Pooling Opportunities Dashboard

**v0 Prompt:**
```
Create a pooling opportunities dashboard:

Header:
- "Smart Pooling Engine" title
- Toggle: "Auto-Pool" with explanation tooltip
- Filter dropdowns: Origin State, Dest State, Equipment, Date Range
- Search bar

Main Content:
- Grid of opportunity cards, each showing:
  - Match score (circular gauge 0-100)
  - Number of shipments in pool (2-4 icons)
  - Origin → Destination with state badges
  - Total savings amount (large, green)
  - Savings percentage badge
  - Individual vs Pooled cost comparison bar
  - "Time remaining" countdown
  - "Execute Pool" button (primary)
  - "View Details" button (secondary)

Sidebar:
- Pooling stats: Success rate, Avg savings, This month's total
- Best performing lanes chart
- Pooling trend sparkline

Modal on "View Details":
- Map showing all shipment routes overlaid
- Each shipment details in accordion
- Combined route optimization preview
- Environmental impact (CO2 saved)
- Confirm pooling button

Use data visualization with recharts, animated numbers
```

### 5. Carrier Portal

**v0 Prompt:**
```
Create a carrier portal dashboard:

Top Bar:
- Carrier name and MC/DOT numbers
- Performance score (large circular)
- Earnings this month
- Available capacity indicator

Main Sections:

1. Available Loads (Primary):
- List of matched loads sorted by profit/mile
- Each card shows:
  - Route (City, ST → City, ST)
  - Distance and estimated hours
  - Rate and rate/mile (highlighted)
  - Pickup and delivery windows
  - Freight details (weight, ft, pallets)
  - Match score badge
  - "Accept Load" button
  - Deadhead miles from current location
- Filter: Equipment, Min rate, Max deadhead, Date

2. My Active Loads:
- Kanban board: Accepted | In Transit | Delivered
- Quick status update buttons
- Document upload for POD

3. Earnings & Payments:
- Weekly earnings chart
- Pending payments list
- Payment history table
- Download invoice button

4. Profile Settings:
- Equipment types checkboxes
- Preferred lanes multi-select
- Rate preferences
- Availability calendar
- Insurance/documents upload

Use professional trucking industry styling, mobile-responsive
```

### 6. Analytics Dashboard

**v0 Prompt:**
```
Create an executive analytics dashboard:

Top Row - KPI Cards:
- Total Revenue (with trend arrow)
- Shipments This Month
- Pooling Rate %
- Average Savings %
- On-Time Delivery %
- Carbon Saved (kg)

Charts Section (2x2 Grid):

1. Revenue Over Time:
- Area chart, monthly
- Compare to previous period
- Forecast line (dashed)

2. Pooling Performance:
- Donut chart: Pooled vs Individual
- Center shows total savings $

3. Top Lanes:
- Horizontal bar chart
- Top 10 lanes by volume
- Color by profitability

4. Demand Heatmap:
- US map with state coloring
- Intensity = shipment volume
- Hover for details

Bottom Section:

1. Savings Breakdown Table:
- Lane, Volume, Individual Cost, Pooled Cost, Savings
- Sortable columns
- Export to CSV

2. Carrier Performance:
- Leaderboard of top carriers
- On-time %, Damage-free %, Loads completed

Use recharts, react-map-gl with MapLibre, data tables with sorting/filtering
```

### 7. Quote Calculator Widget

**v0 Prompt:**
```
Create an embeddable quote calculator widget:

Compact Form:
- Origin ZIP input
- Destination ZIP input
- Weight input (lbs)
- Linear feet slider
- Equipment type select
- "Get Instant Quote" button

Results (slides in from right):
- Animated price reveal
- Price breakdown:
  - Base Rate: $X,XXX
  - Fuel Surcharge: $XXX
  - Estimated Pooling Discount: -$XXX
  - TOTAL: $X,XXX (large, bold)

- Comparison visual:
  - Our Price vs Market Average
  - Bar chart showing savings

- Pooling indicator:
  - "High pooling probability"
  - Circular progress showing 78%
  - "Could save additional $XXX"

- CTA Buttons:
  - "Book Now" (primary)
  - "Get Detailed Quote" (secondary)
  - "Save Quote" (tertiary)

Make it embeddable, configurable colors, responsive
```

### 8. Mobile-First Tracking App View

**v0 Prompt:**
```
Create a mobile-responsive shipment tracking view:

Header:
- Back arrow
- Shipment # (truncated)
- Share button
- Status pill (In Transit - blue)

Hero Section:
- Large ETA display "Arriving in 4h 23m"
- Circular progress ring showing journey %
- Current city/state

Map Section:
- 60% height map
- Current location pulsing marker
- Route line
- Pinch to zoom
- Recenter button

Quick Info Cards (horizontal scroll):
- Driver card (name, phone with tap-to-call)
- Carrier card (name, rating)
- Freight card (weight, dims)

Timeline (scrollable):
- Vertical timeline with dots
- Each event: time, description, location
- Most recent at top
- Green checkmarks for completed

Bottom Fixed Bar:
- "Contact Driver" button
- "Report Issue" button

Use mobile-first design, touch-friendly, swipe gestures
```

---

## 🧩 Reusable Components

### Component Library Prompts for v0:

**1. Shipment Card Component:**
```
Create a shipment card component showing:
- Origin → Destination with arrow
- Status badge (color-coded)
- Key metrics: distance, weight, price
- Pickup/delivery dates
- Pooling indicator
- Action buttons (Track, Details)
Compact and expandable versions, hover effects
```

**2. Route Map Component:**
```
Create a reusable route map component with:
- MapLibre GL JS integration
- Props: origin, destination, waypoints, currentPosition
- Animated route drawing
- Custom markers (truck, origin pin, dest pin)
- Info popup on marker click
- Fit bounds automatically
- Dark/light mode support
```

**3. Stats Card Component:**
```
Create an animated stats card:
- Icon on left (customizable)
- Large number with count-up animation
- Label below
- Trend indicator (up/down arrow with %)
- Sparkline chart option
- Click to expand with details
- Color variants: default, success, warning, info
```

**4. Price Breakdown Component:**
```
Create a price breakdown component:
- Animated reveal of line items
- Base rate, surcharges, discounts
- Subtotal line
- Savings highlight (green)
- Final total (large, bold)
- Compare to market toggle
- Tooltip explanations on each line
```

**5. Pooling Match Card:**
```
Create a pooling match card:
- Match score gauge (0-100)
- Shipments involved (mini cards)
- Savings amount (prominent)
- Route preview mini-map
- Time remaining countdown
- Execute button with loading state
- Expand for details
```

---

## 📊 Data Visualization Components

**Demand Heatmap:**
```
Create a US demand heatmap:
- SVG US map with state boundaries
- Color intensity based on data value
- Hover tooltips with state details
- Legend showing scale
- Animated transitions on data change
- Click state to filter
Use d3.js or react-simple-maps
```

**Savings Waterfall Chart:**
```
Create a waterfall chart showing:
- Individual cost (starting point)
- Deductions: Distance optimization, Pooling savings, Volume discount
- Final pooled cost (ending point)
- Animated bars
- Labels with amounts
Use recharts
```

**Real-time Utilization Gauge:**
```
Create a circular gauge for truck utilization:
- 0-100% scale
- Color zones: red (0-50), yellow (50-70), green (70-95)
- Animated needle
- Center text: current value
- Labels for linear feet used/total
```

---

## 🗺️ Map Configuration

**MapLibre Setup:**
```javascript
// Map configuration for the frontend
const mapConfig = {
  style: "https://tiles.stadiamaps.com/styles/alidade_smooth.json", // Free style
  center: [-98.5795, 39.8283], // US center
  zoom: 4,

  // Alternative free tile sources
  freeTileSources: [
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png"
  ],

  // Custom markers
  markers: {
    truck: "/icons/truck-marker.svg",
    origin: "/icons/origin-pin.svg",
    destination: "/icons/dest-pin.svg",
    warehouse: "/icons/warehouse.svg"
  }
};
```

---

## 📁 Recommended File Structure

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                    # Landing/Dashboard
│   ├── shipments/
│   │   ├── page.tsx                # List shipments
│   │   ├── new/page.tsx            # Create shipment
│   │   └── [id]/
│   │       ├── page.tsx            # Shipment details
│   │       └── tracking/page.tsx   # Live tracking
│   ├── pooling/
│   │   ├── page.tsx                # Pooling opportunities
│   │   └── [id]/page.tsx           # Pool details
│   ├── carriers/
│   │   ├── page.tsx                # Carrier portal
│   │   └── loads/page.tsx          # Available loads
│   ├── analytics/
│   │   └── page.tsx                # Analytics dashboard
│   └── api/                        # API routes (proxy to backend)
├── components/
│   ├── ui/                         # shadcn components
│   ├── shipment/
│   │   ├── ShipmentCard.tsx
│   │   ├── ShipmentForm.tsx
│   │   └── ShipmentTimeline.tsx
│   ├── map/
│   │   ├── RouteMap.tsx
│   │   ├── TrackingMap.tsx
│   │   └── HeatMap.tsx
│   ├── pooling/
│   │   ├── PoolingCard.tsx
│   │   └── PoolingExecutor.tsx
│   ├── analytics/
│   │   ├── StatsCard.tsx
│   │   ├── RevenueChart.tsx
│   │   └── LanePerformance.tsx
│   └── common/
│       ├── Navbar.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
├── hooks/
│   ├── useShipments.ts
│   ├── usePooling.ts
│   ├── useTracking.ts
│   └── useAnalytics.ts
├── lib/
│   ├── api.ts                      # API client
│   ├── maplibre.ts                 # Map utilities
│   └── utils.ts
├── stores/
│   ├── shipmentStore.ts
│   └── userStore.ts
└── types/
    └── index.ts
```

---

## 🔌 API Integration

**API Client Setup:**
```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = {
  shipments: {
    list: () => fetch(`${API_BASE}/shipments`),
    create: (data) => fetch(`${API_BASE}/shipments`, { method: 'POST', body: JSON.stringify(data) }),
    get: (id) => fetch(`${API_BASE}/shipments/${id}`),
    track: (id) => fetch(`${API_BASE}/shipments/${id}/tracking`),
  },
  quotes: {
    create: (data) => fetch(`${API_BASE}/quotes`, { method: 'POST', body: JSON.stringify(data) }),
    accept: (id) => fetch(`${API_BASE}/quotes/${id}/accept`, { method: 'POST' }),
  },
  pooling: {
    optimize: (data) => fetch(`${API_BASE}/pooling/optimize`, { method: 'POST', body: JSON.stringify(data) }),
    execute: (id) => fetch(`${API_BASE}/pooling/matches/${id}/execute`, { method: 'POST' }),
  },
  analytics: {
    platform: () => fetch(`${API_BASE}/analytics/platform`),
    lanes: () => fetch(`${API_BASE}/analytics/lanes`),
    forecast: (origin, dest) => fetch(`${API_BASE}/analytics/forecast?origin_state=${origin}&dest_state=${dest}`),
  },
};
```

---

## 🎯 Key UX Principles

1. **Speed First**: Show skeleton loaders, optimistic updates
2. **Progressive Disclosure**: Start simple, reveal complexity on demand
3. **Real-time Feel**: WebSocket connections, live updates, animations
4. **Mobile Responsive**: All pages work on mobile devices
5. **Accessibility**: ARIA labels, keyboard navigation, color contrast
6. **Trust Building**: Show savings prominently, display reviews/ratings
7. **Action Oriented**: Clear CTAs, minimal steps to complete tasks

---

## 🚀 v0 Generation Order

Generate components in this order for best results:

1. **Design System & Layout** - Navbar, Sidebar, Theme
2. **Dashboard** - Main landing page
3. **Shipment Form** - Multi-step booking
4. **Tracking Page** - Real-time tracking
5. **Pooling Dashboard** - Opportunities view
6. **Analytics** - Charts and metrics
7. **Carrier Portal** - Load board
8. **Mobile Views** - Responsive adaptations

---

*Copy each section as a prompt to v0.dev to generate the components. Adjust styling and functionality as needed.*
