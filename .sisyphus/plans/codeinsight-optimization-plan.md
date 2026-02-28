# CodeInsight 平台优化工作计划

## TL;DR

> **快速摘要**: 修复CodeInsight平台的三个核心问题 - 信息展示null值、聊天不关联项目、缺失版本对比功能
> 
> **交付物**:
> - 修复项目信息展示组件，确保正确显示API、架构、依赖数据
> - 增强RAG服务，使聊天能够正确关联当前项目并生成项目摘要文档
> - 实现版本对比功能，支持可视化展示代码/功能差异
> 
> **预估工作量**: 大型 (需要多个组件协调修改)
> **并行执行**: 是 (3个主要功能模块可并行开发)
> **关键路径**: 修复信息展示 → 增强RAG → 实现版本对比

---

## Context

### 原始需求
用户要求实现聚焦"项目上传 - 信息展示 - 问答对话"三大核心场景的代码洞察平台，但当前存在以下问题：
1. 获取的信息显示为null值
2. 聊天对话无法关联当前项目
3. 版本对比功能尚未实现

### 当前系统分析

**现有架构**:
- 后端：FastAPI + SQLAlchemy + ChromaDB向量存储
- 前端：React + TypeScript + Zustand状态管理
- 核心模块：项目导入、代码解析、RAG聊天、功能分析

**发现的问题**:

1. **信息展示null问题**:
   - `FeatureAnalysis.tsx` 组件正确调用了API获取功能数据
   - `featureService.py` 中的分析功能已实现
   - 问题可能在于API响应格式不匹配或前端数据解析错误

2. **聊天不关联项目问题**:
   - `RAGService` 已有 `project_id` 参数支持
   - `qa_service.py` 正确传递了项目ID到检索器
   - 但缺少项目摘要文档生成功能

3. **版本对比功能缺失**:
   - 没有版本管理系统
   - 缺少代码差异可视化组件
   - 没有历史记录对比功能

---

## Work Objectives

### Core Objective
修复CodeInsight平台的三个核心问题，实现完整的项目分析、展示和对话功能。

### Concrete Deliverables
- 修复信息展示组件，确保正确显示API、架构、依赖数据
- 增强RAG系统，生成项目摘要文档并正确关联聊天上下文
- 实现版本对比功能，包括版本管理和差异可视化

### Definition of Done
- [ ] 项目详情页面能正确显示所有功能分析数据（不再有null值）
- [ ] 聊天系统能够基于当前项目上下文回答问题
- [ ] 用户可以在不同版本间切换并查看差异
- [ ] 所有功能有完整的测试覆盖
- [ ] 前端UI友好，错误处理完善

### Must Have
- 修复信息展示null值问题
- 聊天正确关联项目上下文
- 基础版本对比功能

### Must NOT Have (Guardrails)
- 不要大幅修改现有API结构（尽量保持向后兼容）
- 不要引入新的外部依赖（除非必要）
- 不要完全重写现有组件（优先修复和增强）

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: YES (Tests-after)
- **Framework**: pytest (backend) + 端到端测试 (frontend)

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

#### 信息展示修复验证

```bash
Scenario: 项目功能信息正确显示
  Tool: Playwright (playwright skill)
  Preconditions: 测试项目已导入并完成索引
  Steps:
    1. 导航到项目详情页面
    2. 点击"功能分析"标签页
    3. 检查各子标签（功能树、前端功能、后端功能、API端点、数据模型）
    4. 验证每个标签页都有数据展示（不再显示null或"暂无数据"）
  Expected Result: 所有标签页正确显示对应的功能数据
  Evidence: .sisyphus/evidence/feature-display-fix.png

Scenario: API端点列表正确加载
  Tool: Playwright (playwright skill)
  Preconditions: 后端API服务正常运行
  Steps:
    1. 打开项目详情页面
    2. 点击"功能分析"→"API端点"
    3. 验证API表格中有数据
    4. 检查方法、路径、文件列是否正确填充
  Expected Result: API端点表格显示完整数据
  Evidence: .sisyphus/evidence/api-endpoints-display.png
```

#### 聊天关联项目验证

```bash
Scenario: 聊天正确关联项目上下文
  Tool: Playwright (playwright skill) + Bash (curl)
  Preconditions: 项目已完成索引，聊天服务正常运行
  Steps:
    1. 导航到聊天页面
    2. 选择特定项目
    3. 发送与项目相关的问题（如"这个项目的主要功能是什么？"）
    4. 验证回答是否基于项目内容
    5. 检查回答中是否包含项目特定信息
  Expected Result: 聊天回答基于所选项目，包含项目相关信息
  Evidence: .sisyphus/evidence/chat-project-context.png

Scenario: 项目摘要文档生成
  Tool: Bash (curl)
  Preconditions: RAG服务正常运行
  Steps:
    1. 调用聊天API，project_id参数为测试项目
    2. 查询"总结这个项目的主要功能和架构"
    3. 检查回答是否包含准确的项目概述
    4. 验证是否引用了项目中的具体文件
  Expected Result: 返回基于项目文件的准确摘要
  Evidence: .sisyphus/evidence/project-summary-response.json
```

#### 版本对比验证

```bash
Scenario: 版本列表正确显示
  Tool: Playwright (playwright skill)
  Preconditions: 至少有两个版本的项目
  Steps:
    1. 导航到项目详情页面
    2. 点击新增的"版本对比"标签页
    3. 验证版本列表是否正确显示
    4. 检查版本信息（时间、提交ID、描述）
  Expected Result: 版本列表正确显示所有可用版本
  Evidence: .sisyphus/evidence/version-list-display.png

Scenario: 代码差异正确可视化
  Tool: Playwright (playwright skill)
  Preconditions: 选择了两个不同版本
  Steps:
    1. 在版本对比页面选择两个不同版本
    2. 点击"比较"按钮
    3. 验证差异视图正确显示
    4. 检查添加、删除、修改的代码行
  Expected Result: 代码差异正确高亮显示
  Evidence: .sisyphus/evidence/code-diff-display.png
```

---

## Execution Strategy

### 并行执行方案

我们将任务分为三个主要工作流，可以部分并行执行：

```
Wave 1 (立即开始):
├── 任务1: 修复信息显示null值问题
└── 任务3.1: 设计并实现版本管理基础架构

Wave 2 (Wave 1完成后):
├── 任务2: 增强RAG系统，支持项目关联
└── 任务3.2: 实现版本对比UI组件

Wave 3 (所有基础功能完成后):
├── 任务3.3: 集成版本对比功能
└── 任务4: 测试与优化

关键路径: 任务1 → 任务2 → 任务3.3
并行加速: 约30%时间节省
```

### 依赖矩阵

| 任务 | 依赖 | 阻塞 | 可并行 |
|------|--------|--------|---------|
| 1. 修复信息显示 | 无 | 2 | 3.1 |
| 2. 增强RAG系统 | 1 | 3.3 | 3.2 |
| 3.1 版本管理架构 | 无 | 3.2 | 1, 2 |
| 3.2 版本对比UI | 3.1 | 3.3 | 2 |
| 3.3 集成版本对比 | 2, 3.2 | 无 | 无 |
| 4. 测试优化 | 3.3 | 无 | 无 |

---

## TODOs

- [ ] 1. 修复信息显示null值问题

  **What to do**:
  - 调查API响应格式与前端期望格式的不匹配
  - 修复feature store中的数据解析逻辑
  - 确保错误处理和数据回退机制正常工作
  - 添加调试日志以便跟踪数据流

  **Must NOT do**:
  - 不要完全重写现有的API结构
  - 不要修改数据库schema

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick` (这是一个明确的bug修复任务，需要快速诊断和修复)
    - Reason: 问题定位和修复需要快速迭代，不需要复杂的架构设计
  - **Skills**: [`git-master`]
    - `git-master`: 可能需要追踪最近的代码变更导致的问题
  - **Skills Evaluated but Omitted**:
    - `playwright`: 初期诊断不需要UI测试，修复后再添加验证

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 3.1)
  - **Blocks**: Task 2
  - **Blocked By**: None

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `frontend/src/stores/featureStore.ts:21-31` - API响应数据解析模式
  - `backend/app/api/features.py:34` - API响应格式标准
  - `frontend/src/components/FeatureAnalysis.tsx:125-147` - 数据显示逻辑

  **API/Type References** (contracts to implement against):
  - `frontend/src/types/index.ts` - 前端类型定义
  - `backend/app/services/feature_service.py:121-125` - 后端数据格式

  **Test References** (testing patterns to follow):
  - `backend/tests/test_*.py` - 后端测试模式
  - AGENTS.md中的测试命令

  **Documentation References** (specs and requirements):
  - 原始问题描述中提到的"信息展示显示null值"

  **External References** (libraries and frameworks):
  - React Query/Zustand文档: 状态管理最佳实践
  - FastAPI文档: API响应格式标准

  **WHY Each Reference Matters** (explain the relevance):
  - featureStore.ts：这是数据流的关键节点，问题可能出现在这里
  - features.py：API响应格式必须与前端期望一致
  - FeatureAnalysis.tsx：显示逻辑需要正确处理null/undefined数据

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```bash
  Scenario: FeatureAnalysis组件不再显示null值
    Tool: Playwright (playwright skill)
    Preconditions: 项目已导入并完成索引
    Steps:
      1. 导航到项目详情页面
      2. 点击"功能分析"标签页
      3. 检查各子标签页（功能树、前端功能、后端功能、API端点、数据模型）
      4. 验证数据正确加载（不再显示"暂无数据"或null）
    Expected Result: 所有标签页显示实际的功能数据
    Evidence: .sisyphus/evidence/task-1-feature-data-display.png

  Scenario: API响应数据格式正确
    Tool: Bash (curl)
    Preconditions: 后端服务运行中
    Steps:
      1. curl -X GET "http://localhost:8000/api/features/{PROJECT_ID}/frontend"
      2. 验证响应JSON结构
      3. 检查data字段不为null
      4. 验证返回数据包含预期的字段
    Expected Result: API返回格式正确的数据
    Evidence: .sisyphus/evidence/task-1-api-response.json
  ```

  **Evidence to Capture:**
  - [ ] 功能数据展示截图
  - [ ] API响应日志
  - [ ] 错误修复后的console日志

  **Commit**: YES (after each subtask)
  - Message: `fix(features): resolve null data display issue`
  - Files: `frontend/src/stores/featureStore.ts`, `frontend/src/components/FeatureAnalysis.tsx`
  - Pre-commit: `npm run lint && npm run typecheck`

---

- [ ] 2. 增强RAG系统，支持项目关联和摘要生成

  **What to do**:
  - 实现项目摘要文档生成功能
  - 确保聊天时正确传递project_id
  - 优化向量检索，优先检索项目相关内容
  - 增强提示词，包含项目上下文信息

  **Must NOT do**:
  - 不要修改核心RAG架构
  - 不要改变现有API签名

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `ultrabrain` (需要复杂的LLM集成和提示词优化)
    - Reason: RAG系统优化需要深入的LLM知识和提示工程
  - **Skills**: [`git-master`]
    - `git-master`: 追踪RAG相关代码的变更历史
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: 主要在backend处理，UI改动较小

  **Parallelization**:
  - **Can Run In Parallel**: NO (依赖Task 1完成)
  - **Parallel Group**: Wave 2 (with Task 3.2)
  - **Blocks**: Task 3.3
  - **Blocked By**: Task 1

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `backend/app/rag/qa_service.py:145-174` - 现有的QA服务逻辑
  - `backend/app/rag/rag_service.py:114-133` - RAG服务的核心方法
  - `backend/app/rag/retriever.py` - 检索器实现

  **API/Type References** (contracts to implement against):
  - `backend/app/api/chat.py:75-107` - 聊天API接口
  - `backend/app/models/chat.py` - 聊天相关数据模型

  **Test References** (testing patterns to follow):
  - `backend/tests/test_rag.py` - RAG相关测试

  **Documentation References** (specs and requirements):
  - 原始需求："聊天无法关联当前项目"

  **External References** (libraries and frameworks):
  - LangChain文档: RAG最佳实践
  - OpenAI API文档: 上下文窗口和提示优化

  **WHY Each Reference Matters** (explain the relevance):
  - qa_service.py：需要增强项目上下文处理
  - rag_service.py：核心RAG逻辑，需要优化检索
  - chat.py：API接口，确保正确传递project_id

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```bash
  Scenario: 聊天基于项目上下文回答
    Tool: Playwright (playwright skill)
    Preconditions: 项目已完成索引
    Steps:
      1. 打开聊天页面
      2. 在项目选择器中选择特定项目
      3. 发送问题："这个项目的主要功能是什么？"
      4. 验证回答包含项目特定功能
      5. 检查引用来源是否来自该项目文件
    Expected Result: 回答基于所选项目，内容准确相关
    Evidence: .sisyphus/evidence/task-2-chat-context.png

  Scenario: 项目摘要文档生成
    Tool: Bash (curl)
    Preconditions: RAG服务运行中
    Steps:
      1. POST /api/chat/ask with project_id and question="总结这个项目"
      2. 验证响应包含项目概述
      3. 检查是否有架构、功能、技术栈信息
      4. 确认引用了项目中的关键文件
    Expected Result: 生成准确的项目摘要
    Evidence: .sisyphus/evidence/task-2-project-summary.json
  ```

  **Evidence to Capture:**
  - [ ] 聊天上下文测试截图
  - [ ] 摘要生成API响应
  - [ ] 向量检索日志

  **Commit**: YES
  - Message: `feat(rag): enhance project context awareness and summary generation`
  - Files: `backend/app/rag/qa_service.py`, `backend/app/services/rag_service.py`
  - Pre-commit: `cd backend && mypy . && pytest test_rag.py`

---

- [ ] 3. 实现版本对比功能

  **What to do**:
  - 设计版本管理数据模型
  - 实现代码差异检测算法
  - 创建版本对比UI组件
  - 集成到现有项目详情页面

  **Must NOT do**:
  - 不要使用外部的diff库（除非必要）
  - 不要修改核心项目数据模型

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `artistry` (需要创新的UI设计和用户体验)
    - Reason: 版本对比需要清晰的可视化展示
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: 设计和实现差异可视化界面
  - **Skills Evaluated but Omitted**:
    - `git-master`: 虽然涉及版本，但不是核心Git操作

  **Parallelization**:
  - **Can Run In Parallel**: YES (基础架构可并行开发)
  - **Parallel Group**: Wave 1 (3.1), Wave 2 (3.2)
  - **Blocks**: None
  - **Blocked By**: None (3.1), 3.1 (3.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `backend/app/models/project.py` - 项目数据模型结构
  - `frontend/src/pages/ProjectDetail.tsx:71-76` - 现有标签页实现

  **API/Type References** (contracts to implement against):
  - 需要创建的新API端点: `/api/projects/{id}/versions`, `/api/projects/{id}/diff`

  **Test References** (testing patterns to follow):
  - 现有的项目测试模式

  **Documentation References** (specs and requirements):
  - 原始需求："版本对比功能差异这个暂时还没有完成"

  **External References** (libraries and frameworks):
  - react-diff-viewer: 差异可视化组件
  - Git diff算法文档

  **WHY Each Reference Matters** (explain the relevance):
  - project.py：扩展版本管理字段
  - ProjectDetail.tsx：添加新标签页

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```bash
  Scenario: 版本列表显示
    Tool: Playwright (playwright skill)
    Preconditions: 项目有多个版本记录
    Steps:
      1. 导航到项目详情页面
      2. 点击"版本对比"标签页
      3. 验证版本列表显示
      4. 检查版本信息（时间、提交ID）
    Expected Result: 版本列表正确显示
    Evidence: .sisyphus/evidence/task-3-version-list.png

  Scenario: 代码差异可视化
    Tool: Playwright (playwright skill)
    Preconditions: 选择了两个版本
    Steps:
      1. 在版本对比页选择两个版本
      2. 点击"比较差异"
      3. 验证diff视图显示
      4. 检查添加/删除/修改的高亮
    Expected Result: 代码差异清晰可视化
    Evidence: .sisyphus/evidence/task-3-diff-view.png
  ```

  **Evidence to Capture:**
  - [ ] 版本列表截图
  - [ ] 差异视图截图
  - [ ] API响应示例

  **Commit**: YES (after each subtask)
  - Message: `feat(versions): implement version comparison functionality`
  - Files: 多个文件需要提交
  - Pre-commit: `npm run build && cd backend && pytest`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `fix(display): resolve null values in feature analysis` | frontend/src/stores/featureStore.ts, frontend/src/components/FeatureAnalysis.tsx | npm test |
| 2 | `feat(rag): add project context and summary generation` | backend/app/rag/*.py | pytest tests/test_rag.py |
| 3.1 | `feat(versions): add version management models and APIs` | backend/app/models/versions.py, backend/app/api/versions.py | pytest tests/test_versions.py |
| 3.2 | `feat(ui): implement version comparison interface` | frontend/src/components/VersionComparison.tsx | npm run build |
| 3.3 | `feat(versions): integrate version comparison with project detail` | frontend/src/pages/ProjectDetail.tsx | e2e test |

---

## Success Criteria

### Verification Commands
```bash
# Backend tests
cd backend && pytest -v

# Frontend build
cd frontend && npm run build

# Integration test
curl -X GET "http://localhost:8000/api/features/{project_id}"
```

### Final Checklist
- [ ] FeatureAnalysis组件正确显示所有功能数据（不再有null值）
- [ ] 聊天系统能基于项目上下文生成相关回答
- [ ] 版本对比功能完整可用
- [ ] 所有新功能有对应的测试
- [ ] UI响应流畅，错误提示友好
- [ ] 文档更新（API文档、用户指南）