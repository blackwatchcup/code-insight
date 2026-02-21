import subprocess
import os

os.chdir(r'C:\Users\Alan ZA Zhang\Desktop\newcode\code-insight\code-insight')

print("Current directory:", os.getcwd())

print("\n=== Git status ===")
result = subprocess.run(['git', 'status'], capture_output=True, text=True)
print(result.stdout)

print("\n=== Git add ===")
result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
print("Done")

print("\n=== Git commit ===")
result = subprocess.run(['git', 'commit', '-m', 'feat(parser): implement Phase 2 code parsing engine'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== Git log ===")
result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
print(result.stdout)
