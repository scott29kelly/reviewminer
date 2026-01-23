'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface SourceChartProps {
  data: Record<string, number>;
}

// Vibrant, distinguishable colors
const COLORS = [
  '#818cf8', // indigo
  '#34d399', // emerald
  '#fbbf24', // amber
  '#f472b6', // pink
  '#22d3ee', // cyan
  '#fb7185', // rose
  '#a78bfa', // violet
  '#60a5fa', // blue
];

const RADIAN = Math.PI / 180;

interface LabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percent: number;
  name: string;
}

const renderCustomizedLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
  name,
}: LabelProps) => {
  const radius = outerRadius + 30;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="currentColor"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="text-sm font-medium fill-foreground"
    >
      {name} ({(percent * 100).toFixed(0)}%)
    </text>
  );
};

export function SourceChart({ data }: SourceChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
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
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={3}
          dataKey="value"
          label={renderCustomizedLabel}
          labelLine={{
            stroke: 'currentColor',
            strokeOpacity: 0.3,
            strokeWidth: 1,
          }}
        >
          {chartData.map((_, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={COLORS[index % COLORS.length]}
              stroke="transparent"
              style={{ filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.15))' }}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--popover)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            color: 'var(--popover-foreground)',
            boxShadow: '0 10px 40px -10px rgba(0,0,0,0.3)',
            padding: '12px 16px',
          }}
          formatter={(value: number, name: string) => [
            <span key="value" className="font-semibold">{value} reviews</span>,
            <span key="name" className="text-muted-foreground">{name}</span>
          ]}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
