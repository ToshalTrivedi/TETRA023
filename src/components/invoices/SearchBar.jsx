export default function SearchBar({ value, onChange }) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Search Invoice..."
      className="w-full border rounded-xl px-4 py-3"
    />
  );
}