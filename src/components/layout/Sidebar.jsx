import {
  LayoutDashboard,
  Upload,
  FileText,
  ScanSearch,
  BookOpen,
  Building2,
  BadgeCheck,
  ShieldAlert,
  History,
  BarChart3,
  Settings,
} from "lucide-react";

import { NavLink } from "react-router-dom";

const menuItems = [
  {
    name: "Dashboard",
    icon: LayoutDashboard,
    path: "/",
  },
  {
    name: "Upload Invoices",
    icon: Upload,
    path: "/upload",
  },
  {
    name: "Invoice Management",
    icon: FileText,
    path: "/invoice-management",
  },
  {
    name: "OCR Extraction",
    icon: ScanSearch,
    path: "/ocr",
  },
  {
    name: "Ledger Matching",
    icon: BookOpen,
    path: "/ledger",
  },
  {
    name: "Vendor Master",
    icon: Building2,
    path: "/vendors",
  },
  {
    name: "GST Validation",
    icon: BadgeCheck,
    path: "/gst",
  },
  {
    name: "Risk Analysis",
    icon: ShieldAlert,
    path: "/risk",
  },
  {
    name: "Audit Trail",
    icon: History,
    path: "/audit",
  },
  {
    name: "Reports",
    icon: BarChart3,
    path: "/reports",
  },
  {
    name: "Settings",
    icon: Settings,
    path: "/settings",
  },
];

export default function Sidebar() {
  return (
    <aside className="w-72 bg-white border-r border-gray-200 min-h-screen">

      <div className="h-20 flex items-center justify-center border-b">

        <h1 className="text-2xl font-bold text-indigo-600">
          Invoice AI
        </h1>

      </div>

      <nav className="p-4 space-y-2">

        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.name}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
                ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-lg"
                    : "text-gray-700 hover:bg-indigo-50 hover:text-indigo-600"
                }`
              }
            >
              <Icon size={20} />

              <span>{item.name}</span>
            </NavLink>
          );
        })}

      </nav>

    </aside>
  );
}