// src/components/Sidebar.tsx
import { Home, Video, Settings } from 'lucide-react'
import { cn } from '~/lib/utils'
import { Button } from '~/components/ui/button'
import { Link, useLocation } from 'react-router'

const sidebarItems = [
  { icon: Home, label: 'Dashboard', path: '/' },
  { icon: Video, label: 'Videos', path: '/videos' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

export function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 border-r bg-gray-50/50 p-4">
      <div className="flex h-14 items-center px-4 font-semibold">
        AI Video Generator
      </div>
      <nav className="space-y-2">
        {sidebarItems.map((item) => (
          <Link key={item.path} to={item.path}>
            <Button
              variant="ghost"
              className={cn(
                'w-full justify-start',
                location.pathname === item.path && 'bg-gray-100'
              )}
            >
              <item.icon className="mr-2 h-4 w-4" />
              {item.label}
            </Button>
          </Link>
        ))}
      </nav>
    </div>
  )
}