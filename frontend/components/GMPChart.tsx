// components/GMPChart.tsx
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface GMPChartProps {
  priceBandLower?: number | null;
  priceBandUpper?: number | null;
  gmpAmount?: number | null;
  estimatedListingPrice?: number | null;
}

const GMPChart: React.FC<GMPChartProps> = ({
  priceBandLower,
  priceBandUpper,
  gmpAmount,
  estimatedListingPrice,
}) => {
  if (!priceBandLower || !priceBandUpper) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-500">Price data not available</p>
      </div>
    );
  }

  const data = [
    { label: 'Lower Band', price: priceBandLower },
    { label: 'Upper Band', price: priceBandUpper },
    { label: 'Est. Listing', price: estimatedListingPrice || priceBandUpper + (gmpAmount || 0) },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="text-sm font-semibold text-gray-900">{payload[0].payload.label}</p>
          <p className="text-sm text-gray-600">
            ₹{payload[0].value.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="label" 
            tick={{ fill: '#6b7280', fontSize: 12 }}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis 
            tick={{ fill: '#6b7280', fontSize: 12 }}
            axisLine={{ stroke: '#e5e7eb' }}
            label={{ value: 'Price (₹)', angle: -90, position: 'insideLeft', style: { fill: '#6b7280', fontSize: 12 } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine 
            y={priceBandUpper} 
            stroke="#0ea5e9" 
            strokeDasharray="3 3" 
            label={{ value: 'Issue Price', fill: '#0ea5e9', fontSize: 10 }} 
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#8b5cf6" 
            strokeWidth={3}
            dot={{ fill: '#8b5cf6', r: 6 }}
            activeDot={{ r: 8 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default GMPChart;
