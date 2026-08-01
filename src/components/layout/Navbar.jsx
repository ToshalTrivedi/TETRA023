import {
  Search,
  Bell,
  UserCircle,
} from "lucide-react";

export default function Navbar() {
  return (
    <header className="bg-white h-20 border-b border-gray-200 flex items-center justify-between px-8">

      <div className="relative w-96">

        <Search
          className="absolute left-4 top-3.5 text-gray-400"
          size={18}
        />

        <input
          type="text"
          placeholder="Search invoices..."
          className="w-full bg-gray-100 rounded-xl pl-11 pr-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500"
        />

      </div>

      <div className="flex items-center gap-6">

        <button className="relative">

          <Bell className="text-gray-700" />

          <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-red-500"></span>

        </button>

        <div className="flex items-center gap-3">

          <UserCircle
            size={40}
            className="text-indigo-600"
          />

          <div>

            <h3 className="font-semibold">
              Admin
            </h3>

            <p className="text-sm text-gray-500">
              Auditor
            </p>

          </div>

        </div>

      </div>

    </header>
  );
}