import { Outlet } from "react-router-dom";

import Sidebar from "../components/layout/Sidebar";
import Navbar from "../components/layout/Navbar";

export default function MainLayout() {
  return (
    <div className="flex bg-[#F6F8FC]">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}