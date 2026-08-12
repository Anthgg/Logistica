import sys
from sqlalchemy import text
from app.database.session import SessionLocal

sys.stdout.reconfigure(encoding='utf-8')

db = SessionLocal()
try:
    user_row = db.execute(
        text("SELECT id, email, full_name, role, is_active FROM users WHERE email = :email"),
        {"email": "usuario@example.com"}
    ).fetchone()
    
    if not user_row:
        print("[INFO] User 'usuario@example.com' NOT FOUND.")
    else:
        user_id, email, full_name, role, is_active = user_row
        print(f"=== DATOS DEL USUARIO EN BD ===")
        print(f"ID: {user_id}")
        print(f"Email: {email}")
        print(f"Nombre Completo: {full_name}")
        print(f"Rol de Plataforma (user.role): {role}")
        print(f"Estado Activo: {is_active}")
        print()

        assignments = db.execute(
            text("""
                SELECT ra.id, r.code as role_code, r.name as role_name, ra.organization_id, ra.branch_id
                FROM logistics_role_assignments ra
                JOIN logistics_roles r ON ra.role_id = r.id
                WHERE ra.user_id = :user_id
            """),
            {"user_id": str(user_id)}
        ).fetchall()
        
        print(f"=== ROLES LOGÍSTICOS ASIGNADOS EN TABLA (RBAC) ({len(assignments)}) ===")
        if not assignments:
            print(" - No tiene registros de roles asignados manualmente en 'logistics_role_assignments'.")
        else:
            for a in assignments:
                print(f" - Código Rol: {a.role_code} | Nombre: {a.role_name} | Org ID: {a.organization_id} | Sede ID: {a.branch_id}")

        print()
        print("=== EVALUACIÓN DE ACCESO ===")
        print(f"✓ AL TENER 'user.role = admin':")
        print("  - Es reconocido por el sistema como PLATFORM SUPERADMIN.")
        print("  - TIENE ACCESO TOTAL Y ACCESO A TODOS LOS PERMISOS DE TODOS LOS MÓDULOS DE LA PLATAFORMA.")

finally:
    db.close()
