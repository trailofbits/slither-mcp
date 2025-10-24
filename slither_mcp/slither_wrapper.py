"""Slither wrapper for lazy loading and project building."""

import subprocess
import shutil
import os
import glob

from crytic_compile import CryticCompile
from slither import Slither


def build_project_foundry(path: str):
    """Build the Foundry project using forge build"""
    
    # Try to find the forge executable
    forge_cmd = _find_forge_executable()
    
    try:
        result = subprocess.run(
            [forge_cmd, "build", "--build-info"],
            cwd=str(path),
            check=True,
            capture_output=True,
            text=True
        )
        print("Foundry build completed successfully")
        if result.stdout:
            print("Build output:", result.stdout)
            
    except subprocess.CalledProcessError as e:
        print("Error building Foundry project:")
        print("Return code:", e.returncode)
        if e.stdout:
            print("stdout:", e.stdout)
        if e.stderr:
            print("stderr:", e.stderr)
        raise
    except FileNotFoundError as e:
        print(f"Could not find forge executable at: {forge_cmd}")
        print("Make sure Foundry is properly installed and in your PATH")
        print("You can install Foundry from: https://getfoundry.sh/")
        raise


def _find_forge_executable():
    """Find the forge executable, trying multiple common locations"""
    
    # First try using shutil.which to find forge in PATH
    forge_path = shutil.which("forge")
    if forge_path:
        return forge_path
    
    # Common installation paths to try
    common_paths = [
        os.path.expanduser("~/.foundry/bin/forge"),  # Default foundryup installation
        os.path.expanduser("~/.cargo/bin/forge"),    # If installed via cargo
        "/usr/local/bin/forge",                      # System installation
        "/opt/homebrew/bin/forge",                   # Homebrew on Apple Silicon
        "/usr/bin/forge",                            # System package manager
    ]
    
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            print(f"Found forge executable at: {path}")
            return path
    
    # If we can't find it anywhere, fall back to just "forge" and let the error happen
    print("Warning: Could not locate forge executable, trying 'forge' command directly")
    return "forge"


def _find_npx_executable():
    """Find the npx executable, trying multiple common locations"""
    
    # First try using shutil.which to find npx in PATH
    npx_path = shutil.which("npx")
    if npx_path:
        return npx_path
    
    # Common installation paths to try
    common_paths = [
        os.path.expanduser("~/.nvm/versions/node/*/bin/npx"),  # NVM installation (glob pattern)
        os.path.expanduser("~/.npm-global/bin/npx"),          # NPM global installation
        "/usr/local/bin/npx",                                 # System installation
        "/opt/homebrew/bin/npx",                              # Homebrew on Apple Silicon
        "/usr/bin/npx",                                       # System package manager
        os.path.expanduser("~/node_modules/.bin/npx"),        # Local node_modules
    ]
    
    # Handle glob patterns for NVM paths
    for path_pattern in common_paths:
        if "*" in path_pattern:
            matches = glob.glob(path_pattern)
            for match in matches:
                if os.path.isfile(match) and os.access(match, os.X_OK):
                    print(f"Found npx executable at: {match}")
                    return match
        else:
            if os.path.isfile(path_pattern) and os.access(path_pattern, os.X_OK):
                print(f"Found npx executable at: {path_pattern}")
                return path_pattern
    
    # If we can't find it anywhere, fall back to just "npx" and let the error happen
    print("Warning: Could not locate npx executable, trying 'npx' command directly")
    return "npx"


class LazySlither:
    """Lazy-loading wrapper for Slither that only builds/creates when accessed"""

    def __init__(self, path: str):
        self.path = path
        self._slither = None
        self._built = False

    def _ensure_built(self):
        """Ensure the Slither object is built and ready"""
        if not self._built:
            print(f"Lazy-loading Slither for project at {self.path}...")
            
            # Ensure forge is in PATH for CryticCompile
            forge_path = _find_forge_executable()
            forge_dir = os.path.dirname(forge_path)
            if forge_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{forge_dir}:{os.environ.get('PATH', '')}"
                print(f"Added {forge_dir} to PATH for CryticCompile")
            
            # Ensure npx is in PATH for CryticCompile
            npx_path = _find_npx_executable()
            npx_dir = os.path.dirname(npx_path)
            if npx_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{npx_dir}:{os.environ.get('PATH', '')}"
                print(f"Added {npx_dir} to PATH for CryticCompile")
            
            self._slither = Slither(CryticCompile(self.path))
            print("Slither object created successfully")
            self._built = True

    @property
    def slither(self) -> Slither:
        """Get the Slither object, building it if necessary"""
        self._ensure_built()
        return self._slither

    # Delegate attribute access to the underlying Slither object
    def __getattr__(self, name):
        # Don't trigger slither for common Python internal attributes
        if name.startswith("_") or name in (
            "__dict__",
            "__class__",
            "__module__",
            "__weakref__",
        ):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        self._ensure_built()
        return getattr(self._slither, name)

