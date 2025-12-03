import importlib
import subprocess
import sys

# List of external dependencies (standard libs excluded)
REQUIRED_PACKAGES = [
    "requests",
    "urllib3",
    "pandas",
    "PyYAML",
    "jaydebeapi",
    "InquirerPy"
]

def install_package(package):
    """Install a package via pip inside the current venv."""
    print(f"[INFO] Installing missing package: {package}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_dependencies():
    """Check and install required dependencies."""
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg if pkg != "PyYAML" else "yaml")
            print(f"[OK] {pkg} is installed")
        except ImportError:
            install_package(pkg)

if __name__ == "__main__":
    check_dependencies()
    print("[INFO] Dependency check complete.")
