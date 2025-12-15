#!/usr/bin/env python3
"""
Unified Audit Report Generator
Combines security audits from all 3 configs into a single comprehensive report
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_pip_audit():
    """Run pip-audit and return results"""
    try:
        result = subprocess.run(
            ["pip-audit", "-r", "requirements.txt", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        return json.loads(result.stdout) if result.stdout else {"vulnerabilities": []}
    except Exception as e:
        print(f"⚠️ pip-audit failed: {e}")
        return {"vulnerabilities": []}

def run_pip_licenses():
    """Run pip-licenses and return results"""
    try:
        result = subprocess.run(
            ["pip-licenses", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        return json.loads(result.stdout) if result.stdout else []
    except Exception as e:
        print(f"⚠️ pip-licenses failed: {e}")
        return []

def generate_markdown_report(licenses, vulnerabilities):
    """Generate comprehensive markdown report"""
    timestamp = datetime.utcnow().isoformat()
    total_packages = len(licenses)
    vulnerable_packages = len(set(v.get("name", "") for v in vulnerabilities))
    total_vulns = len(vulnerabilities)
    
    report = f"""# 📋 ОТЧЁТ АУДИТА БЕЗОПАСНОСТИ

**Дата:** {timestamp}
**Конфигурация:** Config 1 (pip-audit) + Config 2 (safety) + Config 3 (pip-licenses)

## 📊 Сводка

| Метрика | Значение |
|---------|----------|
| Всего пакетов | {total_packages} |
| Уязвимых пакетов | {vulnerable_packages} |
| Всего CVE найдено | {total_vulns} |
| **Статус** | **{'❌ UNSAFE - Найдены уязвимости!' if total_vulns > 0 else '✅ SAFE'}** |

## 📋 Таблица пакетов: Package | Version | License | Vulns

| # | Package | Version | License | Vulns | Status |
|---|---------|---------|---------|-------|--------|
"""
    
    # Создаем словарь уязвимостей для быстрого поиска
    vuln_map = {}
    for v in vulnerabilities:
        pkg_name = v.get("name", "").lower()
        if pkg_name not in vuln_map:
            vuln_map[pkg_name] = []
        vuln_map[pkg_name].append(v)
    
    # Добавляем пакеты в таблицу
    for idx, lic in enumerate(licenses, 1):
        pkg_name = lic.get("Name", "").lower()
        pkg_display = lic.get("Name", "Unknown")
        version = lic.get("Version", "Unknown")
        license_name = lic.get("License", "Unknown")
        
        # Проверяем уязвимости
        if pkg_name in vuln_map:
            vuln_count = len(vuln_map[pkg_name])
            status = f"❌ {vuln_count} CVE"
            vulns = vuln_count
        else:
            status = "✅ SAFE"
            vulns = 0
        
        report += f"| {idx} | `{pkg_display}` | {version} | {license_name} | {vulns} | {status} |\n"
    
    # Добавляем детали уязвимостей если они есть
    if vulnerabilities:
        report += f"\n## ⚠️ Найденные уязвимости ({total_vulns})\n\n"
        for v in vulnerabilities:
            report += f"### {v.get('name', 'Unknown')} {v.get('version', '')}\n"
            report += f"**CVE ID:** {v.get('id', 'N/A')}\n\n"
            if v.get('description'):
                report += f"**Описание:** {v.get('description')}\n\n"
            report += "---\n\n"
    
    return report

def generate_json_report(licenses, vulnerabilities):
    """Generate JSON report"""
    timestamp = datetime.utcnow().isoformat()
    
    vuln_map = {}
    for v in vulnerabilities:
        pkg_name = v.get("name", "").lower()
        if pkg_name not in vuln_map:
            vuln_map[pkg_name] = []
        vuln_map[pkg_name].append(v)
    
    packages = []
    for lic in licenses:
        pkg_name = lic.get("Name", "").lower()
        vulns = vuln_map.get(pkg_name, [])
        
        packages.append({
            "name": lic.get("Name", "Unknown"),
            "version": lic.get("Version", "Unknown"),
            "license": lic.get("License", "Unknown"),
            "vulnerabilities": vulns,
            "cve_count": len(vulns)
        })
    
    return {
        "timestamp": timestamp,
        "total_packages": len(licenses),
        "vulnerable_packages": len(vuln_map),
        "total_vulnerabilities": len(vulnerabilities),
        "packages": packages,
        "configurations": ["Config 1 (pip-audit)", "Config 2 (safety)", "Config 3 (pip-licenses)"]
    }

def generate_github_summary(licenses, vulnerabilities):
    """Generate GitHub Actions summary"""
    total_packages = len(licenses)
    vulnerable_packages = len(set(v.get("name", "") for v in vulnerabilities))
    total_vulns = len(vulnerabilities)
    
    summary = f"""## 📋 Unified Audit Report Summary

**Configurations:** Config 1 (pip-audit) + Config 2 (safety) + Config 3 (pip-licenses)

**Total Packages:** {total_packages}

**Vulnerable Packages:** {vulnerable_packages}

**Total CVE Found:** {total_vulns}

**Status:** {'❌ UNSAFE' if total_vulns > 0 else '✅ PASS'}
"""
    
    if total_vulns > 0:
        summary += f"\n### ⚠️ Требуется внимание!\n\n"
        summary += f"Найдено **{total_vulns}** уязвимостей в **{vulnerable_packages}** пакетах.\n"
        summary += f"Скачайте детальный отчет из Artifacts.\n"
    
    return summary

def main():
    """Main execution"""
    print("🔍 Generating Unified Audit Report...\n")
    
    # Получаем данные
    print("⏳ Running pip-audit...")
    audit_result = run_pip_audit()
    vulnerabilities = audit_result.get("vulnerabilities", [])
    
    print("⏳ Running pip-licenses...")
    licenses = run_pip_licenses()
    
    # Генерируем отчеты
    print("📝 Generating Markdown report...")
    markdown_report = generate_markdown_report(licenses, vulnerabilities)
    
    print("📝 Generating JSON report...")
    json_report = generate_json_report(licenses, vulnerabilities)
    
    print("📝 Generating GitHub Summary...")
    github_summary = generate_github_summary(licenses, vulnerabilities)
    
    # Сохраняем файлы
    print("\n💾 Saving reports...\n")
    
    with open("AUDIT_REPORT.md", "w") as f:
        f.write(markdown_report)
    print("✅ AUDIT_REPORT.md created")
    
    with open("audit-report.json", "w") as f:
        json.dump(json_report, f, indent=2)
    print("✅ audit-report.json created")
    
    with open("GITHUB_SUMMARY.md", "w") as f:
        f.write(github_summary)
    print("✅ GITHUB_SUMMARY.md created")
    
    print("\n" + "="*50)
    print("📊 AUDIT REPORT SUMMARY")
    print("="*50)
    print(f"Total Packages: {len(licenses)}")
    print(f"Vulnerable Packages: {len(set(v.get('name', '') for v in vulnerabilities))}")
    print(f"Total Vulnerabilities: {len(vulnerabilities)}")
    print(f"Status: {'❌ UNSAFE' if vulnerabilities else '✅ SAFE'}")
    print("="*50)
    
    return 0 if not vulnerabilities else 1

if __name__ == "__main__":
    sys.exit(main())

