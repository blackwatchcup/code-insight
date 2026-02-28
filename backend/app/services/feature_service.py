import os
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
