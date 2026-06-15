"""Wipe all data that was inserted by seed_demo.py.

Reads the `_demo_data_ids` tracking table, deletes the rows it points at,
then drops the tracking table itself. Safe to run twice.

Note: Drupal users created by `seed_demo.py` (drush user:create) are NOT
removed automatically — delete them via Drupal admin if you want them gone:
    drush user:cancel <username>
"""
from db import query

TABLE_ORDER = [
    # Delete child rows first to satisfy FK constraints
    "anomaly_flags",
    "checkins",
    "planned_visit_items",
    "planned_visits",
    "employees",
]


def has_tracking_table():
    rows, _ = query(
        """
        SELECT COUNT(*) AS n FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name = '_demo_data_ids'
        """
    )
    return rows[0]["n"] > 0


def main():
    if not has_tracking_table():
        print("No _demo_data_ids table found — nothing to remove.")
        return

    deleted = {}
    for table in TABLE_ORDER:
        rows, _ = query(
            "SELECT row_id FROM _demo_data_ids WHERE table_name=%s",
            (table,),
        )
        ids = [r["row_id"] for r in (rows or [])]
        if not ids:
            deleted[table] = 0
            continue
        # Delete in chunks to keep query size sane
        n = 0
        for i in range(0, len(ids), 100):
            chunk = ids[i : i + 100]
            placeholders = ",".join(["%s"] * len(chunk))
            _, _ = query(
                f"DELETE FROM {table} WHERE id IN ({placeholders})",
                tuple(chunk),
                fetch=False,
                commit=True,
            )
            n += len(chunk)
        deleted[table] = n

    # Drop the tracking table last
    query("DROP TABLE _demo_data_ids", fetch=False, commit=True)

    print("Demo data removed:")
    for table, n in deleted.items():
        print(f"  {table}: {n} row(s)")
    print("Dropped tracking table _demo_data_ids.")
    print("Note: Drupal user accounts (demo_priya etc.) were NOT touched.")
    print("      Remove with: drush user:cancel <username>  — if you want them gone.")


if __name__ == "__main__":
    main()
