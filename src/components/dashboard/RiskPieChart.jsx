import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

const data = [
    { name: "Low", value: 60 },
    { name: "Medium", value: 25 },
    { name: "High", value: 15 },
];

const COLORS = [
    "#22C55E",
    "#F59E0B",
    "#EF4444",
];

export default function RiskPieChart() {
    return (
        <div className="bg-white rounded-2xl border p-5">
            <h2 className="font-semibold mb-5">
                Risk Distribution
            </h2>

            <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                    <Pie
                        data={data}
                        dataKey="value"
                        outerRadius={90}
                    >
                        {data.map((entry, index) => (
                            <Cell
                                key={index}
                                fill={COLORS[index]}
                            />
                        ))}
                    </Pie>
                    <Tooltip />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}