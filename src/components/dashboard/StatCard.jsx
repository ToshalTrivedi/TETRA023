export default function StatCard({
  title,
  value,
  color,
}) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6 border">
      <h3 className="text-gray-500 text-sm">
        {title}
      </h3>
      <h1
        className={`text-4xl font-bold mt-3 ${color}`}>
        {value}
      </h1>
    </div>
  );
}