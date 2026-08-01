import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/Dashboard/Dashboard";
import UploadInvoices from "../pages/UploadInvoices/UploadInvoices";
import InvoiceManagement from "../pages/InvoiceManagement/InvoiceManagement";
import OCRExtraction from "../pages/OCRExtraction/OCRExtraction";
import LedgerMatching from "../pages/LedgerMatching/LedgerMatching";
import VendorMaster from "../pages/VendorMaster/VendorMaster";
import GSTValidation from "../pages/GSTValidation/GSTValidation";
import RiskAnalysis from "../pages/RiskAnalysis/RiskAnalysis";
import AuditTrail from "../pages/AuditTrail/AuditTrail";
import Reports from "../pages/Reports/Reports";
import Settings from "../pages/Settings/Settings";

import MainLayout from "../layouts/MainLayout";

export default function AppRoutes() {
    return (
        <Routes>

            <Route element={<MainLayout />}>

                <Route path="/" element={<Dashboard />} />

                <Route path="/upload" element={<UploadInvoices />} />

                <Route path="/invoice-management" element={<InvoiceManagement />} />

                <Route path="/ocr" element={<OCRExtraction />} />

                <Route path="/ledger" element={<LedgerMatching />} />

                <Route path="/vendors" element={<VendorMaster />} />

                <Route path="/gst" element={<GSTValidation />} />

                <Route path="/risk" element={<RiskAnalysis />} />

                <Route path="/audit" element={<AuditTrail />} />

                <Route path="/reports" element={<Reports />} />

                <Route path="/settings" element={<Settings />} />

            </Route>

        </Routes>
    );
}