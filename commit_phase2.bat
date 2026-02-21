@echo off
cd /d "C:\Users\Alan ZA Zhang\Desktop\newcode\code-insight\code-insight"
git add .
git status
git commit -m "feat(parser): implement Phase 2 code parsing engine"
git log --oneline -3
