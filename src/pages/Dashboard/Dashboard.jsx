import StatCard from "../../components/dashboard/StatCard";
import RiskTrendChart from "../../components/dashboard/RiskTrendChart";
import RiskPieChart from "../../components/dashboard/RiskPieChart";
import RecentInvoices from "../../components/dashboard/RecentInvoices";
import RecentActivities from "../../components/dashboard/RecentActivities";

export default function Dashboard() {
    return (
        <div>+
            <h1 className="text-4xl font-bold">
                Dashboard
            </h1>

            <p className="text-gray-500 mb-8">
                AI Invoice Risk Scanner Overview
            </p>
            <div className="grid grid-cols-4 gap-6 mb-8">

                <StatCard
                    title="Total Invoices"
                    value="1,248"
                    color="text-blue-600"
                />
                <StatCard
                    title="High Risk"
                    value="26"
                    color="text-red-500"
                />
                <StatCard
                    title="Scanned Today"
                    value="154"
                    color="text-green-500"
                />
                <StatCard
                    title="Registered Vendors"
                    value="91"
                    color="text-purple-500"/>
            </div>
            <div className="grid grid-cols-2 gap-6 mb-8">
                <RiskTrendChart />
                <RiskPieChart />
            </div>
            <div className="grid grid-cols-2 gap-6">
                <RecentInvoices />
                <RecentActivities />
            </div>
        </div>
    );
}