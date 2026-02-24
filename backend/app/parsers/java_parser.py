from typing import List

from tree_sitter import Language, Parser
import tree_sitter_java as tsjava

from app.parsers.base import BaseParser, ParseResult, FunctionInfo, ClassInfo


class JavaParser(BaseParser):
    """Java 代码解析器，基于 Tree-sitter。"""

    def __init__(self):
        try:
            language = Language(tsjava.language())
            self.parser = Parser(language)
        except Exception as e:
            raise ImportError(f"Failed to initialize Java parser: {e}")

    def get_language(self) -> str:
        return "java"

    def parse(self, content: str, file_path: str) -> ParseResult:
        """解析 Java 代码文件。

        Args:
            content: Java 代码内容
            file_path: 文件路径

        Returns:
            ParseResult: 解析结果
        """
        try:
            tree = self.parser.parse(bytes(content, "utf8"))
            root = tree.root_node

            functions = self._extract_methods(root, content)
            classes = self._extract_classes(root, content)
            imports = self._extract_imports(root, content)

            return ParseResult(
                file_path=file_path,
                language="java",
                functions=functions,
                classes=classes,
                imports=imports,
                variables=[],
                raw_ast=tree,
            )
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language="java",
                functions=[],
                classes=[],
                imports=[],
                variables=[],
                raw_ast=None,
                error=str(e),
            )

    def _extract_methods(self, node, content: str) -> List[FunctionInfo]:
        """提取 Java 方法声明。

        Args:
            node: AST 节点
            content: 代码内容

        Returns:
            List[FunctionInfo]: 方法列表
        """
        methods = []
        for child in node.children:
            if child.type == "method_declaration":
                methods.append(self._parse_method(child, content))
            # 递归处理类内部的方法
            elif child.type == "class_declaration":
                methods.extend(self._extract_methods(child, content))
            elif child.type == "interface_declaration":
                methods.extend(self._extract_methods(child, content))
        return methods

    def _extract_classes(self, node, content: str) -> List[ClassInfo]:
        """提取 Java 类声明。

        Args:
            node: AST 节点
            content: 代码内容

        Returns:
            List[ClassInfo]: 类列表
        """
        classes = []
        for child in node.children:
            if child.type == "class_declaration":
                classes.append(self._parse_class(child, content))
            elif child.type == "interface_declaration":
                # 将接口也视为类
                classes.append(self._parse_interface(child, content))
        return classes

    def _extract_imports(self, node, content: str) -> List[str]:
        """提取 import 语句。

        Args:
            node: AST 节点
            content: 代码内容

        Returns:
            List[str]: import 语句列表
        """
        imports = []
        for child in node.children:
            if child.type == "import_declaration":
                imports.append(content[child.start_byte: child.end_byte].strip())
        return imports

    def _parse_method(self, node, content: str) -> FunctionInfo:
        """解析方法信息。

        Args:
            node: 方法节点
            content: 代码内容

        Returns:
            FunctionInfo: 方法信息
        """
        # 查找方法名
        name = ""
        parameters = []
        return_type = ""
        docstring = ""

        for child in node.children:
            if child.type == "identifier":
                # 方法名
                name = content[child.start_byte: child.end_byte]
            elif child.type == "formal_parameters":
                # 参数列表
                parameters = self._extract_parameters(child, content)
            elif child.type == "type_identifier":
                # 返回类型
                return_type = content[child.start_byte: child.end_byte]
            elif child.type == "block_comment" or child.type == "line_comment":
                # Javadoc 注释
                docstring = content[child.start_byte: child.end_byte]

        return FunctionInfo(
            name=name,
            return_type=return_type,
            parameters=parameters,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
        )

    def _parse_class(self, node, content: str) -> ClassInfo:
        """解析类信息。

        Args:
            node: 类节点
            content: 代码内容

        Returns:
            ClassInfo: 类信息
        """
        name = ""
        methods = []
        properties = []
        docstring = ""

        for child in node.children:
            if child.type == "identifier":
                # 类名
                name = content[child.start_byte: child.end_byte]
            elif child.type == "block_comment" or child.type == "line_comment":
                # Javadoc 注释
                docstring = content[child.start_byte: child.end_byte]

        # 提取类中的方法
        for child in node.children:
            if child.type == "method_declaration":
                methods.append(self._parse_method(child, content))

        # 提取字段作为属性
        for child in node.children:
            if child.type == "field_declaration":
                field_props = self._extract_fields(child, content)
                properties.extend(field_props)

        return ClassInfo(
            name=name,
            methods=methods,
            properties=properties,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
        )

    def _parse_interface(self, node, content: str) -> ClassInfo:
        """解析接口信息。

        Args:
            node: 接口节点
            content: 代码内容

        Returns:
            ClassInfo: 接口信息（作为类处理）
        """
        name = ""
        methods = []
        docstring = ""

        for child in node.children:
            if child.type == "identifier":
                name = content[child.start_byte: child.end_byte]
            elif child.type == "block_comment" or child.type == "line_comment":
                docstring = content[child.start_byte: child.end_byte]

        # 提取接口中的方法
        for child in node.children:
            if child.type == "method_declaration":
                methods.append(self._parse_method(child, content))

        return ClassInfo(
            name=name,
            methods=methods,
            properties=[],
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
        )

    def _extract_parameters(self, node, content: str) -> List:
        """提取方法参数。

        Args:
            node: 参数节点
            content: 代码内容

        Returns:
            List: 参数列表
        """
        parameters = []
        for child in node.children:
            if child.type == "formal_parameter":
                param_name = ""
                param_type = ""
                for grandchild in child.children:
                    if grandchild.type == "identifier":
                        param_name = content[grandchild.start_byte: grandchild.end_byte]
                    elif grandchild.type == "type_identifier":
                        param_type = content[grandchild.start_byte: grandchild.end_byte]

                if param_name:
                    parameters.append({"name": param_name, "type": param_type})

        return parameters

    def _extract_fields(self, node, content: str) -> List:
        """提取字段声明。

        Args:
            node: 字段节点
            content: 代码内容

        Returns:
            List: 字段列表
        """
        fields = []
        for child in node.children:
            if child.type == "variable_declarator":
                field_name = ""
                for grandchild in child.children:
                    if grandchild.type == "identifier":
                        field_name = content[grandchild.start_byte: grandchild.end_byte]
                        break

                if field_name:
                    # 获取类型
                    field_type = ""
                    type_node = node.child_by_field_name("type")
                    if type_node:
                        field_type = content[type_node.start_byte: type_node.end_byte]

                    fields.append({"name": field_name, "type": field_type})

        return fields
