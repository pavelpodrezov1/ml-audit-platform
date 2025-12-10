import subprocess
import json
import sys
from datetime import datetime

def run_command(cmd):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def audit_vulnerabilities():
    """Проверяет уязвимости с pip-audit"""
    print("\n" + "=" * 70)
    print("1. ПРОВЕРКА УЯЗВИМОСТЕЙ (pip-audit)")
    print("=" * 70)
    
    returncode, stdout, stderr = run_command("pip-audit -r requirements.txt --format json")
    
    if returncode == 0:
        print("✓ Уязвимостей не найдено")
        return True
    else:
        print("✗ Найдены уязвимости:")
        try:
            data = json.loads(stdout)
            for vuln in data.get('vulnerabilities', []):
                print(f"\n  Пакет: {vuln['name']} {vuln['installed_version']}")
                print(f"  Уязвимость: {vuln['id']}")
                print(f"  Описание: {vuln['description']}")
                print(f"  Зафиксировано в: {vuln['fixed_versions']}")
        except:
            print(stdout)
        return False

def check_licenses():
    """Проверяет лицензии с pip-licenses"""
    print("\n" + "=" * 70)
    print("2. ПРОВЕРКА ЛИЦЕНЗИЙ (pip-licenses)")
    print("=" * 70)
    
    # Получаем список лицензий
    returncode, stdout, stderr = run_command(
        "pip-licenses --format=json --with-urls --with-authors"
    )
    
    try:
        licenses = json.loads(stdout)
        
        print(f"\nВсего пакетов: {len(licenses)}\n")
        print("Сводка по лицензиям:")
        
        license_counts = {}
        for pkg in licenses:
            lic = pkg.get('License', 'Unknown')
            license_counts[lic] = license_counts.get(lic, 0) + 1
        
        for lic, count in sorted(license_counts.items(), key=lambda x: x, reverse=True):
            print(f"  {lic}: {count} пакетов")
        
        # Проверяем на потенциально опасные лицензии
        dangerous_licenses = ['GPL', 'AGPL']
        print("\n\nПотенциально конфликтующие лицензии (GPL-совместимые):")
        
        found_dangerous = False
        for pkg in licenses:
            lic = pkg.get('License', 'Unknown')
            if any(danger in lic for danger in dangerous_licenses):
                print(f"  ⚠ {pkg['Name']}: {lic}")
                found_dangerous = True
        
        if not found_dangerous:
            print("  ✓ GPL-совместимые лицензии не найдены")
        
        return not found_dangerous
        
    except Exception as e:
        print(f"Ошибка при парсинге лицензий: {e}")
        return False

def check_outdated():
    """Проверяет устаревшие пакеты"""
    print("\n" + "=" * 70)
    print("3. ПРОВЕРКА УСТАРЕВШИХ ПАКЕТОВ")
    print("=" * 70)
    
    returncode, stdout, stderr = run_command("pip list --outdated")
    
    if "to check" not in stdout and not stdout.strip():
        print("✓ Все пакеты актуальны")
        return True
    else:
        print("⚠ Найдены устаревшие пакеты:")
        print(stdout)
        return True

def generate_sbom():
    """Генерирует SBOM (Software Bill of Materials)"""
    print("\n" + "=" * 70)
    print("4. ГЕНЕРАЦИЯ SBOM (Software Bill of Materials)")
    print("=" * 70)
    
    returncode, stdout, stderr = run_command(
        "pip-licenses --format=json > sbom_report.json"
    )
    
    try:
        with open('sbom_report.json', 'r') as f:
            sbom_data = json.load(f)
        
        print(f"\n✓ SBOM сгенерирован (sbom_report.json)")
        print(f"  Всего компонентов: {len(sbom_data)}")
        
        # Сохраняем в более красивом формате
        with open('sbom_report.json', 'w') as f:
            json.dump(sbom_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"✗ Ошибка при генерации SBOM: {e}")
        return False

def create_audit_report():
    """Создает полный отчет об аудите"""
    print("\n" + "=" * 70)
    print("ПОЛНЫЙ ОТЧЕТ АУДИТА")
    print("=" * 70)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'vulnerabilities': audit_vulnerabilities(),
        'licenses': check_licenses(),
        'outdated': check_outdated(),
        'sbom': generate_sbom()
    }
    
    # Сохраняем результаты
    with open('audit_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 70)
    print("ИТОГИ:")
    print("=" * 70)
    
    status = all(results.values())
    if status:
        print("✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        print("✗ ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        for check, passed in results.items():
            if not passed and check != 'timestamp':
                print(f"  - {check}")
    
    return status

if __name__ == '__main__':
    success = create_audit_report()
    sys.exit(0 if success else 1)

