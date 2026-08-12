import os
import glob

services_dir = r"c:\Users\anthg\OneDrive\Escritorio\proyecto tesis\autenticacion-continua\backend\app\modules\logistics\files\application\services"

for fpath in glob.glob(os.path.join(services_dir, "*.py")):
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = content.replace("entity_type=", "resource_type=")
    new_content = new_content.replace("entity_id=", "resource_id=")
    new_content = new_content.replace("details=", "payload=")
    
    if new_content != content:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(fpath)}")

print("Done updating AuditEventCommand arguments.")
