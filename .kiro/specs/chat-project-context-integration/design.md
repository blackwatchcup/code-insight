# Chat Project Context Integration Bugfix Design

## Overview

聊天功能当前在项目模式（chat_mode="project"）下缺少项目元数据上下文。虽然系统已实现 RAG 检索来获取相关代码片段，但缺少项目的基本信息（名称、技术栈、文件统计等）。这导致 LLM 无法充分理解项目整体情况，回答缺乏针对性。

本次修复将在 `QAService.answer()` 和 `QAService.answer_stream()` 方法中集成项目元数据获取逻辑，确保在项目模式下，LLM 提示词包含完整的项目上下文信息。修复策略是最小化改动，仅在满足 bug condition 时添加项目信息到提示词中，保持其他功能不变。

## Glossary

- **Bug_Condition (C)**: 触发 bug 的条件 - 当 chat_mode="project" 且 project_id 不为空时，系统未获取并添加项目元数据到 LLM 上下文
- **Property (P)**: 期望行为 - 在满足 bug condition 时，LLM 提示词应包含项目基本信息（名称、类型、文件统计、技术栈等）
- **Preservation**: 必须保持不变的现有行为 - 自由模式、无 project_id 的请求、RAG 检索、历史管理等功能
- **QAService**: `backend/app/rag/qa_service.py` 中的服务类，负责处理问答请求并生成回答
- **answer()**: QAService 的核心方法，处理用户问题并返回完整的 QAResponse
- **answer_stream()**: QAService 的流式响应方法，逐块返回 LLM 生成的回答
- **ProjectService**: `backend/app/services/project_service.py` 中的服务类，提供 `get_project()` 方法获取项目信息
- **Project Model**: `backend/app/models/project.py` 中的 SQLAlchemy 模型，包含 name, source_type, file_count, line_count, status 等字段
- **chat_mode**: 聊天模式参数，"project" 表示基于项目的 RAG 模式，"freeform" 表示自由对话模式
- **project_id**: 项目唯一标识符，用于从数据库查询项目信息和检索相关代码

## Bug Details

### Fault Condition

bug 发生在用户使用项目模式聊天时。`QAService.answer()` 和 `answer_stream()` 方法接收到 `chat_mode="project"` 和有效的 `project_id` 参数后，仅执行 RAG 检索获取代码片段，但未从数据库查询项目元数据，也未将项目信息添加到 LLM 提示词中。这导致 LLM 在生成回答时缺少项目整体上下文。

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type ChatRequest with fields (question, chat_mode, project_id, ...)
  OUTPUT: boolean
  
  RETURN (input.chat_mode = "project") 
         AND (input.project_id IS NOT NULL)
         AND (input.project_id != "")
         AND NOT projectContextAddedToPrompt(input)
END FUNCTION
```

### Examples

- **Example 1**: 用户在项目 "code-insight" 中询问 "这个项目是做什么的？"
  - **Expected**: LLM 应基于项目元数据（名称、技术栈、文件统计）回答
  - **Actual**: LLM 仅基于检索到的零散代码片段回答，无法提供项目整体信息

- **Example 2**: 用户在项目 "my-api" 中询问 "项目使用了哪些技术？"
  - **Expected**: LLM 应基于 source_type、文件扩展名分析等信息回答
  - **Actual**: LLM 只能从检索到的代码中推测，可能遗漏重要技术栈

- **Example 3**: 用户在项目 "frontend-app" 中询问 "项目有多少文件？"
  - **Expected**: LLM 应基于 file_count 字段准确回答
  - **Actual**: LLM 无法获取准确数字，只能说"不确定"

- **Edge Case**: 用户提供了 project_id 但数据库中不存在该项目
  - **Expected**: 系统应优雅处理，记录警告但继续处理（仅使用 RAG 结果）

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 自由模式（chat_mode="freeform"）下的聊天必须继续使用 FREEFORM_PROMPT，不执行 RAG 检索，不添加项目上下文
- 未提供 project_id 的请求必须继续正常处理，仅使用 RAG 检索结果（如果在项目模式）
- RAG 检索功能必须继续正常工作，检索到的代码片段格式化逻辑保持不变
- 聊天历史管理功能必须继续正常工作，历史消息传递给 LLM 的逻辑保持不变
- 置信度计算、引用提取、会话标题更新等功能必须保持不变

**Scope:**
所有不满足 bug condition 的输入（chat_mode != "project" 或 project_id 为空）应完全不受此修复影响。这包括：
- 自由模式下的所有聊天请求
- 项目模式但未提供 project_id 的请求
- 所有非聊天相关的功能（项目索引、搜索、分析等）

## Hypothesized Root Cause

基于 bug 描述和代码分析，最可能的原因是：

1. **缺少项目信息获取逻辑**: `QAService` 当前未依赖 `ProjectService`，没有调用 `get_project()` 方法获取项目元数据

2. **提示词构建不完整**: `_build_context()` 方法仅处理 RAG 检索结果，未考虑项目元数据的格式化和添加

3. **设计遗漏**: 初始设计时可能仅关注代码片段检索，未考虑项目整体信息对 LLM 理解的重要性

4. **依赖注入缺失**: `QAService.__init__()` 未接收 `ProjectService` 或数据库 session，无法查询项目信息

## Correctness Properties

Property 1: Fault Condition - Project Context Integration

_For any_ chat request where chat_mode="project" and project_id is not null, the fixed answer() and answer_stream() methods SHALL retrieve project metadata from the database and include it in the LLM prompt context, ensuring the LLM has access to project name, source_type, file_count, line_count, and status information.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Non-Project Mode Behavior

_For any_ chat request where chat_mode != "project" or project_id is null, the fixed methods SHALL produce exactly the same behavior as the original methods, preserving freeform mode handling, RAG retrieval logic, history management, and all other existing functionality.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

