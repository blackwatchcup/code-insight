# Bugfix Requirements Document

## Introduction

聊天功能当前在回答用户问题时缺少项目上下文信息，导致回答与项目的关联度低。虽然系统已经实现了 RAG（检索增强生成）功能来检索相关代码片段，但缺少项目的基本元数据（如项目名称、技术栈、文件结构、依赖关系等）作为上下文。这导致 LLM 在生成回答时无法充分理解项目的整体情况，回答显得通用而不够针对性。

本次修复将确保聊天功能在处理用户问题时，能够获取并传递当前项目的基本信息给 LLM，从而提高回答的相关性和准确性。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 用户在项目模式（chat_mode="project"）下提问 THEN 系统仅使用 RAG 检索到的代码片段作为上下文，不包含项目的基本信息（名称、路径、技术栈、文件统计等）

1.2 WHEN 用户询问项目整体相关的问题（如"这个项目是做什么的？"、"项目使用了哪些技术？"）THEN 系统无法提供准确的项目级别信息，只能基于检索到的零散代码片段回答

1.3 WHEN 用户在有 project_id 的会话中提问 THEN 系统不会主动获取该项目的元数据信息并添加到 LLM 提示词中

1.4 WHEN LLM 生成回答时 THEN 提示词中缺少项目上下文部分，导致 LLM 无法理解项目的整体架构和特征

### Expected Behavior (Correct)

2.1 WHEN 用户在项目模式（chat_mode="project"）下提问且提供了 project_id THEN 系统 SHALL 从数据库获取项目基本信息（名称、路径、source_type、file_count、line_count、status）并将其添加到 LLM 提示词的上下文部分

2.2 WHEN 用户询问项目整体相关的问题 THEN 系统 SHALL 在提示词中包含项目元数据，使 LLM 能够基于完整的项目信息生成准确回答

2.3 WHEN 用户在有 project_id 的会话中提问 THEN 系统 SHALL 自动获取项目信息并格式化为结构化的上下文文本（包含项目名称、类型、文件统计、技术栈等）

2.4 WHEN LLM 生成回答时 THEN 提示词 SHALL 包含"项目信息"部分，位于"代码上下文"部分之前，提供项目的整体概览

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 用户在自由模式（chat_mode="freeform"）下提问 THEN 系统 SHALL CONTINUE TO 跳过 RAG 检索和项目上下文，使用 FREEFORM_PROMPT 生成回答

3.2 WHEN 用户提问时未提供 project_id THEN 系统 SHALL CONTINUE TO 正常处理问题，仅使用 RAG 检索结果（如果在项目模式）或直接回答（如果在自由模式）

3.3 WHEN RAG 检索到相关代码片段 THEN 系统 SHALL CONTINUE TO 将这些代码片段格式化为上下文并传递给 LLM

3.4 WHEN 聊天历史存在时 THEN 系统 SHALL CONTINUE TO 将历史消息传递给 LLM 以保持对话连贯性

3.5 WHEN 项目索引、搜索、历史管理等其他聊天相关功能被调用 THEN 系统 SHALL CONTINUE TO 按现有逻辑正常工作，不受此修复影响


---

## Bug Condition Analysis

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type ChatRequest
  OUTPUT: boolean
  
  // Bug occurs when in project mode with a project_id but no project context is added
  RETURN (X.chat_mode = "project") AND (X.project_id IS NOT NULL)
END FUNCTION
```

### Property Specification

```pascal
// Property: Fix Checking - Project Context Integration
FOR ALL X WHERE isBugCondition(X) DO
  response ← answer'(X)
  project_info ← get_project_info(X.project_id)
  prompt_context ← extract_prompt_context(response)
  
  ASSERT project_info IS NOT NULL
  ASSERT prompt_context CONTAINS project_info.name
  ASSERT prompt_context CONTAINS project_info.file_count
  ASSERT prompt_context CONTAINS project_info.line_count
  ASSERT prompt_context CONTAINS project_info.source_type
END FOR
```

### Preservation Goal

```pascal
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  // For freeform mode or requests without project_id
  ASSERT answer(X).behavior = answer'(X).behavior
  ASSERT answer(X).prompt_structure = answer'(X).prompt_structure
END FOR
```

### Key Definitions

- **F (answer)**: 当前的 `QAService.answer()` 方法 - 不包含项目元数据上下文
- **F' (answer')**: 修复后的 `QAService.answer()` 方法 - 包含项目元数据上下文
- **Bug Condition**: `chat_mode="project"` 且 `project_id` 不为空
- **Counterexample**: 用户在项目 "code-insight" 中询问 "这个项目是做什么的？"，系统无法提供项目名称、技术栈等基本信息

### Expected Fix Impact

修复后，当满足 bug condition 时：
1. 系统将从数据库查询项目信息（Project 模型）
2. 将项目信息格式化为结构化文本（项目名称、类型、文件统计等）
3. 在构建 LLM 提示词时，将项目信息添加到上下文部分
4. LLM 将基于完整的项目上下文生成更相关的回答

对于不满足 bug condition 的情况（自由模式或无 project_id），行为保持不变。
