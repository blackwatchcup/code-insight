import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.analysis.api_call_analyzer import APICallAnalyzer, APICallInfo
from app.analysis.api_extractor import APIEndpoint, APIExtractor
from app.analysis.feature_detector import SystemFeature, SystemFeatureDetector
from app.analysis.feature_tree import FeatureNode, FeatureTree, FeatureTreeBuilder
from app.analysis.frontend_analyzer import FrontendAnalyzer, PageFunction
from app.analysis.model_extractor import DataModel, ModelExtractor
from app.analysis.route_parser import RouteInfo, RouteParser
from app.core.config import settings
from app.llm.service import LLMService


class FeatureService:
    def __init__(self, db: Session = None):
        self.db = db
        self.route_parser = RouteParser()
        self.frontend_analyzer = FrontendAnalyzer()
        self.api_call_analyzer = APICallAnalyzer()
        self.api_extractor = APIExtractor()
        self.feature_detector = SystemFeatureDetector()
        self.model_extractor = ModelExtractor()

    async def analyze_project(self, project_path: str, project_id: str) -> FeatureTree:
        routes: List[RouteInfo] = []
        page_functions: Dict[str, List[PageFunction]] = {}
        api_calls: Dict[str, List[APICallInfo]] = {}
        apis: List[APIEndpoint] = []
        system_features: List[SystemFeature] = []
        models: List[DataModel] = []

        project_dir = Path(project_path)

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file():
                continue

            if self._should_skip(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                relative_path = str(file_path.relative_to(project_dir))

                if self._is_frontend_file(file_path):
                    file_routes = self.route_parser.parse(content, str(file_path))
                    routes.extend(file_routes)

                    functions = self.frontend_analyzer.extract_functions(content, str(file_path))
                    if functions:
                        page_functions[relative_path] = functions

                    calls = self.api_call_analyzer.analyze(content, str(file_path))
                    if calls:
                        api_calls[relative_path] = calls

                if self._is_backend_file(file_path):
                    file_apis = self.api_extractor.extract(content, str(file_path))
                    apis.extend(file_apis)

                    file_models = self.model_extractor.extract(content, str(file_path))
                    models.extend(file_models)

                features = self.feature_detector.detect(content, str(file_path))
                system_features.extend(features)

            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue

        builder = FeatureTreeBuilder(project_id)
        tree = builder.build(
            routes=routes,
            page_functions=page_functions,
            api_calls=api_calls,
            apis=apis,
            system_features=system_features,
            models=models,
        )

        return tree

    async def get_feature_tree(self, project_id: str, project_path: str) -> FeatureTree:
        return await self.analyze_project(project_path, project_id)

    async def get_frontend_features(self, project_path: str) -> Dict:
        routes: List[RouteInfo] = []
        page_functions: Dict[str, List[PageFunction]] = {}
        api_calls: Dict[str, List[APICallInfo]] = {}

        project_dir = Path(project_path)

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file() or self._should_skip(file_path):
                continue

            if not self._is_frontend_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                relative_path = str(file_path.relative_to(project_dir))

                file_routes = self.route_parser.parse(content, str(file_path))
                routes.extend(file_routes)

                functions = self.frontend_analyzer.extract_functions(content, str(file_path))
                if functions:
                    page_functions[relative_path] = functions

                calls = self.api_call_analyzer.analyze(content, str(file_path))
                if calls:
                    api_calls[relative_path] = calls

            except Exception:
                continue

        return {
            "routes": [r.to_dict() for r in routes],
            "page_functions": {k: [f.to_dict() for f in v] for k, v in page_functions.items()},
            "api_calls": {k: [c.to_dict() for c in v] for k, v in api_calls.items()},
        }

    async def get_backend_features(self, project_path: str) -> Dict:
        api_dict: Dict[str, APIEndpoint] = {}
        system_features: List[SystemFeature] = []
        models: List[DataModel] = []

        project_dir = Path(project_path)

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file() or self._should_skip(file_path):
                continue

            if not self._is_backend_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                file_apis = self.api_extractor.extract(content, str(file_path))
                # 去重处理 API 端点
                for api in file_apis:
                    key = f"{api.method}{api.path}"
                    if key not in api_dict:
                        api_dict[key] = api

                file_models = self.model_extractor.extract(content, str(file_path))
                models.extend(file_models)

                features = self.feature_detector.detect(content, str(file_path))
                system_features.extend(features)

            except Exception:
                continue

        return {
            "apis": [a.to_dict() for a in api_dict.values()],
            "system_features": [f.to_dict() for f in system_features],
            "models": [m.to_dict() for m in models],
        }

    async def get_api_endpoints(self, project_path: str) -> List[Dict]:
        api_dict: Dict[str, APIEndpoint] = {}
        project_dir = Path(project_path)

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file() or self._should_skip(file_path):
                continue

            if not self._is_backend_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                file_apis = self.api_extractor.extract(content, str(file_path))
                
                # 去重处理，使用 method + path 作为唯一键
                for api in file_apis:
                    key = f"{api.method}{api.path}"
                    if key not in api_dict:
                        api_dict[key] = api
            except Exception:
                continue

        return [a.to_dict() for a in api_dict.values()]

    async def get_data_models(self, project_path: str) -> List[Dict]:
        models: List[DataModel] = []
        project_dir = Path(project_path)

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file() or self._should_skip(file_path):
                continue

            if not self._is_backend_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                file_models = self.model_extractor.extract(content, str(file_path))
                models.extend(file_models)
            except Exception:
                continue

        return [m.to_dict() for m in models]

    async def get_system_features(self, project_path: str) -> List[Dict]:
        features: List[SystemFeature] = []
        project_dir = Path(project_path)

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file() or self._should_skip(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                file_features = self.feature_detector.detect(content, str(file_path))
                features.extend(file_features)
            except Exception:
                continue

        return [f.to_dict() for f in features]

    async def get_feature_insights(self, project_path: str, include_llm: bool = False) -> Dict[str, Any]:
        frontend_data = await self.get_frontend_features(project_path)
        backend_data = await self.get_backend_features(project_path)

        frontend_summary = self._build_frontend_summary(frontend_data)
        backend_summary = self._build_backend_summary(backend_data)

        insights: Dict[str, Any] = {
            "frontend": frontend_summary,
            "backend": backend_summary,
            "llm": {
                "enabled": False,
                "frontend_summary": "",
                "backend_summary": "",
                "model": settings.OPENAI_MODEL,
                "error": "",
            },
        }

        if include_llm:
            llm_result = await self._generate_llm_feature_summaries(frontend_summary, backend_summary)
            insights["llm"] = llm_result

        return insights

    def _build_frontend_summary(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        routes = frontend_data.get("routes", [])
        page_functions = frontend_data.get("page_functions", {})
        api_calls = frontend_data.get("api_calls", {})

        function_items: List[Dict[str, Any]] = []
        for items in page_functions.values():
            if isinstance(items, list):
                function_items.extend(items)

        api_call_items: List[Dict[str, Any]] = []
        for items in api_calls.values():
            if isinstance(items, list):
                api_call_items.extend(items)

        file_counter = Counter()
        type_counter = Counter()
        route_paths: List[str] = []
        route_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        function_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        api_call_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for route in routes:
            file_path = route.get("file_path", "")
            if file_path:
                file_counter[file_path] += 1
                route_by_file[file_path].append(route)
            path = route.get("path", "")
            if path:
                route_paths.append(path)

        for item in function_items:
            file_path = item.get("file_path", "")
            if file_path:
                file_counter[file_path] += 1
                function_by_file[file_path].append(item)
            type_name = item.get("type", "unknown")
            type_counter[type_name] += 1

        for item in api_call_items:
            file_path = item.get("file_path", "")
            if file_path:
                file_counter[file_path] += 1
                api_call_by_file[file_path].append(item)

        highlights: List[str] = []
        if len(route_paths) > 20:
            highlights.append("前端路由规模较大，建议梳理路由分组与懒加载策略")
        if type_counter.get("state", 0) > 30:
            highlights.append("状态管理相关逻辑较多，建议检查状态边界与复用")
        if len(api_call_items) > 40:
            highlights.append("页面内 API 调用较密集，可考虑统一请求封装与缓存策略")
        if not highlights:
            highlights.append("前端功能结构整体清晰，可继续按页面域拆分模块")

        page_analyses: List[Dict[str, Any]] = []
        all_files = sorted(
            set(route_by_file.keys())
            | set(function_by_file.keys())
            | set(api_call_by_file.keys())
        )
        for file_path in all_files:
            file_routes = route_by_file.get(file_path, [])
            file_functions = function_by_file.get(file_path, [])
            file_api_calls = api_call_by_file.get(file_path, [])

            file_type_counter = Counter()
            for item in file_functions:
                file_type_counter[item.get("type", "unknown")] += 1

            file_highlights: List[str] = []
            if len(file_routes) >= 3:
                file_highlights.append("该页面承载多路由入口，建议检查路由守卫与加载性能")
            if file_type_counter.get("state", 0) >= 4:
                file_highlights.append("状态管理逻辑较多，建议拆分状态域并减少耦合")
            if len(file_api_calls) >= 4:
                file_highlights.append("接口调用较集中，建议增加防抖/缓存与错误兜底")
            if not file_highlights:
                file_highlights.append("页面职责相对聚焦，可继续保持组件边界清晰")

            page_analyses.append(
                {
                    "name": Path(file_path).name,
                    "file_path": file_path,
                    "route_count": len(file_routes),
                    "page_function_count": len(file_functions),
                    "api_call_count": len(file_api_calls),
                    "top_types": [
                        {"name": name, "count": count}
                        for name, count in file_type_counter.most_common(3)
                    ],
                    "sample_routes": [route.get("path", "") for route in file_routes[:5]],
                    "highlights": file_highlights,
                }
            )

        return {
            "overview": (
                f"识别到 {len(routes)} 个路由、{len(function_items)} 个页面交互功能、"
                f"{len(api_call_items)} 个前端 API 调用。"
            ),
            "metrics": {
                "route_count": len(routes),
                "page_function_count": len(function_items),
                "api_call_count": len(api_call_items),
                "active_file_count": len(file_counter),
            },
            "top_types": [
                {"name": name, "count": count}
                for name, count in type_counter.most_common(6)
            ],
            "top_files": [
                {"name": name, "count": count}
                for name, count in file_counter.most_common(6)
            ],
            "sample_routes": route_paths[:8],
            "highlights": highlights,
            "page_analyses": page_analyses,
        }

    def _build_backend_summary(self, backend_data: Dict[str, Any]) -> Dict[str, Any]:
        apis = backend_data.get("apis", [])
        system_features = backend_data.get("system_features", [])
        models = backend_data.get("models", [])

        api_method_counter = Counter()
        api_group_counter = Counter()
        file_counter = Counter()
        feature_type_counter = Counter()
        api_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        model_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        system_feature_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        auth_required_count = 0

        for api in apis:
            method = (api.get("method", "UNKNOWN") or "UNKNOWN").upper()
            api_method_counter[method] += 1

            path = api.get("path", "")
            normalized = path.strip("/")
            group = normalized.split("/")[0] if normalized else "root"
            api_group_counter[group] += 1

            if api.get("auth_required"):
                auth_required_count += 1

            file_path = api.get("file_path", "")
            if file_path:
                file_counter[file_path] += 1
                api_by_file[file_path].append(api)

        for feature in system_features:
            feature_type = feature.get("type", "unknown")
            feature_type_counter[feature_type] += 1
            file_path = feature.get("file_path", "")
            if file_path:
                file_counter[file_path] += 1
                system_feature_by_file[file_path].append(feature)

        for model in models:
            file_path = model.get("file_path", "")
            if file_path:
                file_counter[file_path] += 1
                model_by_file[file_path].append(model)

        highlights: List[str] = []
        if len(apis) > 50:
            highlights.append("后端 API 数量较多，建议按业务域拆分路由与服务层")
        if len(models) > 20:
            highlights.append("数据模型较多，建议明确领域边界并梳理聚合关系")
        if auth_required_count and auth_required_count < len(apis) * 0.3:
            highlights.append("鉴权 API 占比较低，建议复核敏感接口的访问控制")
        if feature_type_counter.get("middleware", 0) > 8:
            highlights.append("中间件配置较多，建议检查顺序与职责是否清晰")
        if not highlights:
            highlights.append("后端功能分层较完整，建议继续增强可观测性与错误治理")

        page_analyses: List[Dict[str, Any]] = []
        all_files = sorted(
            set(api_by_file.keys()) | set(model_by_file.keys()) | set(system_feature_by_file.keys())
        )
        for file_path in all_files:
            file_apis = api_by_file.get(file_path, [])
            file_models = model_by_file.get(file_path, [])
            file_system_features = system_feature_by_file.get(file_path, [])

            file_method_counter = Counter()
            auth_api_count = 0
            sample_api_paths: List[str] = []
            for api in file_apis:
                method = (api.get("method", "UNKNOWN") or "UNKNOWN").upper()
                file_method_counter[method] += 1
                if api.get("auth_required"):
                    auth_api_count += 1
                if api.get("path"):
                    sample_api_paths.append(api.get("path"))

            file_feature_counter = Counter()
            for feature in file_system_features:
                file_feature_counter[feature.get("type", "unknown")] += 1

            file_highlights: List[str] = []
            if len(file_apis) >= 6:
                file_highlights.append("该文件接口数量较多，建议拆分路由模块")
            if len(file_models) >= 3:
                file_highlights.append("模型聚合度较高，建议评估领域边界")
            if len(file_system_features) >= 5:
                file_highlights.append("基础能力配置较集中，建议提取公共基础设施层")
            if auth_api_count and auth_api_count < len(file_apis) * 0.3:
                file_highlights.append("鉴权覆盖偏低，建议检查敏感接口权限")
            if not file_highlights:
                file_highlights.append("文件职责较清晰，可继续保持单一职责")

            page_analyses.append(
                {
                    "name": Path(file_path).name,
                    "file_path": file_path,
                    "api_count": len(file_apis),
                    "model_count": len(file_models),
                    "system_feature_count": len(file_system_features),
                    "auth_api_count": auth_api_count,
                    "top_api_methods": [
                        {"name": name, "count": count}
                        for name, count in file_method_counter.most_common(3)
                    ],
                    "top_system_features": [
                        {"name": name, "count": count}
                        for name, count in file_feature_counter.most_common(3)
                    ],
                    "sample_api_paths": sample_api_paths[:5],
                    "highlights": file_highlights,
                }
            )

        return {
            "overview": (
                f"识别到 {len(apis)} 个后端 API、{len(models)} 个数据模型、"
                f"{len(system_features)} 个系统能力特征。"
            ),
            "metrics": {
                "api_count": len(apis),
                "model_count": len(models),
                "system_feature_count": len(system_features),
                "auth_api_count": auth_required_count,
                "active_file_count": len(file_counter),
            },
            "top_api_methods": [
                {"name": name, "count": count}
                for name, count in api_method_counter.most_common(6)
            ],
            "top_api_groups": [
                {"name": name, "count": count}
                for name, count in api_group_counter.most_common(6)
            ],
            "top_system_features": [
                {"name": name, "count": count}
                for name, count in feature_type_counter.most_common(6)
            ],
            "top_files": [
                {"name": name, "count": count}
                for name, count in file_counter.most_common(6)
            ],
            "highlights": highlights,
            "page_analyses": page_analyses,
        }

    async def _generate_llm_feature_summaries(
        self,
        frontend_summary: Dict[str, Any],
        backend_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        llm_api_key = (
            settings.OPENAI_API_KEY
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

        if not llm_api_key:
            return {
                "enabled": False,
                "frontend_summary": "",
                "backend_summary": "",
                "model": settings.OPENAI_MODEL,
                "error": "LLM 未配置 API Key，已返回规则分析结果",
            }

        llm_service = LLMService()

        frontend_prompt = (
            "请基于以下前端功能统计，输出 4~6 句中文总结，包含："
            "整体规模、主要交互模式、潜在复杂度风险、可执行优化建议。\n\n"
            f"统计数据: {frontend_summary}"
        )
        backend_prompt = (
            "请基于以下后端功能统计，输出 4~6 句中文总结，包含："
            "整体规模、API 结构特征、系统能力覆盖、可执行优化建议。\n\n"
            f"统计数据: {backend_summary}"
        )

        try:
            frontend_text, backend_text = await asyncio.gather(
                llm_service.generate(
                    frontend_prompt,
                    system_prompt="你是资深软件架构师，请给出清晰、可执行、简洁的技术总结。",
                ),
                llm_service.generate(
                    backend_prompt,
                    system_prompt="你是资深软件架构师，请给出清晰、可执行、简洁的技术总结。",
                ),
            )

            return {
                "enabled": True,
                "frontend_summary": frontend_text or "",
                "backend_summary": backend_text or "",
                "model": settings.OPENAI_MODEL,
                "error": "",
            }
        except Exception as exc:
            return {
                "enabled": False,
                "frontend_summary": "",
                "backend_summary": "",
                "model": settings.OPENAI_MODEL,
                "error": str(exc),
            }

    def _should_skip(self, file_path: Path) -> bool:
        skip_dirs = {
            ".git",
            ".github",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "coverage",
            ".pytest_cache",
            "migrations",
            "docs",
        }

        for part in file_path.parts:
            if part in skip_dirs:
                return True

        if file_path.suffix in [".min.js", ".min.css", ".map", ".lock", ".log"]:
            return True

        return False

    def _is_frontend_file(self, file_path: Path) -> bool:
        frontend_extensions = {".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte"}
        return file_path.suffix in frontend_extensions

    def _is_backend_file(self, file_path: Path) -> bool:
        backend_extensions = {".py", ".java", ".go", ".rs", ".rb", ".php", ".cs"}
        return file_path.suffix in backend_extensions
