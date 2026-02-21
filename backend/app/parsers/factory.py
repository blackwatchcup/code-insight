from typing import Dict, Type, Optional, List
from app.parsers.base import BaseParser


class ParserFactory:
    _parsers: Dict[str, Type[BaseParser]] = {}
    _extension_map: Dict[str, str] = {}

    @classmethod
    def register(cls, language: str, parser_class: Type[BaseParser], extensions: Optional[List[str]] = None):
        cls._parsers[language] = parser_class
        if extensions:
            for ext in extensions:
                ext_normalized = ext.lower().lstrip(".")
                cls._extension_map[ext_normalized] = language

    @classmethod
    def get_parser(cls, language: str) -> BaseParser:
        if language not in cls._parsers:
            raise ValueError(f"Unsupported language: {language}")
        return cls._parsers[language]()

    @classmethod
    def get_parser_by_extension(cls, extension: str) -> Optional[BaseParser]:
        ext_normalized = extension.lower().lstrip(".")
        if ext_normalized not in cls._extension_map:
            return None
        language = cls._extension_map[ext_normalized]
        return cls.get_parser(language)

    @classmethod
    def supported_languages(cls) -> List[str]:
        return list(cls._parsers.keys())

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return list(cls._extension_map.keys())

    @classmethod
    def get_language_for_extension(cls, extension: str) -> Optional[str]:
        ext_normalized = extension.lower().lstrip(".")
        return cls._extension_map.get(ext_normalized)

    @classmethod
    def is_supported(cls, extension: str) -> bool:
        ext_normalized = extension.lower().lstrip(".")
        return ext_normalized in cls._extension_map
