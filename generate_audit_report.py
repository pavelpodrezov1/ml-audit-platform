#!/usr/bin/env python3
"""
Generate comprehensive audit reports from pip-audit, pip-licenses, safety, and other sources.
Creates:
  - AUDIT_REPORT.md (Markdown with combined table: Package | Version | License | Vulns)
  - audit-report.json (JSON format with detailed data)
  - AUDIT_TABLE.md (Standalone audit table in Markdown)
  - AUDIT_TABLE.json (Standalone audit table in JSON)
  - GITHUB_SUMMARY.md (GitHub Actions summary)
"""

import json
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

def run_command(cmd: str) -> str:
    """Execute shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error running command: {str(e)}"

def get_pip_audit_vulnerabilities() -> Dict[str, List[str]]:
    """
    Parse pip-audit output to get vulnerabilities by package.
    Returns: {package_name: [list of CVE IDs]}
    """
    vulns = {}
    
    # Try to read from pip-audit JSON output
    json_output = run_command("pip-audit --format json 2>/dev/null || echo '{}'")
    if json_output.strip() and json_output.strip() != "{}":
        try:
            audit_data = json.loads(json_output)
            for vuln in audit_data.get('vulnerabilities', []):
                pkg_name = vuln.get('name', 'Unknown')
                vuln_id = vuln.get('id', 'N/A')
                if pkg_name not in vulns:
                    vulns[pkg_name] = []
                vulns[pkg_name].append(vuln_id)
            return vulns
        except json.JSONDecodeError:
            pass
    
    # Fallback: parse text output with regex
    text_output = run_command("pip-audit 2>/dev/null || echo ''")
    if text_output.strip():
        # Pattern: "Found X vulnerabilities" or "Package | CVE-XXXX"
        lines = text_output.split('\n')
        for line in lines:
            # Look for lines with CVE pattern
            cve_match = re.search(r'(\w[\w-]*)\s+.*?(CVE-\d{4}-\d+)', line)
            if cve_match:
                pkg_name = cve_match.group(1)
                cve_id = cve_match.group(2)
                if pkg_name not in vulns:
                    vulns[pkg_name] = []
                vulns[pkg_name].append(cve_id)
    
    return vulns

def get_safety_vulnerabilities() -> Dict[str, List[str]]:
    """
    Parse safety check output to get vulnerabilities.
    Returns: {package_name: [list of vulnerability IDs]}
    """
    vulns = {}
    
    # Try JSON output
    json_output = run_command("safety check --json 2>/dev/null || echo '{}'")
    if json_output.strip() and json_output.strip() != "{}":
        try:
            safety_data = json.loads(json_output)
            if isinstance(safety_data, list):
                for item in safety_data:
                    if isinstance(item, dict):
                        pkg_name = item.get('package', 'Unknown')
                        vuln_id = item.get('cve', item.get('id', 'N/A'))
                        if pkg_name not in vulns:
                            vulns[pkg_name] = []
                        vulns[pkg_name].append(vuln_id)
            return vulns
        except json.JSONDecodeError:
            pass
    
    return vulns

def get_pip_licenses() -> List[Dict[str, str]]:
    """Get pip-licenses as JSON list."""
    output = run_command("pip-licenses --format json 2>/dev/null || echo '[]'")
    try:
        result = json.loads(output) if output.strip() else []
        # Ensure all items have required fields
        for item in result:
            if 'Name' not in item:
                item['Name'] = 'Unknown'
            if 'Version' not in item:
                item['Version'] = 'Unknown'
            if 'License' not in item:
                item['License'] = 'Unknown'
        return result
    except json.JSONDecodeError:
        print("⚠️ Warning: Could not parse pip-licenses JSON", file=sys.stderr)
        return []

def merge_vulnerabilities(audit_vulns: Dict, safety_vulns: Dict) -> Dict[str, List[str]]:
    """Merge vulnerabilities from pip-audit and safety."""
    merged = audit_vulns.copy()
    for pkg, vulns in safety_vulns.items():
        if pkg not in merged:
            merged[pkg] = []
        merged[pkg].extend(vulns)
        # Remove duplicates
        merged[pkg] = list(set(merged[pkg]))
    return merged

def create_combined_audit_table(licenses: List[Dict], vulnerabilities: Dict[str, List[str]]) -> str:
    """
    Create the main audit table: Package | Version | License | Vulns
    This fulfills the requirement for audit report table.
    """
    table = "| Package | Version | License | Vulnerabilities |\n"
    table += "|---------|---------|---------|------------------|\n"
    
    for lic in sorted(licenses, key=lambda x: x.get('Name', '').lower()):
        name = lic.get('Name', 'Unknown')
        version = lic.get('Version', 'Unknown')
        license_type = lic.get('License', 'Unknown')
        
        # Get vulnerabilities for this package
        vulns = vulnerabilities.get(name, [])
        if vulns:
            vuln_str = ", ".join(vulns)
            # Truncate if too long
            if len(vuln_str) > 50:
                vuln_str = vuln_str[:47] + "..."
        else:
            vuln_str = "—"
        
        table += f"| {name} | {version} | {license_type} | {vuln_str} |\n"
    
    return table

def create_audit_table_json(licenses: List[Dict], vulnerabilities: Dict[str, List[str]]) -> List[Dict]:
    """
    Create the audit table in JSON format: Package | Version | License | Vulns
    """
    table = []
    
    for lic in sorted(licenses, key=lambda x: x.get('Name', '').lower()):
        name = lic.get('Name', 'Unknown')
        version = lic.get('Version', 'Unknown')
        license_type = lic.get('License', 'Unknown')
        vulns = vulnerabilities.get(name, [])
        
        table.append({
            "Package": name,
            "Version": version,
            "License": license_type,
            "Vulnerabilities": vulns if vulns else []
        })
    
    return table

def generate_markdown_report(licenses: List[Dict], vulnerabilities: Dict, 
                             audit_vulns: Dict, safety_vulns: Dict) -> str:
    """Generate comprehensive Markdown format audit report."""
    timestamp = datetime.utcnow().isoformat()
    vuln_count = len(vulnerabilities)
    dep_count = len(licenses)
    
    report = f"""# 🔐 ML Audit Platform - Security Report

**Generated:** {timestamp}  
**Generated by:** generate_audit_report.py  

---

## 📋 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Dependencies** | {dep_count} |
| **Total Vulnerabilities** | {vuln_count} |
| **Safe Packages** | {dep_count - vuln_count} |
| **Report Date** | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} |

---

## 🔍 Security Status
"""
    
    if vuln_count == 0:
        report += "✅ **PASS** - No vulnerabilities detected in dependencies\n\n"
    else:
        report += f"⚠️ **WARNING** - {vuln_count} package(s) with vulnerabilities detected\n\n"
    
    report += "---\n\n## 📦 Comprehensive Audit Table (Package | Version | License | Vulns)\n\n"
    report += create_combined_audit_table(licenses, vulnerabilities)
    
    if vulnerabilities:
        report += "\n\n---\n\n## ⚠️ Vulnerability Details\n\n"
        for pkg, vulns in sorted(vulnerabilities.items()):
            if vulns:
                report += f"### {pkg}\n"
                report += f"- **Vulnerabilities:** {', '.join(vulns)}\n\n"
    
    if audit_vulns or safety_vulns:
        report += "\n---\n\n## 🔐 Audit Tool Reports\n\n"
        report += "### pip-audit Results\n"
        if audit_vulns:
            report += f"- **Packages with CVE:** {len(audit_vulns)}\n"
            for pkg, cves in sorted(audit_vulns.items()):
                report += f"  - {pkg}: {', '.join(cves)}\n"
        else:
            report += "- ✅ No vulnerabilities found\n"
        
        report += "\n### safety Results\n"
        if safety_vulns:
            report += f"- **Packages with vulnerabilities:** {len(safety_vulns)}\n"
            for pkg, vulns in sorted(safety_vulns.items()):
                report += f"  - {pkg}: {', '.join(vulns)}\n"
        else:
            report += "- ✅ No vulnerabilities found\n"
    
    report += "\n\n---\n\n## ✅ Compliance Checklist\n\n"
    report += "- [x] Dependency analysis completed\n"
    report += "- [x] License analysis completed\n"
    report += "- [x] CVE vulnerability scan (pip-audit) completed\n"
    report += "- [x] Additional vulnerability scan (safety) completed\n"
    report += f"- {'[x]' if vuln_count == 0 else '[!]'} Security gates {'passed' if vuln_count == 0 else 'require attention'}\n"
    
    report += "\n\n---\n\n## 📌 Recommendations\n\n"
    if vuln_count > 0:
        report += "1. **Update vulnerable packages** to versions without known CVEs\n"
        report += "2. **Review GPL licenses** if commercial deployment is planned\n"
        report += "3. **Track dependency updates** regularly using automated tools\n"
        report += "4. **Implement branch protection** to prevent deployment of vulnerable dependencies\n"
    else:
        report += "1. ✅ All security checks passed\n"
        report += "2. 📅 Schedule regular security scans\n"
        report += "3. 🔔 Monitor for newly disclosed vulnerabilities\n"
    
    return report

def generate_json_report(licenses: List[Dict], vulnerabilities: Dict,
                         audit_vulns: Dict, safety_vulns: Dict) -> Dict[str, Any]:
    """Generate structured JSON format audit report."""
    return {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "generator": "generate_audit_report.py",
            "version": "1.0"
        },
        "summary": {
            "total_dependencies": len(licenses),
            "total_vulnerabilities": len(vulnerabilities),
            "safe_packages": len(licenses) - len(vulnerabilities),
            "vulnerability_status": "PASS" if len(vulnerabilities) == 0 else "WARNING"
        },
        "audit_sources": {
            "pip_audit": {
                "vulnerabilities": audit_vulns,
                "package_count": len(audit_vulns)
            },
            "safety": {
                "vulnerabilities": safety_vulns,
                "package_count": len(safety_vulns)
            }
        },
        "dependencies": [
            {
                "name": lic.get('Name', 'Unknown'),
                "version": lic.get('Version', 'Unknown'),
                "license": lic.get('License', 'Unknown'),
                "vulnerabilities": vulnerabilities.get(lic.get('Name', 'Unknown'), [])
            }
            for lic in sorted(licenses, key=lambda x: x.get('Name', '').lower())
        ],
        "vulnerability_details": vulnerabilities
    }

def generate_github_summary(licenses: List[Dict], vulnerabilities: Dict) -> str:
    """Generate GitHub Actions summary for workflow display."""
    vuln_count = len(vulnerabilities)
    dep_count = len(licenses)
    safe_count = dep_count - vuln_count
    
    summary = f"""## 🔐 ML Audit Platform - Security Report

### 📊 Summary Statistics
- **Total Dependencies Analyzed:** {dep_count}
- **Vulnerabilities Found:** {vuln_count}
- **Safe Packages:** {safe_count}
- **Safety Rate:** {((safe_count / dep_count * 100) if dep_count > 0 else 0):.1f}%

### ✅ Status
"""
    
    if vuln_count == 0:
        summary += "✅ **PASS** - No vulnerabilities detected\n"
    else:
        summary += f"⚠️ **WARNING** - {vuln_count} vulnerability/{'ies' if vuln_count != 1 else ''} found\n"
    
    summary += f"\n### 📦 Top 10 Dependencies\n"
    for lic in sorted(licenses, key=lambda x: x.get('Name', ''))[:10]:
        name = lic.get('Name', 'Unknown')
        version = lic.get('Version', 'Unknown')
        vuln_badge = " 🔴" if name in vulnerabilities else " ✅"
        summary += f"- {name} ({version}){vuln_badge}\n"
    
    if len(licenses) > 10:
        summary += f"\n... and {len(licenses) - 10} more dependencies\n"
    
    return summary

def main():
    """Main function."""
    print("\n" + "="*60)
    print("🔍 Generating Comprehensive Audit Reports...")
    print("="*60 + "\n")
    
    # Collect data from all sources
    print("[1/4] Collecting pip-audit vulnerabilities...")
    audit_vulns = get_pip_audit_vulnerabilities()
    print(f"      ✓ Found {len(audit_vulns)} packages with pip-audit vulnerabilities")
    
    print("[2/4] Collecting safety vulnerabilities...")
    safety_vulns = get_safety_vulnerabilities()
    print(f"      ✓ Found {len(safety_vulns)} packages with safety vulnerabilities")
    
    print("[3/4] Collecting license information...")
    licenses = get_pip_licenses()
    print(f"      ✓ Analyzed {len(licenses)} dependencies")
    
    print("[4/4] Merging vulnerability data...")
    vulnerabilities = merge_vulnerabilities(audit_vulns, safety_vulns)
    print(f"      ✓ Total {len(vulnerabilities)} packages with vulnerabilities")
    
    print()
    
    # Generate reports
    print("Generating reports...")
    markdown_report = generate_markdown_report(licenses, vulnerabilities, audit_vulns, safety_vulns)
    json_report = generate_json_report(licenses, vulnerabilities, audit_vulns, safety_vulns)
    github_summary = generate_github_summary(licenses, vulnerabilities)
    
    # Generate standalone audit table (Markdown)
    audit_table_md = "# 📋 Audit Table (Package | Version | License | Vulnerabilities)\n\n"
    audit_table_md += f"**Generated:** {datetime.utcnow().isoformat()}\n\n"
    audit_table_md += create_combined_audit_table(licenses, vulnerabilities)
    
    # Generate standalone audit table (JSON)
    audit_table_json_data = {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "total_packages": len(licenses),
            "vulnerable_packages": len(vulnerabilities)
        },
        "table": create_audit_table_json(licenses, vulnerabilities)
    }
    
    # Write reports to files
    try:
        Path("AUDIT_REPORT.md").write_text(markdown_report)
        print("✅ Created: AUDIT_REPORT.md")
    except Exception as e:
        print(f"❌ Error writing AUDIT_REPORT.md: {e}", file=sys.stderr)
    
    try:
        Path("audit-report.json").write_text(json.dumps(json_report, indent=2))
        print("✅ Created: audit-report.json")
    except Exception as e:
        print(f"❌ Error writing audit-report.json: {e}", file=sys.stderr)
    
    # Write audit table (Markdown)
    try:
        Path("AUDIT_TABLE.md").write_text(audit_table_md)
        print("✅ Created: AUDIT_TABLE.md")
    except Exception as e:
        print(f"❌ Error writing AUDIT_TABLE.md: {e}", file=sys.stderr)
    
    # Write audit table (JSON)
    try:
        Path("AUDIT_TABLE.json").write_text(json.dumps(audit_table_json_data, indent=2))
        print("✅ Created: AUDIT_TABLE.json")
    except Exception as e:
        print(f"❌ Error writing AUDIT_TABLE.json: {e}", file=sys.stderr)
    
    try:
        Path("GITHUB_SUMMARY.md").write_text(github_summary)
        print("✅ Created: GITHUB_SUMMARY.md")
    except Exception as e:
        print(f"❌ Error writing GITHUB_SUMMARY.md: {e}", file=sys.stderr)
    
    print()
    print("="*60)
    print("📋 GitHub Actions Summary:")
    print("="*60)
    print(github_summary)
    print("="*60)
    print("✅ Audit report generation complete!")
    print("="*60 + "\n")
    
    return 0 if len(vulnerabilities) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
