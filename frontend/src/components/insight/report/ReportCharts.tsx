import { BarChart3 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ReportChart } from "@/types/report";

interface ReportChartsProps {
  charts: ReportChart[];
}

export function ReportCharts({ charts }: ReportChartsProps) {
  if (!charts.length) return null;

  return (
    <section id="charts" className="scroll-mt-28">
      <div className="mb-5 flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold text-white">Visual Overview</h3>
      </div>

      <div className="space-y-5">
        {charts.map((chart, index) => (
          <div
            key={`${chart.title}-${index}`}
            className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl"
          >
            <h4 className="mb-4 text-sm font-semibold text-white">
              {chart.title}
            </h4>

            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                {chart.type === "line" ? (
                  <LineChart
                    data={chart.data}
                    margin={{ top: 8, right: 12, bottom: 0, left: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.07)"
                    />
                    <XAxis
                      dataKey="label"
                      stroke="rgba(255,255,255,0.42)"
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="rgba(255,255,255,0.42)"
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                      width={48}
                    />
                    <Tooltip
                      cursor={{ stroke: "rgba(255,255,255,0.12)" }}
                      contentStyle={{
                        background: "rgba(8,13,27,0.96)",
                        border: "1px solid rgba(255,255,255,0.12)",
                        borderRadius: 14,
                        color: "#fff",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2.5}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                ) : chart.type === "pie" ? (
                  <PieChart>
                    <Tooltip
                      contentStyle={{
                        background: "rgba(8,13,27,0.96)",
                        border: "1px solid rgba(255,255,255,0.12)",
                        borderRadius: 14,
                        color: "#fff",
                      }}
                    />
                    <Pie
                      data={chart.data}
                      dataKey="value"
                      nameKey="label"
                      outerRadius={78}
                      innerRadius={42}
                      fill="hsl(var(--primary))"
                    />
                  </PieChart>
                ) : (
                  <BarChart
                    data={chart.data}
                    margin={{ top: 8, right: 12, bottom: 0, left: 0 }}
                    barCategoryGap="45%"
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.07)"
                    />
                    <XAxis
                      dataKey="label"
                      stroke="rgba(255,255,255,0.42)"
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="rgba(255,255,255,0.42)"
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                      width={48}
                    />
                    <Tooltip
                      cursor={{ fill: "rgba(255,255,255,0.035)" }}
                      contentStyle={{
                        background: "rgba(8,13,27,0.96)",
                        border: "1px solid rgba(255,255,255,0.12)",
                        borderRadius: 14,
                        color: "#fff",
                      }}
                    />
                    <Bar
                      dataKey="value"
                      radius={[8, 8, 0, 0]}
                      fill="hsl(var(--primary))"
                      maxBarSize={54}
                    />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}