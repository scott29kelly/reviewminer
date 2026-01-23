'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface IntensityChartProps {
  data: Record<string, number>;
}

// Semantic colors for intensity levels
const COLORS = {
  high: '#f87171',   // red-400
  medium: '#fbbf24', // amber-400
  low: '#34d399',    // emerald-400
};

const LABELS = {
  high: 'High Intensity',
  medium: 'Medium',
  low: 'Low',
};

export function IntensityChart({ data }: IntensityChartProps) {
  const chartData = Object.entries(data)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({
      name: LABELS[name as keyof typeof LABELS] || name,
      value,
      color: COLORS[name as keyof typeof COLORS] || '#71717a',
    }));

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  if (total === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={200}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="45%"
          innerRadius={55}
          outerRadius={80}
          paddingAngle={4}
          dataKey="value"
          strokeWidth={0}
        >
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.color}
              style={{ filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.15))' }}
            />
          ))}
        </Pie>
        {/* Center text */}
        <text
          x="50%"
          y="45%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="fill-foreground"
        >
          <tspan x="50%" dy="-0.5em" fontSize="24" fontWeight="700">
            {total}
          </tspan>
          <tspan x="50%" dy="1.5em" fontSize="12" className="fill-muted-foreground">
            Total
          </tspan>
        </text>
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--popover)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            color: 'var(--popover-foreground)',
            boxShadow: '0 10px 40px -10px rgba(0,0,0,0.3)',
            padding: '12px 16px',
          }}
          formatter={(value: number) => [
            <span key="value" className="font-semibold">{value} pain points</span>,
            null
          ]}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value: string) => (
            <span className="text-sm text-foreground ml-1">{value}</span>
          )}
          iconType="circle"
          iconSize={10}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
