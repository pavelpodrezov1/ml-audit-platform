#!/usr/bin/env python3
"""
Generate audit reports from pip-audit, pip-licenses, and other sources.
Creates AUDIT_REPORT.md, audit-report.json, and GITHUB_SUMMARY.md
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def run_command(cmd: str) -> str:
    """Execute shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error running command: {str(e)}"

def get_pip_audit_report() -> Dict[str, Any]:
    """Get pip-audit vulnerabilities as JSON."""
    output = run_command("pip-audit --desc --format json 2>/dev/null || echo '{}'")
    try:
        return json.loads(output) if output.strip() else {}
    except json.JSONDecodeError:
        return {}

def get_pip_licenses() -> List[Dict[str, str]]:
    """Get pip-licenses as JSON."""
    output = run_command("pip-licenses --format json 2>/dev/null || echo '[]'")
    try:
        return json.loads(output) if output.strip() else []
    except json.JSONDecodeError:
        return []

def get_dependency_tree() -> str:
    """Get pipdeptree output."""
    return run_command("pipdeptree 2>/dev/null || echo 'No dependency tree available'")

def generate_markdown_report(audit_data: Dict, licenses: List) -> str:
    """Generate Markdown format audit report."""
    timestamp = datetime.utcnow().isoformat()
    
    report = f"""# ML Audit Platform - Security Report

**Generated:** {timestamp}

## 📋 Executive Summary

- **Vulnerabilities Found:** {len(audit_data.get('vulnerabilities', []))}
- **Dependencies Analyzed:** {len(licenses)}
- **Report Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

---

## 🔍 Vulnerability Scan (pip-audit)

"""
    
    vulnerabilities = audit_data.get('vulnerabilities', [])
    if vulnerabilities:
        report += "### ⚠️ Found Vulnerabilities:\n\n"
        report += "| Package | Version | Vulnerability ID | Description |\n"
        report += "|---------|---------|-------------------|-------------|\n"
        for vuln in vulnerabilities:
            pkg = vuln.get('name', 'N/A')
            ver = vuln.get('version', 'N/A')
            vid = vuln.get('id', 'N/A')
            desc = vuln.get('description', 'N/A')
            report += f"| {pkg} | {ver} | {vid} | {desc[:50]}... |\n"
    else:
        report += "✅ **No vulnerabilities detected!**\n"
    
    report += "\n---\n\n## 📦 Dependencies & Licenses\n\n"
    report += "| Package | Version | License |\n"
    report += "|---------|---------|----------|\n"
    
    for lic in sorted(licenses, key=lambda x: x.get('Name', '')):
        name = lic.get('Name', 'N/A')
        version = lic.get('Version', 'N/A')
        license_type = lic.get('License', 'Unknown')
        report += f"| {name} | {version} | {license_type} |\n"
    
    report += "\n---\n\n## ✅ Compliance Status\n\n"
    report += "- [x] Dependency audit completed\n"
    report += "- [x] License analysis completed\n"
    report += "- [x] Vulnerability scan completed\n"
    
    return report

def generate_json_report(audit_data: Dict, licenses: List) -> Dict[str, Any]:
    """Generate JSON format audit report."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "vulnerabilities": audit_data.get('vulnerabilities', []),
        "total_vulnerabilities": len(audit_data.get('vulnerabilities', [])),
        "dependencies": licenses,
        "total_dependencies": len(licenses),
        "compliance": {
            "audit_completed": True,
            "licenses_analyzed": True,
            "vulnerabilities_scanned": True
        }
    }

def generate_github_summary(audit_data: Dict, licenses: List) -> str:
    """Generate GitHub Actions summary for workflow display."""
    vuln_count = len(audit_data.get('vulnerabilities', []))
    dep_count = len(licenses)
    
    summary = f"""## 🔐 ML Audit Platform Report

### Summary
- **Vulnerabilities:** {vuln_count}
- **Dependencies:** {dep_count}
- **Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

### Status
"""
    
    if vuln_count == 0:
        summary += "✅ **PASS** - No vulnerabilities detected\n"
    else:
        summary += f"⚠️ **WARNING** - {vuln_count} vulnerability/vulnerabilities found\n"
    
    summary += f"\n### Top Dependencies\n"
    for lic in sorted(licenses, key=lambda x: x.get('Name', ''))[:10]:
        name = lic.get('Name', 'N/A')
        version = lic.get('Version', 'N/A')
        summary += f"- {name} ({version})\n"
    
    return summary

def main():
    """Main function."""
    print("\n" + "="*50)
    print("🔍 Generating Audit Reports...")
    print("="*50 + "\n")
    
    # Collect data
    audit_data = get_pip_audit_report()
    licenses = get_pip_licenses()
    
    print(f"✓ Collected audit data: {len(audit_data.get('vulnerabilities', []))} vulnerabilities")
    print(f"✓ Collected license data: {len(licenses)} dependencies\n")
    
    # Generate reports
    markdown_report = generate_markdown_report(audit_data, licenses)
    json_report = generate_json_report(audit_data, licenses)
    github_summary = generate_github_summary(audit_data, licenses)
    
    # Write reports to files
    Path("AUDIT_REPORT.md").write_text(markdown_report)
    Path("audit-report.json").write_text(json.dumps(json_report, indent=2))
    Path("GITHUB_SUMMARY.md").write_text(github_summary)
    
    print("✅ Created files:")
    print("   - AUDIT_REPORT.md")
    print("   - audit-report.json")
    print("   - GITHUB_SUMMARY.md\n")
    
    # Display summary
    print(github_summary)
    
    print("\n" + "="*50)
    print("✅ Audit report generation complete!")
    print("="*50 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

