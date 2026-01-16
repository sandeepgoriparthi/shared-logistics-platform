"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Download, ArrowUpDown } from "lucide-react"
import { useState } from "react"

const savingsData = [
  { lane: "Los Angeles → Dallas", volume: 342, individual: 512000, pooled: 384000, savings: 128000 },
  { lane: "Chicago → Atlanta", volume: 298, individual: 387400, pooled: 298098, savings: 89302 },
  { lane: "Seattle → Phoenix", volume: 256, individual: 345600, pooled: 276480, savings: 69120 },
  { lane: "New York → Miami", volume: 234, individual: 398580, pooled: 318864, savings: 79716 },
  { lane: "Denver → Las Vegas", volume: 198, individual: 237600, pooled: 190080, savings: 47520 },
  { lane: "Houston → Orlando", volume: 176, individual: 264000, pooled: 211200, savings: 52800 },
]

export function SavingsTable() {
  const [sortField, setSortField] = useState<"volume" | "savings">("savings")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")

  const sortedData = [...savingsData].sort((a, b) => {
    const multiplier = sortDir === "asc" ? 1 : -1
    return (a[sortField] - b[sortField]) * multiplier
  })

  const handleSort = (field: "volume" | "savings") => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDir("desc")
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Savings Breakdown</CardTitle>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Lane</TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 font-medium hover:bg-transparent"
                  onClick={() => handleSort("volume")}
                >
                  Volume
                  <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead className="text-right">Individual</TableHead>
              <TableHead className="text-right">Pooled</TableHead>
              <TableHead className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 font-medium hover:bg-transparent"
                  onClick={() => handleSort("savings")}
                >
                  Savings
                  <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedData.map((row) => (
              <TableRow key={row.lane}>
                <TableCell className="font-medium">{row.lane}</TableCell>
                <TableCell>{row.volume}</TableCell>
                <TableCell className="text-right">${row.individual.toLocaleString()}</TableCell>
                <TableCell className="text-right">${row.pooled.toLocaleString()}</TableCell>
                <TableCell className="text-right text-emerald-600 font-semibold">
                  ${row.savings.toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
