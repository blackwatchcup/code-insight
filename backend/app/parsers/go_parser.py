from typing import List

from tree_sitter import Language, Parser
import tree_sitter_go as tsgo

from app.parsers.base import BaseParser, ParseResult, FunctionInfo, ClassInfo


class GoParser(BaseParser):
    """Go 代码解析器，基于 Tree-sitter。"""

    def __init__(self):
        try:
            language = Language(tsgo.language())
            self.parser = Parser(language)
        except Exception as e:
            raise ImportError(f"Failed to initialize Go parser: {e}")

    def get_language(self) -> str:
        return "go"

    def parse(self, content: str, file_path: str) -> ParseResult:
        """解析 Go 代码文件。

        Args:
            content: Go 代码内容
            file_path: 文件路径

        Returns:
            ParseResult: 解析结果
        """
        try:
            tree = self.parser.parse(bytes(content, "utf8"))
            root = tree.root_node

            functions = self._extract_functions(root, content)
            # Go 没有 class，但有 struct 和 interface，我们将它们也视为类
            classes = self._extract_structs_and_interfaces(root, content)
            imports = self._extract_imports(root, content)

            return ParseResult(
                file_path=file_path,
                language="go",
                functions=functions,
                classes=classes,
                imports=imports,
                variables=[],
                raw_ast=tree,
            )
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language="go",
                functions=[],
                classes=[],
                imports=[],
                variables=[],
                raw_ast=None,
                error=str(e),
            )

    def _extract_functions(self, node, content: str) -> List[FunctionInfo]:
        """提取 Go 函数声明。

        Args:
            node: AST 节点
            content: 代码内容

        Returns:
            List[FunctionInfo]: 函数列表
        """
        functions = []
        for child in node.children:
            if child.type in [
                "function_declaration",
                "method_declaration",
            ]:
                functions.append(self._parse_function(child, content))
            # 递归处理 struct 内部的方法
            elif child.type == "type_declaration":
                functions.extend(self._extract_functions(child, content))
            elif child.type == "source_file":
                functions.extend(self._extract_functions(child, content))

        return functions

    def _extract_structs_and_interfaces(
        self, node, content: str
    ) -> List[ClassInfo]:
        """提取 Go struct 和 interface 声明。

        Args:
            node: AST 节点
            content: 代码内容

        Returns:
            List[ClassInfo]: struct 和 interface 列表（作为类处理）
        """
        structs = []
        for child in node.children:
            if child.type == "type_declaration":
                type_spec = child.child_by_field_name("type_spec")
                if type_spec:
                    type_ident = type_spec.child_by_field_name("type_identifier")
                    if type_ident:
                        name = content[
                            type_ident.start_byte : type_ident.end_byte
                        ]

                        # 检查是否是 struct 或 interface
                        body = child.child_by_field_name("body")
                        if body:
                            if body.type == "struct_type":
                                # 结构体
                                structs.append(
                                    self._parse_struct(child, content, name)
                                )
                            elif body.type == "interface_type":
                                # 接口
                                structs.append(
                                    self._parse_interface(child, content, name)
                                )

            elif child.type == "source_file":
                structs.extend(
                    self._extract_structs_and_interfaces(child, content)
                )

        return structs

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
                import_path = child.child_by_field_name("import_path")
                if import_path:
                    # 去除引号
                    path_text = content[
                        import_path.start_byte : import_path.end_byte
                    ]
                    imports.append(path_text.strip('"'))
            elif child.type == "import_spec_list":
                # 处理批量导入
                for spec in child.children:
                    if spec.type == "import_spec":
                        path = spec.child_by_field_name("import_path")
                        if path:
                            path_text = content[path.start_byte : path.end_byte]
                            imports.append(path_text.strip('"'))

        return imports

    def _parse_function(self, node, content: str) -> FunctionInfo:
        """解析函数信息。

        Args:
            node: 函数节点
            content: 代码内容

        Returns:
            FunctionInfo: 函数信息
        """
        name = ""
        parameters = []
        return_type = ""
        docstring = ""
        is_receiver = False

        for child in node.children:
            if child.type == "identifier":
                name = content[child.start_byte : child.end_byte]
            elif child.type == "parameter_list":
                parameters = self._extract_parameters(child, content)
            elif child.type == "type_identifier":
                return_type = content[child.start_byte : child.end_byte]
            elif child.type == "comment" or child.type == "line_comment":
                docstring = content[child.start_byte : child.end_byte]
            elif child.type == "parameter_declaration":
                # 检查是否有 receiver（方法）
                name_node = child.child_by_field_name("name")
                if name_node and name_node.type == "identifier":
                    receiver_name = content[
                        name_node.start_byte : name_node.end_byte
                    ]
                    if receiver_name in ("self", "this", "m", "ctx"):
                        is_receiver = True

        return FunctionInfo(
            name=name,
            return_type=return_type,
            parameters=parameters,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
        )

    def _parse_struct(self, node, content: str, name: str) -> ClassInfo:
        """解析 struct 信息。

        Args:
            node: struct 节点
            content: 代码内容
            name: struct 名称

        Returns:
            ClassInfo: struct 信息（作为类处理）
        """
        methods = []
        properties = []
        docstring = ""

        # 提取字段
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "comment" or child.type == "line_comment":
                    docstring = content[child.start_byte : child.end_byte]
                elif child.type == "field_declaration_list":
                    for field in child.children:
                        if field.type == "field_declaration":
                            field_props = self._extract_fields(
                                field, content
                            )
                            properties.extend(field_props)

        return ClassInfo(
            name=f"struct {name}",
            methods=methods,
            properties=properties,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
        )

    def _parse_interface(self, node, content: str, name: str) -> ClassInfo:
        """解析 interface 信息。

        Args:
            node: interface 节点
            content: 代码内容
            name: interface 名称

        Returns:
            ClassInfo: interface 信息（作为类处理）
        """
        methods = []
        docstring = ""

        # 提取接口方法
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "comment" or child.type == "line_comment":
                    docstring = content[child.start_byte : child.end_byte]
                elif child.type == "method_spec":
                    methods.append(self._parse_method_spec(child, content))

        return ClassInfo(
            name=f"interface {name}",
            methods=methods,
            properties=[],
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=docstring,
        )

    def _parse_method_spec(self, node, content: str) -> FunctionInfo:
        """解析 interface 方法规格。

        Args:
            node: 方法规格节点
            content: 代码内容

        Returns:
            FunctionInfo: 方法信息
        """
        name = ""
        parameters = []
        return_type = ""

        for child in node.children:
            if child.type == "field_identifier":
                name = content[child.start_byte : child.end_byte]
            elif child.type == "parameter_list":
                parameters = self._extract_parameters(child, content)
            elif child.type == "type_identifier":
                return_type = content[child.start_byte : child.end_byte]

        return FunctionInfo(
            name=name,
            return_type=return_type,
            parameters=parameters,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring="",
        )

    def _extract_parameters(self, node, content: str) -> List:
        """提取函数参数。

        Args:
            node: 参数节点
            content: 代码内容

        Returns:
            List: 参数列表
        """
        parameters = []
        for child in node.children:
            if child.type == "parameter_declaration":
                param_name = ""
                param_type = ""

                # 查找参数名
                name_node = child.child_by_field_name("name")
                if name_node:
                    for grandchild in name_node.children:
                        if grandchild.type == "identifier":
                            param_name = content[
                                grandchild.start_byte : grandchild.end_byte
                            ]
                            break

                # 查找参数类型
                type_node = child.child_by_field_name("type")
                if type_node:
                    param_type = content[
                        type_node.start_byte : type_node.end_byte
                    ]

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
        name_node = node.child_by_field_name("name")
        if name_node:
            field_name = ""
            for child in name_node.children:
                if child.type == "identifier":
                    field_name = content[child.start_byte : child.end_byte]
                    break

            if field_name:
                # 获取类型
                field_type = ""
                type_node = node.child_by_field_name("type")
                if type_node:
                    field_type = content[
                        type_node.start_byte : type_node.end_byte
                    ]

                fields.append({"name": field_name, "type": field_type})

        return fields
