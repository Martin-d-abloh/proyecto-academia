import { Outlet } from "react-router-dom"

function Layout() {
  return (
    <div className="min-h-screen bg-gray-100 text-gray-800 font-sans">
      <main className="max-w-5xl mx-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
