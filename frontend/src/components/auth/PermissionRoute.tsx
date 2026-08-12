import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { permissionsFor, type Permissions } from '../../utils/permissions'

export function PermissionRoute({ permission }: { permission: keyof Permissions }) {
  const { user } = useAuth()
  if (!user || !permissionsFor(user.role)[permission]) {
    return <Navigate to="/unauthorized" replace />
  }
  return <Outlet />
}
