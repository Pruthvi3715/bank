import { useState, useCallback } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  LayoutGrid,
  Bell,
  Share2,
  FileText,
  ShieldCheck,
  Menu,
  X,
  Activity,
} from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

const navItems = [
  { to: "/", icon: LayoutGrid, label: "Dashboard" },
  { to: "/alerts", icon: Bell, label: "Alerts" },
  { to: "/graph", icon: Share2, label: "Graph Analysis" },
  { to: "/sar", icon: FileText, label: "SAR Reports" },
  { to: "/tests", icon: ShieldCheck, label: "Adversarial Tests" },
];

const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.25, ease: "easeInOut" },
};

export const AppLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950 text-gray-100">
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={closeSidebar}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence>
        <motion.aside
          key="sidebar"
          initial={false}
          animate={{ x: 0 }}
          className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-gray-900 border-r border-gray-800 transition-transform duration-300 lg:static lg:translate-x-0 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          {/* Sidebar header */}
          <div className="flex items-center justify-between px-5 py-5 border-b border-gray-800">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="h-7 w-7 text-purple-500" />
              <span className="text-lg font-bold tracking-tight">
                GraphSentinel
              </span>
            </div>
            <button
              onClick={closeSidebar}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-800 hover:text-gray-200 lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                onClick={closeSidebar}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150 ${
                    isActive
                      ? "bg-purple-600/20 text-purple-400"
                      : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                  }`
                }
              >
                <Icon className="h-[18px] w-[18px] shrink-0" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Sidebar footer */}
          <div className="border-t border-gray-800 px-4 py-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Theme</span>
              <ThemeToggle />
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Activity className="h-3.5 w-3.5 text-emerald-500" />
              <span>
                System Status:{" "}
                <span className="text-emerald-400 font-medium">
                  Operational
                </span>
              </span>
            </div>
          </div>
        </motion.aside>
      </AnimatePresence>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <header className="flex items-center gap-3 border-b border-gray-800 bg-gray-900 px-4 py-3 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-gray-200"
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-purple-500" />
            <span className="font-semibold">GraphSentinel</span>
          </div>
        </header>

        {/* Page content with route transition */}
        <main className="flex-1 overflow-y-auto bg-gray-950">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={pageTransition.initial}
              animate={pageTransition.animate}
              exit={pageTransition.exit}
              transition={pageTransition.transition}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};
