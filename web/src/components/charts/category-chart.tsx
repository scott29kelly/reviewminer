'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface CategoryChartProps {
  data: Record<string, number>;
}

// Vibrant, high-contrast colors
const COLORS = [
  '#818cf8', // indigo
  '#a78bfa', // violet
  '#f472b6', // pink
  '#fbbf24', // amber
  '#34d399', // emerald
  '#22d3ee', // cyan
  '#60a5fa', // blue
  '#fb7185', // rose
];

export function CategoryChart({ data }: CategoryChartProps) {
  const chartData = Object.entries(data)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  if (chartData.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={200}>
      <BarChart 
        data={chartData} 
        layout="vertical" 
        margin={{ left: 0, right: 24, top: 8, bottom: 8 }}
        barCategoryGap="20%"
      >
        <XAxis 
          type="number" 
          stroke="currentColor"
          strokeOpacity={0.3}
          fontSize={12}
          tickLine={false}
          axisLine={false}
          className="text-muted-foreground"
        />
        <YAxis
          type="category"
          dataKey="name"
          stroke="currentColor"
          strokeOpacity={0}
          fontSize={13}
          fontWeight={500}
          width={110}
          tickLine={false}
          axisLine={false}
          className="text-foreground"
          tickFormatter={(value) => value.length > 12 ? value.slice(0, 12) + '...' : value}
        />
        <Tooltip
          cursor={{ fill: 'currentColor', fillOpacity: 0.05 }}
          contentStyle={{
            backgroundColor: 'var(--popover)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            color: 'var(--popover-foreground)',
            boxShadow: '0 10px 40px -10px rgba(0,0,0,0.3)',
            padding: '12px 16px',
          }}
          labelStyle={{ fontWeight: 600, marginBottom: '4px' }}
          formatter={(value: number) => [
            <span key="value" className="font-semibold">{value} pain points</span>,
            null
          ]}
        />
        <Bar 
          dataKey="value" 
          radius={[0, 8, 8, 0]}
          maxBarSize={32}
        >
          {chartData.map((_, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={COLORS[index % COLORS.length]}
              style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
