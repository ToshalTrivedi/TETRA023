import StatusBadge from "./StatusBadge";

export default function InvoiceTable({

    invoices

}) {

    return (

        <table className="w-full">

            <thead>

                <tr>

                    <th>Invoice</th>

                    <th>Vendor</th>

                    <th>Date</th>

                    <th>Amount</th>

                    <th>Status</th>

                    <th>Risk</th>

                    <th>Action</th>

                </tr>

            </thead>

            <tbody>

                {invoices.map((invoice) => (

                    <tr key={invoice.id}>

                        <td>{invoice.invoiceNumber}</td>

                        <td>{invoice.vendor}</td>

                        <td>{invoice.date}</td>

                        <td>{invoice.amount}</td>

                        <td>

                            <StatusBadge status={invoice.status} />

                        </td>

                        <td>{invoice.risk}</td>

                        <td>

                            <button>

                                View

                            </button>

                        </td>

                    </tr>

                ))}

            </tbody>

        </table>

    )

}