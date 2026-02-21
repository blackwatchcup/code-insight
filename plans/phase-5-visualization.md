# Phase 5: 可视化与文档 - 执行计划

**目标**：实现流程图、架构图生成，文档生成与导出  
**任务数**：8个  
**预计时间**：1.5周  
**分支**：feature/phase-5-visualization  
**依赖**：Phase 3, Phase 4 完成

---

## 任务 5.1：Mermaid流程图生成

### 描述
通过LLM生成Mermaid格式的流程图。

### 执行步骤

1. 创建流程图生成器 `app/graph/flow_generator.py`
```python
from typing import List, Dict
from app.llm.openai_service import OpenAIService

FLOW_PROMPT = """基于以下代码，生成一个清晰的执行流程图。

代码：
```{language}
{code}
```

要求：
1. 使用Mermaid flowchart TD语法
2. 节点使用中文描述
3. 包含关键步骤和判断分支
4. 节点ID使用简洁的字母

请直接输出Mermaid代码，不要包含```mermaid标记："""

class FlowGenerator:
    def __init__(self):
        self.llm = OpenAIService()
    
    async def generate_from_function(
        self, 
        code: str, 
        language: str = "python"
    ) -> Dict:
        prompt = FLOW_PROMPT.format(code=code, language=language)
        
        messages = [
            {"role": "system", "content": "你是一个专业的流程图生成专家。"},
            {"role": "user", "content": prompt}
        ]
        
        mermaid_code = await self.llm.generate(messages, temperature=0.3)
        
        # 清理输出
        mermaid_code = mermaid_code.strip()
        if mermaid_code.startswith("```"):
            mermaid_code = mermaid_code.split("\n", 1)[1]
        if mermaid_code.endswith("```"):
            mermaid_code = mermaid_code.rsplit("```", 1)[0]
        
        return {
            "type": "flowchart",
            "format": "mermaid",
            "content": mermaid_code,
            "nodes": self._extract_nodes(mermaid_code)
        }
    
    def _extract_nodes(self, mermaid_code: str) -> List[Dict]:
        import re
        nodes = []
        
        # 提取节点定义
        pattern = r'(\w+)\[([^\]]+)\]'
        for match in re.finditer(pattern, mermaid_code):
            nodes.append({
                "id": match.group(1),
                "label": match.group(2)
            })
        
        return nodes
```

### 验收标准
- [ ] 可生成Mermaid代码
- [ ] 语法正确可渲染
- [ ] 节点信息可提取

### 提交信息
```
feat(graph): add mermaid flowchart generator
```

---

## 任务 5.2：架构图生成

### 描述
基于模块分析生成系统架构图。

### 执行步骤

1. 创建架构图生成器 `app/graph/arch_generator.py`
```python
from typing import Dict, List
from app.analysis.feature_tree_builder import FeatureTreeBuilder

ARCH_PROMPT = """基于以下项目结构信息，生成系统架构图。

模块信息：
{modules}

要求：
1. 使用Mermaid graph TB语法
2. 使用subgraph分组相关模块
3. 清晰展示模块间的依赖关系
4. 使用中文标签

请直接输出Mermaid代码："""

class ArchGenerator:
    def __init__(self):
        self.feature_builder = FeatureTreeBuilder
    
    async def generate(self, feature_tree: Dict) -> Dict:
        modules = self._extract_modules(feature_tree)
        
        # 自动生成架构图
        mermaid_code = self._auto_generate(modules)
        
        return {
            "type": "architecture",
            "format": "mermaid",
            "content": mermaid_code,
            "modules": modules
        }
    
    def _extract_modules(self, feature_tree: Dict) -> List[Dict]:
        modules = []
        
        # 提取前端模块
        if "frontend" in feature_tree:
            for child in feature_tree["frontend"].get("children", []):
                modules.append({
                    "name": child["name"],
                    "type": "frontend",
                    "category": child.get("type", "page")
                })
        
        # 提取后端模块
        if "backend" in feature_tree:
            for child in feature_tree["backend"].get("children", []):
                modules.append({
                    "name": child["name"],
                    "type": "backend",
                    "category": child.get("type", "api")
                })
        
        return modules
    
    def _auto_generate(self, modules: List[Dict]) -> str:
        lines = ["graph TB"]
        
        # 前端子图
        frontend_modules = [m for m in modules if m["type"] == "frontend"]
        if frontend_modules:
            lines.append("    subgraph Frontend[前端]")
            for m in frontend_modules[:10]:  # 限制数量
                node_id = f"f_{m['name'].replace(' ', '_')}"
                lines.append(f"        {node_id}[{m['name']}]")
            lines.append("    end")
        
        # 后端子图
        backend_modules = [m for m in modules if m["type"] == "backend"]
        if backend_modules:
            lines.append("    subgraph Backend[后端]")
            for m in backend_modules[:10]:
                node_id = f"b_{m['name'].replace(' ', '_')}"
                lines.append(f"        {node_id}[{m['name']}]")
            lines.append("    end")
        
        # 数据库
        lines.append("    DB[(数据库)]")
        
        # 添加连接
        if frontend_modules and backend_modules:
            lines.append("    Frontend --> Backend")
        if backend_modules:
            lines.append("    Backend --> DB")
        
        return "\n".join(lines)
```

### 验收标准
- [ ] 可生成架构图
- [ ] 模块正确分组
- [ ] 依赖关系清晰

### 提交信息
```
feat(graph): add architecture diagram generator
```

---

## 任务 5.3：调用图可视化

### 描述
将调用链分析结果可视化。

### 执行步骤

1. 创建调用图可视化器 `app/graph/call_graph_visualizer.py`
```python
from typing import Dict, List
from app.graph.call_graph import CallGraphBuilder

class CallGraphVisualizer:
    def to_mermaid(self, call_graph: Dict) -> str:
        nodes = call_graph["nodes"]
        edges = call_graph["edges"]
        
        lines = ["graph TD"]
        
        # 添加节点
        for node_id, node in nodes.items():
            label = node.name
            if node.type == "method":
                label = f"{node.name}"
            lines.append(f'    {self._safe_id(node_id)}["{label}"]')
        
        # 添加边
        for edge in edges:
            lines.append(f"    {self._safe_id(edge.caller)} --> {self._safe_id(edge.callee)}")
        
        return "\n".join(lines)
    
    def to_json(self, call_graph: Dict) -> Dict:
        """转换为前端可用的JSON格式"""
        nodes = []
        edges = []
        
        for node_id, node in call_graph["nodes"].items():
            nodes.append({
                "id": node_id,
                "label": node.name,
                "file": node.file_path,
                "line": node.line,
                "type": node.type
            })
        
        for i, edge in enumerate(call_graph["edges"]):
            edges.append({
                "id": f"e{i}",
                "source": edge.caller,
                "target": edge.callee
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def _safe_id(self, id: str) -> str:
        # 替换特殊字符
        return id.replace(":", "_").replace("/", "_").replace(".", "_")
```

### 验收标准
- [ ] 可转换为Mermaid
- [ ] 可转换为JSON
- [ ] 支持前端渲染

### 提交信息
```
feat(graph): add call graph visualizer
```

---

## 任务 5.4：前端图表渲染

### 描述
在前端集成Mermaid和ReactFlow渲染。

### 执行步骤

1. 安装依赖
```bash
npm install mermaid reactflow
```

2. 创建Mermaid组件 `src/components/graph/MermaidChart.tsx`
```tsx
import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

interface Props {
  code: string
  className?: string
}

export function MermaidChart({ code, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      securityLevel: 'loose',
    })
    
    if (ref.current) {
      mermaid.render('mermaid-svg', code).then(({ svg }) => {
        ref.current!.innerHTML = svg
      })
    }
  }, [code])
  
  return <div ref={ref} className={className} />
}
```

3. 创建流程图页面 `src/pages/FlowChart.tsx`
```tsx
import { useState, useEffect } from 'react'
import { MermaidChart } from '@/components/graph/MermaidChart'
import { api } from '@/services/api'

interface Props {
  projectId: string
}

export function FlowChart({ projectId }: Props) {
  const [flowData, setFlowData] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [selectedFunction, setSelectedFunction] = useState('')
  
  const generateFlow = async () => {
    if (!selectedFunction) return
    
    setLoading(true)
    const res = await api.get(`/graph/${projectId}/flow`, {
      params: { entry: selectedFunction }
    })
    setFlowData(res.data.data.content)
    setLoading(false)
  }
  
  return (
    <div className="p-6">
      <div className="mb-4">
        <select 
          value={selectedFunction}
          onChange={e => setSelectedFunction(e.target.value)}
        >
          <option value="">选择入口函数</option>
        </select>
        <button onClick={generateFlow}>生成流程图</button>
      </div>
      
      {loading && <div>生成中...</div>}
      
      {flowData && (
        <div className="border rounded-lg p-4">
          <MermaidChart code={flowData} />
        </div>
      )}
    </div>
  )
}
```

### 验收标准
- [ ] Mermaid可渲染
- [ ] 流程图可交互
- [ ] 样式正常

### 提交信息
```
feat(ui): add mermaid chart rendering component
```

---

## 任务 5.5：功能详情页

### 描述
创建前后端功能展示界面。

### 执行步骤

1. 创建功能树组件 `src/components/features/FeatureTree.tsx`
```tsx
import { useState } from 'react'

interface FeatureNode {
  id: string
  name: string
  type: string
  children: FeatureNode[]
}

interface Props {
  data: FeatureNode
  onSelect: (node: FeatureNode) => void
}

export function FeatureTree({ data, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false)
  
  const hasChildren = data.children && data.children.length > 0
  
  return (
    <div className="ml-4">
      <div 
        className="flex items-center p-2 hover:bg-gray-100 cursor-pointer rounded"
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren && (
          <span className="mr-2">{expanded ? '▼' : '▶'}</span>
        )}
        <span>{data.name}</span>
        <span className="ml-2 text-xs text-gray-500">{data.type}</span>
      </div>
      
      {expanded && hasChildren && (
        <div className="border-l ml-3 pl-2">
          {data.children.map(child => (
            <FeatureTree 
              key={child.id} 
              data={child} 
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}
```

2. 创建功能详情页 `src/pages/Features.tsx`
```tsx
import { useState, useEffect } from 'react'
import { FeatureTree } from '@/components/features/FeatureTree'
import { api } from '@/services/api'

interface Props {
  projectId: string
}

export function Features({ projectId }: Props) {
  const [featureTree, setFeatureTree] = useState(null)
  const [selectedFeature, setSelectedFeature] = useState(null)
  const [activeTab, setActiveTab] = useState('frontend')
  
  useEffect(() => {
    fetchFeatures()
  }, [projectId])
  
  const fetchFeatures = async () => {
    const res = await api.get(`/features/${projectId}`)
    setFeatureTree(res.data.data)
  }
  
  return (
    <div className="flex h-full">
      {/* 左侧树形结构 */}
      <div className="w-80 border-r overflow-auto">
        <div className="flex border-b">
          <button 
            className={`flex-1 p-2 ${activeTab === 'frontend' ? 'bg-blue-50' : ''}`}
            onClick={() => setActiveTab('frontend')}
          >
            前端
          </button>
          <button 
            className={`flex-1 p-2 ${activeTab === 'backend' ? 'bg-blue-50' : ''}`}
            onClick={() => setActiveTab('backend')}
          >
            后端
          </button>
        </div>
        
        {featureTree && (
          <FeatureTree 
            data={featureTree[activeTab]} 
            onSelect={setSelectedFeature}
          />
        )}
      </div>
      
      {/* 右侧详情 */}
      <div className="flex-1 p-6 overflow-auto">
        {selectedFeature ? (
          <FeatureDetail feature={selectedFeature} />
        ) : (
          <div className="text-gray-500">选择一个功能查看详情</div>
        )}
      </div>
    </div>
  )
}
```

### 验收标准
- [ ] 功能树可展示
- [ ] 可展开/折叠
- [ ] 详情可显示

### 提交信息
```
feat(ui): add feature detail page with tree view
```

---

## 任务 5.6：API文档生成

### 描述
自动生成API文档。

### 执行步骤

1. 创建API文档生成器 `app/docs/api_doc.py`
```python
from typing import List, Dict
from app.analysis.api_extractor import APIEndpoint

class APIDocGenerator:
    def generate(self, apis: List[APIEndpoint]) -> str:
        lines = ["# API 文档\n"]
        
        # 按模块分组
        grouped = self._group_by_module(apis)
        
        for module, module_apis in grouped.items():
            lines.append(f"## {module}\n")
            
            for api in module_apis:
                lines.append(f"### {api.method} {api.path}\n")
                
                if api.description:
                    lines.append(f"{api.description}\n")
                
                lines.append(f"- **文件位置**: `{api.file_path}:{api.line}`")
                lines.append(f"- **认证**: {'需要' if api.auth_required else '不需要'}\n")
                
                if api.params:
                    lines.append("**参数**\n")
                    lines.append("| 名称 | 类型 | 必填 | 说明 |")
                    lines.append("|------|------|------|------|")
                    for param in api.params:
                        lines.append(f"| {param.get('name', '')} | {param.get('type', '')} | {'是' if param.get('required') else '否'} | {param.get('description', '')} |")
                    lines.append("")
                
                lines.append("---\n")
        
        return "\n".join(lines)
    
    def _group_by_module(self, apis: List[APIEndpoint]) -> Dict[str, List[APIEndpoint]]:
        grouped = {}
        for api in apis:
            module = self._extract_module(api.path)
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(api)
        return grouped
    
    def _extract_module(self, path: str) -> str:
        parts = path.strip("/").split("/")
        if len(parts) > 1:
            return parts[0].title()
        return "Default"
```

### 验收标准
- [ ] 可生成Markdown文档
- [ ] API正确分组
- [ ] 参数信息完整

### 提交信息
```
feat(docs): add API documentation generator
```

---

## 任务 5.7：项目文档生成

### 描述
自动生成README和架构文档。

### 执行步骤

1. 创建文档生成器 `app/docs/readme_gen.py`
```python
from typing import Dict
from app.llm.openai_service import OpenAIService

README_PROMPT = """基于以下项目信息，生成一个专业的README.md文档。

项目名称: {name}
技术栈: {tech_stack}
主要功能: {features}
项目结构: {structure}

要求：
1. 包含项目简介
2. 技术栈说明
3. 快速开始指南
4. 项目结构说明
5. 主要功能列表
6. 使用Markdown格式

请直接输出README内容："""

class ReadmeGenerator:
    def __init__(self):
        self.llm = OpenAIService()
    
    async def generate(self, project_info: Dict) -> str:
        prompt = README_PROMPT.format(
            name=project_info.get("name", "Project"),
            tech_stack=", ".join(project_info.get("tech_stack", [])),
            features="\n".join([f"- {f}" for f in project_info.get("features", [])]),
            structure=project_info.get("structure", "")
        )
        
        messages = [
            {"role": "system", "content": "你是一个专业的技术文档撰写专家。"},
            {"role": "user", "content": prompt}
        ]
        
        return await self.llm.generate(messages, temperature=0.5)
```

### 验收标准
- [ ] 可生成README
- [ ] 内容完整专业
- [ ] Markdown格式正确

### 提交信息
```
feat(docs): add README documentation generator
```

---

## 任务 5.8：文档导出

### 描述
支持Markdown/PDF/HTML导出。

### 执行步骤

1. 创建导出器 `app/docs/exporter.py`
```python
from typing import Literal
import markdown
from pathlib import Path

class DocumentExporter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self, 
        content: str, 
        filename: str, 
        format: Literal["markdown", "html", "pdf"]
    ) -> str:
        if format == "markdown":
            return self._export_markdown(content, filename)
        elif format == "html":
            return self._export_html(content, filename)
        elif format == "pdf":
            return self._export_pdf(content, filename)
    
    def _export_markdown(self, content: str, filename: str) -> str:
        path = self.output_dir / f"{filename}.md"
        path.write_text(content, encoding="utf-8")
        return str(path)
    
    def _export_html(self, content: str, filename: str) -> str:
        html = markdown.markdown(
            content, 
            extensions=["tables", "fenced_code", "toc"]
        )
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{filename}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                pre {{ background: #f5f5f5; padding: 15px; overflow-x: auto; }}
                code {{ background: #f5f5f5; padding: 2px 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        path = self.output_dir / f"{filename}.html"
        path.write_text(full_html, encoding="utf-8")
        return str(path)
    
    def _export_pdf(self, content: str, filename: str) -> str:
        # 使用 weasyprint 或 pdfkit
        try:
            from weasyprint import HTML
            html_content = markdown.markdown(content, extensions=["tables", "fenced_code"])
            html = HTML(string=f"<html><body>{html_content}</body></html>")
            path = self.output_dir / f"{filename}.pdf"
            html.write_pdf(str(path))
            return str(path)
        except ImportError:
            raise RuntimeError("weasyprint not installed")
```

### 验收标准
- [ ] Markdown导出正常
- [ ] HTML导出正常
- [ ] PDF导出正常

### 提交信息
```
feat(docs): add document exporter with multiple formats
```

---

## Phase 5 完成标准

- [ ] 流程图可生成
- [ ] 架构图可生成
- [ ] 调用图可可视化
- [ ] 前端图表可渲染
- [ ] 功能详情页可用
- [ ] API文档可生成
- [ ] README可生成
- [ ] 文档可导出

## 下一阶段

完成 Phase 5 后，进入 Phase 6: 优化与完善
