"use client"; // Mark as a Client Component

import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"; // Import Card components

// Define the structure for an alert
interface GoldenCrossAlert {
  symbol: string;
  date: string;
  sma50: number | null;
  sma200: number | null;
}

export default function Home() {
  const [alerts, setAlerts] = useState<GoldenCrossAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastScanTime, setLastScanTime] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // 1. Fetch the list of golden cross symbols
        const resultsRes = await fetch('/api/results');
        if (!resultsRes.ok) {
          throw new Error(`Failed to fetch results: ${resultsRes.statusText}`);
        }
        const resultsData = await resultsRes.json();
        const goldenCrossSymbols: string[] = resultsData.golden_crosses || [];
        setLastScanTime(resultsData.last_scan_time);

        if (goldenCrossSymbols.length === 0) {
           setAlerts([]);
           setLoading(false);
           return;
        }

        // 2. Fetch details for each symbol
        const alertDetailsPromises = goldenCrossSymbols.map(async (symbol) => {
          const stockRes = await fetch(`/api/stock/${symbol}`);
          if (!stockRes.ok) {
            console.error(`Failed to fetch details for ${symbol}: ${stockRes.statusText}`);
            return null;
          }
          const stockData = await stockRes.json();

          if (stockData.status !== 'success' || !stockData.chart_data || stockData.chart_data.length === 0) {
             console.error(`Invalid or empty data received for ${symbol}`);
             return null;
          }

          // 3. Extract latest data
          const latestData = stockData.chart_data[stockData.chart_data.length - 1];
          return {
            symbol: symbol,
            date: latestData.Date || 'N/A',
            sma50: typeof latestData.SMA_50 === 'number' ? latestData.SMA_50 : null,
            sma200: typeof latestData.SMA_200 === 'number' ? latestData.SMA_200 : null,
          };
        });

        const resolvedAlerts = (await Promise.all(alertDetailsPromises))
                                .filter((alert): alert is GoldenCrossAlert => alert !== null);

        setAlerts(resolvedAlerts);

      } catch (err) {
        console.error("Error fetching golden cross data:", err);
        setError(err instanceof Error ? err.message : "An unknown error occurred");
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center p-6 md:p-12">
       {/* Removed the separate h1 and p tags */}
      <Card className="w-full max-w-4xl"> {/* Use Card component */}
        <CardHeader>
          <CardTitle>Tadawul Golden Cross Alerts</CardTitle>
          <CardDescription>
            {lastScanTime ? `Last Scan: ${lastScanTime}` : 'Checking scan status...'}
          </CardDescription>
        </CardHeader>
        <CardContent> {/* Wrap Table in CardContent */}
          <Table>
            <TableCaption>
              {loading ? "Loading recent signals..." : alerts.length > 0 ? "Recent Golden Cross Signals" : "No recent signals found."}
            </TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[150px]">Stock Symbol</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">50-Day SMA</TableHead>
                <TableHead className="text-right">200-Day SMA</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : error ? (
                 <TableRow>
                   <TableCell colSpan={4} className="h-24 text-center text-destructive">
                     Error loading data: {error}
                   </TableCell>
                 </TableRow>
              ) : alerts.length > 0 ? (
                alerts.map((alert) => (
                  <TableRow key={alert.symbol}>
                    <TableCell className="font-medium">{alert.symbol}</TableCell>
                    <TableCell>{alert.date}</TableCell>
                    <TableCell className="text-right">
                      {alert.sma50 !== null ? alert.sma50.toFixed(2) : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                       {alert.sma200 !== null ? alert.sma200.toFixed(2) : 'N/A'}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                    No recent golden cross signals found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </main>
  );
}
