const invoices = [
    {
        id: "INV001",
        vendor: "ABC Traders",
        amount: "₹15,000",
        risk: "High",
    },
    {
        id: "INV002",
        vendor: "XYZ Pvt Ltd",
        amount: "₹8,200",
        risk: "Low",
    },
];

export default function RecentInvoices() {
    return (
        <div className="bg-white rounded-2xl border p-5">
            <h2 className="font-semibold mb-5">
                Recent Invoices
            </h2>
            <table className="w-full">
                <thead>
                    <tr className="border-b">
                        <th className="text-left py-2">
                            Invoice
                        </th>
                        <th className="text-left">
                            Vendor
                        </th>
                        <th className="text-left">
                            Amount
                        </th>
                        <th className="text-left">
                            Risk
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {invoices.map((invoice) => (
                        <tr key={invoice.id} className="border-b">
                            <td className="py-3">{invoice.id}</td>
                            <td>{invoice.vendor}</td>
                            <td>{invoice.amount}</td>
                            <td>{invoice.risk}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}