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

