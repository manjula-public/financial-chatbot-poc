
import sys
from importlib.metadata import version, PackageNotFoundError

print("--- Python Version ---")
print(sys.version)

print("\n--- Installed Packages ---")
packages = [
    "langchain", "langchain-core", "langchain-community", 
    "langchain-openai", "langchain-google-genai",
    "google-generativeai", "pydantic"
]
for p in packages:
    try:
        print(f"{p}: {version(p)}")
    except PackageNotFoundError:
        print(f"{p}: Not Installed")
