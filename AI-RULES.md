# AI 开发规则

本项目由 AI 辅助开发，以下规则必须严格遵守。

---

## 1. Git 提交规则

### 1.1 提交时机

- 每完成一个子任务，立即提交
- 提交前确保代码可运行（无语法错误）
- 提交信息遵循 Conventional Commits 规范

### 1.2 提交格式

```
<type>(<scope>): <subject>

<body> (可选)

<footer> (可选)
```

#### Type 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat(api): add project import endpoint |
| `fix` | Bug修复 | fix(parser): handle empty file parsing |
| `docs` | 文档更新 | docs: update API documentation |
| `style` | 代码格式（不影响逻辑） | style: format code with prettier |
| `refactor` | 重构 | refactor: extract common parser logic |
| `test` | 测试 | test: add unit tests for vector store |
| `chore` | 构建/工具/配置 | chore: update docker configuration |

#### Scope 范围

| Scope | 说明 |
|-------|------|
| `api` | 后端API相关 |
| `parser` | 代码解析器 |
| `rag` | RAG检索引擎 |
| `llm` | LLM服务层 |
| `ui` | 前端界面 |
| `docs` | 文档生成 |
| `docker` | Docker配置 |
| `config` | 配置文件 |

### 1.3 提交示例

```bash
# 好的提交
git add backend/app/api/projects.py
git commit -m "feat(api): add project import endpoint"

git add backend/app/parsers/python_parser.py
git commit -m "fix(parser): handle empty file parsing"

# 避免的提交
git add .
git commit -m "update"                    # 太笼统
git commit -m "fix bugs"                  # 不明确
git commit -m "一些修改"                   # 无意义
```

### 1.4 提交粒度

- 每个子任务一次提交
- 不相关的修改分开提交
- 大任务拆分为多个小提交

---

## 2. 分支策略

### 2.1 分支结构

```
main                    # 主分支 - 稳定发布版本
  └── develop           # 开发分支 - 集成测试
      ├── feature/phase-1-foundation    # Phase 1 功能分支
      ├── feature/phase-2-parser        # Phase 2 功能分支
      ├── feature/phase-3-analysis      # Phase 3 功能分支
      ├── feature/phase-4-rag-chat      # Phase 4 功能分支
      ├── feature/phase-5-visualization # Phase 5 功能分支
      └── feature/phase-6-optimization  # Phase 6 功能分支
```

### 2.2 分支规则

1. `main` 分支：只接受来自 `develop` 的合并，代表稳定版本
2. `develop` 分支：开发集成分支，功能测试通过后合并到 main
3. `feature/*` 分支：每个 Phase 一个分支，完成后合并到 develop

### 2.3 分支操作

```bash
# 创建新功能分支
git checkout develop
git checkout -b feature/phase-1-foundation

# 完成功能后合并
git checkout develop
git merge feature/phase-1-foundation
git branch -d feature/phase-1-foundation
```

---

## 3. 代码规范

### 3.1 Python (后端)

```python
# 使用 Black 格式化
# 使用 isort 排序 import

# 类型注解必须完整
def parse_file(file_path: str) -> dict[str, Any]:
    """解析文件并返回结构化数据。
    
    Args:
        file_path: 文件路径
        
    Returns:
        解析后的数据字典
        
    Raises:
        FileNotFoundError: 文件不存在
    """
    pass

# import 排序
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
```

### 3.2 TypeScript (前端)

```typescript
// 使用 ESLint + Prettier
// 组件使用函数式组件 + Hooks
// 禁止 any 类型

// 组件示例
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  label, 
  onClick, 
  disabled = false 
}) => {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
};
```

### 3.3 通用规则

- 禁止提交敏感信息（API Key、密码、Token等）
- 禁止提交 `node_modules/`、`__pycache__/`、`.env` 等
- 代码必须有适当的注释
- 复杂逻辑必须有说明

---

## 4. 任务执行规则

### 4.1 执行前检查

```bash
# 1. 确认当前分支
git branch

# 2. 拉取最新代码
git pull origin <current-branch>

# 3. 确认工作区干净
git status

# 4. 阅读任务文档
cat docs/task-progress.md
cat plans/phase-X-xxx.md
```

### 4.2 执行中规范

1. 只修改与当前任务相关的文件
2. 保持代码风格与已有代码一致
3. 编写可测试的代码
4. 及时验证功能是否正常

### 4.3 执行后验收

```bash
# 1. 运行代码检查
# Python
cd code-insight/backend
black --check .
isort --check .
mypy .

# TypeScript
cd code-insight/frontend
npm run lint
npm run typecheck

# 2. 提交代码
git add <specific-files>
git commit -m "<type>(<scope>): <subject>"

# 3. 更新任务进度
# 编辑 docs/task-progress.md
```

---

## 5. 任务进度管理

### 5.1 进度文件位置

`docs/task-progress.md`

### 5.2 状态标记

| 标记 | 状态 | 说明 |
|------|------|------|
| `[ ]` | 待开始 | 任务尚未开始 |
| `[~]` | 进行中 | 任务正在执行 |
| `[x]` | 已完成 | 任务已完成并提交 |
| `[-]` | 已跳过 | 任务被跳过（需说明原因） |

### 5.3 进度更新格式

```markdown
| # | 任务 | 状态 | 提交hash | 完成时间 | 备注 |
|---|------|------|----------|----------|------|
| 1.1 | 创建项目结构 | [x] | abc1234 | 2024-01-15 | |
| 1.2 | 后端FastAPI框架 | [~] | - | - | 进行中 |
| 1.3 | 前端React框架 | [ ] | - | - | |
```

---

## 6. 文件结构规则

### 6.1 文档位置

| 文档 | 路径 | 用途 |
|------|------|------|
| 需求文档 | `docs/requirements.md` | 完整需求规格 |
| 架构设计 | `docs/architecture.md` | 系统架构说明 |
| API设计 | `docs/api-design.md` | API接口设计 |
| 任务分解 | `docs/task-breakdown.md` | 任务详细分解 |
| 任务进度 | `docs/task-progress.md` | 任务执行进度 |
| AI规则 | `AI-RULES.md` | 本文件 |

### 6.2 计划文件

| 文件 | 路径 | 用途 |
|------|------|------|
| Phase 1 | `plans/phase-1-foundation.md` | 基础框架任务 |
| Phase 2 | `plans/phase-2-parser.md` | 代码解析任务 |
| Phase 3 | `plans/phase-3-analysis.md` | 功能分析任务 |
| Phase 4 | `plans/phase-4-rag-chat.md` | RAG问答任务 |
| Phase 5 | `plans/phase-5-visualization.md` | 可视化任务 |
| Phase 6 | `plans/phase-6-optimization.md` | 优化完善任务 |

---

## 7. 禁止事项

### 7.1 Git 禁止

1. 禁止 `git push --force`
2. 禁止直接提交到 `main` 分支
3. 禁止 `git commit --no-verify` 跳过检查
4. 禁止提交包含硬编码密钥的代码
5. 禁止一个 commit 包含多个不相关的修改

### 7.2 代码禁止

1. 禁止使用 `any` 类型（TypeScript）
2. 禁止忽略 ESLint/Pylint 警告
3. 禁止在生产代码中使用 `print()` 调试
4. 禁止提交带有 `TODO` 但未处理的代码（需先处理或记录）

### 7.3 安全禁止

1. 禁止在代码中硬编码密钥、Token、密码
2. 禁止提交 `.env` 文件
3. 禁止提交包含真实用户数据的测试文件

---

## 8. AI 执行检查清单

每次任务执行前后，AI 必须确认：

### 执行前

- [ ] 已读取 `docs/task-progress.md` 确认当前任务
- [ ] 已读取 `plans/phase-X-xxx.md` 了解任务详情
- [ ] 已确认当前在正确的分支
- [ ] 已确认工作区是干净的

### 执行后

- [ ] 代码已通过 lint/typecheck 检查
- [ ] 已使用正确的 commit 格式提交
- [ ] 已记录 commit hash 到进度文档
- [ ] 已更新 `docs/task-progress.md` 状态

---

## 9. 附录

### 9.1 常用命令速查

```bash
# Git
git status
git branch
git checkout -b feature/xxx
git add <files>
git commit -m "type(scope): subject"
git log --oneline -10

# Python
black .
isort .
mypy .
pytest

# Node.js
npm run lint
npm run typecheck
npm run build
npm run test
```

### 9.2 问题反馈

如遇到规则不明确或需要调整，请在 `docs/task-progress.md` 的备注中说明。
