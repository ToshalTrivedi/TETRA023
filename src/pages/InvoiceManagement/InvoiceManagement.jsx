import { useEffect, useState } from "react";
import SearchBar from "../../components/invoices/SearchBar";
import FilterBar from "../../components/invoices/FilterBar";
import InvoiceTable from "../../components/invoices/InvoiceTable";
import { getInvoices } from "../../services/invoiceApi";

export default function InvoiceManagement() {
  const [invoices, setInvoices] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      const data = await getInvoices();
      setInvoices(data);
    } catch (error) {
      console.error("Error loading invoices:", error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Invoice Management</h1>
        <p className="text-gray-500">
          View, search and manage all uploaded invoices.
        </p>
      </div>

      <div className="flex gap-4">
        <SearchBar value={search} onChange={setSearch} />
        <FilterBar status={status} setStatus={setStatus} />
      </div>

      <InvoiceTable invoices={invoices} />
    </div>
  );
}