import {
  LineChart,
  Line,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";

const data = [
  { day: "Mon", risk: 12 },
  { day: "Tue", risk: 18 },
  { day: "Wed", risk: 8 },
  { day: "Thu", risk: 25 },
  { day: "Fri", risk: 15 },
  { day: "Sat", risk: 11 },
];

export default function RiskTrendChart() {
  return (
    <div className="bg-white rounded-2xl border p-5">

      <h2 className="font-semibold text-lg mb-5">
        Weekly Risk Trend
      </h2>

      <ResponsiveContainer width="100%" height={300}>

        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" />
          <YAxis />

          <Tooltip />
          <Line
            dataKey="risk"
            stroke="#4F46E5"
            strokeWidth={3}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}