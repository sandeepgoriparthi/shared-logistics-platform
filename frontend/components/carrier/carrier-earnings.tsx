"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Download, DollarSign, TrendingUp } from "lucide-react"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const weeklyData = [
  { week: "Week 1", earnings: 5200 },
  { week: "Week 2", earnings: 6800 },
  { week: "Week 3", earnings: 4900 },
  { week: "Week 4", earnings: 7680 },
]

const pendingPayments = [
  { id: "PAY-001", amount: 3200, loads: 2, status: "Processing", eta: "Jan 18" },
  { id: "PAY-002", amount: 1680, loads: 1, status: "Pending", eta: "Jan 20" },
]

const paymentHistory = [
  { id: "PAY-003", date: "Jan 10, 2024", amount: 4850, loads: 3, method: "ACH" },
  { id: "PAY-004", date: "Jan 3, 2024", amount: 5620, loads: 4, method: "ACH" },
  { id: "PAY-005", date: "Dec 27, 2023", amount: 3980, loads: 2, method: "ACH" },
  { id: "PAY-006", date: "Dec 20, 2023", amount: 6240, loads: 4, method: "ACH" },
]

export function CarrierEarnings() {
  return (
    <div className="space-y-6">
      {/* Weekly Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Weekly Earnings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="week" className="text-xs" />
                <YAxis className="text-xs" tickFormatter={(value) => `$${value / 1000}k`} />
                <Tooltip
                  formatter={(value: number) => [`$${value.toLocaleString()}`, "Earnings"]}
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="earnings"
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary)/0.2)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Pending Payments */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-amber-500" />
              Pending Payments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pendingPayments.map((payment) => (
                <div key={payment.id} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                  <div>
                    <p className="font-medium">${payment.amount.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">
                      {payment.loads} loads • ETA: {payment.eta}
                    </p>
                  </div>
                  <Badge variant={payment.status === "Processing" ? "default" : "secondary"}>{payment.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Payment History */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Payment History</CardTitle>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Loads</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paymentHistory.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell className="font-medium">{payment.date}</TableCell>
                    <TableCell>{payment.loads}</TableCell>
                    <TableCell className="text-right">${payment.amount.toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
