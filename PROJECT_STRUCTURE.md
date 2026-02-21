# CodeInsight 项目结构

**项目根目录**: `C:\Users\Alan ZA Zhang\Desktop\newcode\code-insight`

---

## 📁 目录结构

```
code-insight/                      # 主项目根目录
├── backend/                       # 后端服务
│   ├── app/
│   │   ├── api/                  # API路由
│   │   ├── core/                 # 核心配置
│   │   ├── models/               # 数据库模型
│   │   ├── parsers/              # 代码解析器
│   │   ├── services/             # 业务服务
│   │   └── main.py              # FastAPI应用入口
│   ├── tests/                    # 测试文件
│   ├── requirements.txt          # Python依赖
│   └── ...
│
├── frontend/                     # 前端服务
│   ├── src/
│   │   ├── components/          # React组件
│   │   ├── services/            # API服务
│   │   ├── App.tsx              # 主应用
│   │   └── main.tsx             # 入口文件
│   ├── package.json             # Node依赖
│   └── ...
│
├── docs/                         # 文档目录
│   ├── plans/                   # 设计和计划文档
│   │   ├── 2026-02-21-codeinsight-implementation-design.md
│   │   └── 2026-02-21-phase1-phase2-implementation.md
│   ├── api-design.md            # API设计
│   ├── architecture.md          # 架构设计
│   └── requirements.md          # 需求文档
│
├── plans/                        # 原始计划文档
│   ├── phase-1-foundation.md
│   └── phase-2-parser.md
│
├── docker-compose.yml           # Docker配置
├── README.md                    # 项目说明
├── AI-RULES.md                  # AI规则
└── DEPLOYMENT_RECORD.md         # 部署记录
```

---

## 🎯 核心功能模块

### 1. 后端 (Backend)
- **技术栈**: FastAPI + Python 3.8+ + SQLite
- **端口**: http://localhost:8000
- **主要功能**:
  - 项目管理 (导入、列表、详情、删除)
  - 代码解析 (Python, JavaScript, TypeScript)
  - API接口服务

### 2. 前端 (Frontend)
- **技术栈**: React 18 + TypeScript + TailwindCSS + Vite
- **端口**: http://localhost:5173
- **主要功能**:
  - 项目管理界面
  - 代码结构展示
  - 智能问答界面

### 3. 代码解析器 (Parsers)
- **技术**: Tree-sitter 0.21
- **支持语言**: Python, JavaScript, TypeScript
- **提取信息**: 函数、类、导入、变量、调用关系

### 4. 数据库 (Database)
- **类型**: SQLite
- **位置**: `backend/data/codeinsight.db`
- **模型**: Project, File, Chat, Feature

---

## 🚀 快速启动

### 启动后端
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 启动前端
```bash
cd frontend
npm run dev
```

### 访问应用
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

---

## 📊 测试覆盖

### 后端测试
```bash
cd backend
pytest tests/ -v
```

**测试结果**:
- 模型测试: 17/17 ✅ (100%)
- 解析器测试: 18/18 ✅ (100%)
- **总计**: 35/35 ✅ (100%)

### 系统集成测试
```bash
python test_system.py
```

**测试结果**:
- ✅ 后端健康检查
- ✅ 项目创建
- ✅ 项目列表
- ✅ 项目详情
- ✅ 前端访问
- ✅ 前后端交互

---

## 📝 文档说明

### 设计文档
- `docs/plans/2026-02-21-codeinsight-implementation-design.md` - 完整系统设计
- `docs/plans/2026-02-21-phase1-phase2-implementation.md` - 详细实施计划

### 原始计划
- `plans/phase-1-foundation.md` - Phase 1基础框架
- `plans/phase-2-parser.md` - Phase 2代码解析引擎

---

## 🔧 开发进度

### ✅ 已完成 (Phase 1 & Phase 2)
- [x] 数据库模型完善 (17个测试通过)
- [x] 项目导入API (本地导入、列表、详情、删除)
- [x] Tree-sitter集成 (Python, JS, TS解析器)
- [x] 代码结构提取 (函数、类、导入、变量)
- [x] 参数名称提取修复 (100%测试通过)
- [x] Import模块解析修复 (100%测试通过)
- [x] 返回类型清理修复 (100%测试通过)

### 🚧 进行中 (Phase 3)
- [ ] RAG系统集成
- [ ] 向量化存储 (ChromaDB)
- [ ] 智能问答功能
- [ ] 多轮对话支持

### 📋 待开发 (Phase 4+)
- [ ] 可视化功能
- [ ] 更多语言支持
- [ ] 性能优化
- [ ] 部署优化

---

## 🎉 项目状态

**当前版本**: v1.0-alpha  
**最后更新**: 2026-02-21  
**测试覆盖**: 100% (35/35测试通过)  
**系统状态**: 
- ✅ 后端运行正常
- ✅ 前端运行正常
- ✅ 前后端交互正常
- ✅ 代码解析功能完整

---

## 📞 开发者信息

**Git提交记录**:
```
74573d3 - fix(parsers): fix parameter name extraction, import module parsing, and return type cleaning
c31b043 - fix(parsers): fix tree-sitter initialization for all parsers
3ad9de2 - feat(api): add to_dict method to Project model and update API responses
8640eb2 - feat(models): add relationships and missing fields to database models
948294b - docs: add Phase 1 & Phase 2 detailed implementation plan
2d41290 - docs: add CodeInsight implementation design document
```

**开发团队**: CodeInsight Team  
**开发方式**: 使用Superpowers技能集进行TDD开发

---

**注意**: 此项目结构已清理，移除了重复的内层目录。所有开发工作都在外层 `code-insight/` 目录进行。
