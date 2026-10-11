"""Automated unit & integration test for File Organizer."""

from pathlib import Path
from backend.demo_generator import create_demo_sandbox, DEMO_DIR
from backend.scanner import DirectoryScanner
from backend.organizer import FileOrganizer, rollback_batch
from backend.database import get_all_batches, get_custom_rules, add_custom_rule, delete_custom_rule

def test_full_pipeline():
    print("1. Creating Demo Sandbox...")
    demo = create_demo_sandbox()
    assert demo["success"] == True
    print(f"   Created {demo['total_files']} files.")

    print("2. Testing DirectoryScanner...")
    scanner = DirectoryScanner(DEMO_DIR)
    scan_res = scanner.scan(detect_duplicates=True)
    print(f"   Found {scan_res['total_files']} files, {scan_res['duplicates_count']} duplicates.")
    assert scan_res['total_files'] > 0
    assert scan_res['duplicates_count'] > 0

    print("3. Testing Preview / Simulation...")
    organizer = FileOrganizer(DEMO_DIR)
    preview = organizer.preview()
    print(f"   Planned {len(preview['planned_moves'])} moves.")
    assert len(preview['planned_moves']) == scan_res['total_files']

    print("4. Testing Live Execution...")
    exec_res = organizer.execute()
    batch_id = exec_res["batch_id"]
    moved_count = exec_res["summary"]["moved_files"]
    print(f"   Batch {batch_id}: Successfully moved {moved_count} files.")
    assert moved_count > 0

    print("5. Testing 1-Click Rollback...")
    rb_res = rollback_batch(batch_id)
    print(f"   Rollback status: {rb_res['success']}, restored {rb_res['restored_files']} files.")
    assert rb_res["success"] == True
    assert rb_res["restored_files"] == moved_count

    print("6. Testing Custom Rules Engine...")
    rule_id = add_custom_rule("Tax Docs", "keyword", "tax", "Finance/Taxes", priority=5)
    rules = get_custom_rules()
    assert any(r["id"] == rule_id for r in rules)
    delete_custom_rule(rule_id)
    print("   Custom rules added and verified.")

    print("\n All End-to-End Tests Passed Successfully!")

if __name__ == "__main__":
    test_full_pipeline()
