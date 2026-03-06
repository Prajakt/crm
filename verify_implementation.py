#!/usr/bin/env python3
"""
Verification script for CRM Project implementation.
Checks if all files and changes are in place.
"""

import os
import json
from pathlib import Path


def check_file_exists(path, description):
    """Check if a file exists"""
    if os.path.exists(path):
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description} MISSING: {path}")
        return False


def check_json_field(path, field_name, description):
    """Check if a field exists in a JSON file"""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            fields = data.get('fields', [])
            for field in fields:
                if field.get('fieldname') == field_name:
                    print(f"✓ {description}: {field_name} in {os.path.basename(path)}")
                    return True
            print(f"✗ {description} MISSING: {field_name} in {os.path.basename(path)}")
            return False
    except Exception as e:
        print(f"✗ Error reading {path}: {e}")
        return False


def main():
    print("=" * 70)
    print("CRM PROJECT IMPLEMENTATION VERIFICATION")
    print("=" * 70)
    print()

    base_path = os.path.dirname(os.path.abspath(__file__))
    results = []

    # Phase 1: Core DocTypes
    print("\n📦 PHASE 1: CORE DOCTYPES")
    print("-" * 70)

    results.append(check_file_exists(
        os.path.join(base_path, "crm/fcrm/doctype/crm_project/crm_project.json"),
        "CRM Project DocType JSON"
    ))

    results.append(check_file_exists(
        os.path.join(base_path, "crm/fcrm/doctype/crm_project/crm_project.py"),
        "CRM Project Controller"
    ))

    results.append(check_file_exists(
        os.path.join(base_path, "crm/fcrm/doctype/crm_project_member/crm_project_member.json"),
        "CRM Project Member DocType JSON"
    ))

    results.append(check_file_exists(
        os.path.join(base_path, "crm/fcrm/doctype/crm_project_member/crm_project_member.py"),
        "CRM Project Member Controller"
    ))

    # Phase 1: API Endpoints
    print("\n🔌 PHASE 1: API ENDPOINTS")
    print("-" * 70)

    results.append(check_file_exists(
        os.path.join(base_path, "crm/api/project.py"),
        "Project API Module"
    ))

    # Phase 2: Custom Fields
    print("\n🏗️  PHASE 2: CUSTOM FIELDS")
    print("-" * 70)

    results.append(check_file_exists(
        os.path.join(base_path, "crm/patches/v1_0/add_project_fields_to_core_doctypes.py"),
        "Custom Fields Patch"
    ))

    # Phase 2: Controller Modifications
    print("\n🔧 PHASE 2: CONTROLLER MODIFICATIONS")
    print("-" * 70)

    # Check if auto_assign_project method exists in controllers
    controllers = [
        ("crm/fcrm/doctype/crm_lead/crm_lead.py", "CRM Lead"),
        ("crm/fcrm/doctype/crm_deal/crm_deal.py", "CRM Deal"),
        ("crm/fcrm/doctype/crm_task/crm_task.py", "CRM Task"),
        ("crm/fcrm/doctype/crm_organization/crm_organization.py", "CRM Organization"),
    ]

    for controller_path, name in controllers:
        full_path = os.path.join(base_path, controller_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read()
                if 'auto_assign_project' in content:
                    print(f"✓ {name} has auto_assign_project method")
                    results.append(True)
                else:
                    print(f"✗ {name} MISSING auto_assign_project method")
                    results.append(False)
        else:
            print(f"✗ {name} controller not found")
            results.append(False)

    # Phase 3: Permissions
    print("\n🔐 PHASE 3: PERMISSIONS")
    print("-" * 70)

    results.append(check_file_exists(
        os.path.join(base_path, "crm/permissions.py"),
        "Permissions Module"
    ))

    # Check hooks.py
    hooks_path = os.path.join(base_path, "crm/hooks.py")
    if os.path.exists(hooks_path):
        with open(hooks_path, 'r') as f:
            content = f.read()
            if 'permission_query_conditions' in content and 'crm.permissions' in content:
                print(f"✓ Hooks configured for permissions")
                results.append(True)
            else:
                print(f"✗ Hooks NOT configured for permissions")
                results.append(False)
    else:
        print(f"✗ hooks.py not found")
        results.append(False)

    # Phase 4: Project-Specific Schemas
    print("\n📋 PHASE 4: PROJECT-SPECIFIC SCHEMAS")
    print("-" * 70)

    results.append(check_json_field(
        os.path.join(base_path, "crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.json"),
        "project",
        "Project field in CRM Fields Layout"
    ))

    # Check if get_fields_layout supports project parameter
    layout_controller = os.path.join(base_path, "crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py")
    if os.path.exists(layout_controller):
        with open(layout_controller, 'r') as f:
            content = f.read()
            if 'project: str | None = None' in content:
                print(f"✓ get_fields_layout supports project parameter")
                results.append(True)
            else:
                print(f"✗ get_fields_layout MISSING project parameter")
                results.append(False)
    else:
        print(f"✗ Fields Layout controller not found")
        results.append(False)

    # Phase 5 & 6: Enhanced APIs
    print("\n🚀 PHASE 5 & 6: ENHANCED APIs")
    print("-" * 70)

    # Check if new API functions exist
    api_file = os.path.join(base_path, "crm/api/project.py")
    if os.path.exists(api_file):
        with open(api_file, 'r') as f:
            content = f.read()

            api_functions = [
                'get_project_dashboard',
                'get_all_projects',
                'add_team_member',
                'remove_team_member',
                'update_team_member_role',
                'get_project_activity',
                'get_project_reports',
                'get_project_settings',
                'update_project_settings',
                'copy_project_layout',
            ]

            for func in api_functions:
                if f'def {func}' in content:
                    print(f"✓ API function: {func}")
                    results.append(True)
                else:
                    print(f"✗ API function MISSING: {func}")
                    results.append(False)
    else:
        print(f"✗ Project API file not found")
        results.extend([False] * 10)

    # Documentation
    print("\n📚 DOCUMENTATION")
    print("-" * 70)

    docs = [
        "PROJECT_ARCHITECTURE.md",
        "PHASE_1_IMPLEMENTATION.md",
        "PHASE_2_IMPLEMENTATION.md",
        "PHASE_3_IMPLEMENTATION.md",
        "PHASE_4_5_6_IMPLEMENTATION.md",
        "TESTING_GUIDE.md"
    ]

    for doc in docs:
        results.append(check_file_exists(
            os.path.join(base_path, doc),
            f"Documentation: {doc}"
        ))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\nTotal Checks: {total}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")

    if failed == 0:
        print("\n🎉 ALL CHECKS PASSED! Implementation is complete.")
        print("\nNext steps:")
        print("1. Install this app in a Frappe bench")
        print("2. Run: bench --site [site] migrate")
        print("3. Follow TESTING_GUIDE.md for functional testing")
        return 0
    else:
        print(f"\n⚠️  {failed} check(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
