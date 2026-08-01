export default function RecentActivities() {
    return (
        <div className="bg-white rounded-2xl border p-5">
            <h2 className="font-semibold mb-5">
                Recent Activities
            </h2>
            <ul className="space-y-4">
                <li>✅ Invoice INV001 uploaded</li>
                <li>⚠ High Risk Invoice Detected</li>
                <li>📄 OCR Extraction Completed</li>
                <li>✔ Ledger Matched Successfully</li>
            </ul>
        </div>
    );
}