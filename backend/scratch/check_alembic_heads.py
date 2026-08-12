import glob
import ast

files = sorted(glob.glob("alembic/versions/*.py"))
revs = {}
down_revs = {}

for f in files:
    try:
        tree = ast.parse(open(f, encoding="utf-8").read(), filename=f)
        rev_id = None
        down_id = None
        for stmt in tree.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if stmt.target.id == "revision" and isinstance(stmt.value, ast.Constant):
                    rev_id = stmt.value.value
                elif stmt.target.id == "down_revision" and isinstance(stmt.value, ast.Constant):
                    down_id = stmt.value.value
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "revision" and isinstance(stmt.value, ast.Constant):
                            rev_id = stmt.value.value
                        elif target.id == "down_revision" and isinstance(stmt.value, ast.Constant):
                            down_id = stmt.value.value
        
        if rev_id:
            revs[rev_id] = f
            down_revs[rev_id] = down_id
            print(f"{f:65s} | revision='{rev_id}' | down_revision='{down_id}'")
        else:
            print(f"WARNING: Could not parse revision from {f}")
    except Exception as e:
        print(f"ERROR parsing {f}: {e}")

all_revs = set(revs.keys())
all_downs = set(d for d in down_revs.values() if d)
heads = all_revs - all_downs
print("\nHEADS FOUND:", heads)

# Also check for duplicate revisions
rev_counts = {}
for r in revs.keys():
    rev_counts[r] = rev_counts.get(r, 0) + 1
print("DUPLICATE REVISIONS:", [r for r, c in rev_counts.items() if c > 1])
