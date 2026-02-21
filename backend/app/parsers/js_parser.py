import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser, Node
from typing import List, Optional
from app.parsers.base import (
    BaseParser,
    ParseResult,
    FunctionInfo,
    ClassInfo,
    ImportInfo,
    VariableInfo,
    ParameterInfo,
    CallInfo,
)


class JavaScriptParser(BaseParser):
    def __init__(self):
        self.parser = Parser(Language(tsjs.language()))

    def get_language(self) -> str:
        return "javascript"

    def get_supported_extensions(self) -> List[str]:
        return [".js", ".jsx", ".mjs", ".cjs"]

    def parse(self, content: str, file_path: str) -> ParseResult:
        try:
            tree = self.parser.parse(bytes(content, "utf8"))
            root = tree.root_node

            functions = self._extract_functions(root, content)
            classes = self._extract_classes(root, content)
            imports = self._extract_imports(root, content)
            variables = self._extract_variables(root, content)
            calls = self._extract_calls(root, content)

            return ParseResult(
                file_path=file_path,
                language="javascript",
                functions=functions,
                classes=classes,
                imports=imports,
                variables=variables,
                calls=calls,
                raw_ast=tree,
            )
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language="javascript",
                error=str(e),
            )

    def _extract_functions(self, node: Node, content: str) -> List[FunctionInfo]:
        functions = []
        self._traverse_functions(node, content, functions)
        return functions

    def _traverse_functions(self, node: Node, content: str, functions: List[FunctionInfo]):
        if node.type == "function_declaration":
            func = self._parse_function(node, content)
            functions.append(func)
        elif node.type == "variable_declaration":
            for child in node.children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    if name_node and value_node and value_node.type in ("arrow_function", "function_expression"):
                        name = self._get_node_text(name_node, content) or ""
                        func = self._parse_function(value_node, content, name)
                        functions.append(func)
        elif node.type == "lexical_declaration":
            for child in node.children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    if name_node and value_node and value_node.type in ("arrow_function", "function_expression"):
                        name = self._get_node_text(name_node, content) or ""
                        func = self._parse_function(value_node, content, name)
                        functions.append(func)
        elif node.type == "method_definition":
            func = self._parse_method(node, content)
            functions.append(func)

        for child in node.children:
            self._traverse_functions(child, content, functions)

    def _parse_function(self, node: Node, content: str, name: str = "") -> FunctionInfo:
        if not name:
            name_node = node.child_by_field_name("name")
            name = self._get_node_text(name_node, content) or ""

        is_async = False
        for child in node.children:
            if child.type == "async":
                is_async = True
                break

        parameters = self._extract_parameters(node, content)
        body = self._get_node_text(node.child_by_field_name("body"), content) or ""

        return FunctionInfo(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            parameters=parameters,
            is_async=is_async,
            body=body,
        )

    def _parse_method(self, node: Node, content: str) -> FunctionInfo:
        name_node = node.child_by_field_name("name")
        name = self._get_node_text(name_node, content) or ""

        is_async = False
        is_static = False
        for child in node.children:
            if child.type == "async":
                is_async = True
            if child.type == "static":
                is_static = True

        parameters = self._extract_parameters(node, content)
        body = self._get_node_text(node.child_by_field_name("body"), content) or ""

        return FunctionInfo(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            parameters=parameters,
            is_async=is_async,
            is_method=True,
            body=body,
        )

    def _extract_parameters(self, node: Node, content: str) -> List[ParameterInfo]:
        parameters = []
        params_node = node.child_by_field_name("parameters")
        if not params_node:
            return parameters

        for child in params_node.children:
            if child.type == "identifier":
                parameters.append(
                    ParameterInfo(name=self._get_node_text(child, content) or "")
                )
            elif child.type == "assignment_pattern":
                name = ""
                default = ""
                for subchild in child.children:
                    if subchild.type == "identifier":
                        name = self._get_node_text(subchild, content) or ""
                    else:
                        default = self._get_node_text(subchild, content) or ""
                parameters.append(ParameterInfo(name=name, default_value=default))
            elif child.type == "rest_parameter":
                name = self._get_node_text(child.child_by_field_name("name"), content) or ""
                parameters.append(ParameterInfo(name=f"...{name}"))
            elif child.type == "object_pattern":
                parameters.append(
                    ParameterInfo(name=self._get_node_text(child, content) or "")
                )
            elif child.type == "array_pattern":
                parameters.append(
                    ParameterInfo(name=self._get_node_text(child, content) or "")
                )

        return parameters

    def _extract_classes(self, node: Node, content: str) -> List[ClassInfo]:
        classes = []
        self._traverse_classes(node, content, classes)
        return classes

    def _traverse_classes(self, node: Node, content: str, classes: List[ClassInfo]):
        if node.type == "class_declaration":
            cls = self._parse_class(node, content)
            classes.append(cls)
        elif node.type == "export_statement":
            for child in node.children:
                if child.type == "class_declaration":
                    cls = self._parse_class(child, content)
                    classes.append(cls)

        for child in node.children:
            self._traverse_classes(child, content, classes)

    def _parse_class(self, node: Node, content: str) -> ClassInfo:
        name = self._get_node_text(node.child_by_field_name("name"), content) or ""
        base_classes = []
        
        extends = node.child_by_field_name("parent")
        if extends:
            base_classes.append(self._get_node_text(extends, content) or "")

        methods = []
        attributes = []

        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "method_definition":
                    method = self._parse_method(child, content)
                    methods.append(method)
                elif child.type == "field_definition":
                    field_name = self._get_node_text(child.child_by_field_name("name"), content) or ""
                    field_value = self._get_node_text(child.child_by_field_name("value"), content) or ""
                    attributes.append({"name": field_name, "value": field_value})
                elif child.type == "public_field_definition":
                    field_name = self._get_node_text(child.child_by_field_name("name"), content) or ""
                    field_value = self._get_node_text(child.child_by_field_name("value"), content) or ""
                    attributes.append({"name": field_name, "value": field_value})

        return ClassInfo(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            methods=methods,
            attributes=attributes,
            base_classes=base_classes,
        )

    def _extract_imports(self, node: Node, content: str) -> List[ImportInfo]:
        imports = []
        self._traverse_imports(node, content, imports)
        return imports

    def _traverse_imports(self, node: Node, content: str, imports: List[ImportInfo]):
        if node.type == "import_statement":
            module = ""
            names = []
            
            source = node.child_by_field_name("source")
            if source:
                module = self._get_node_text(source, content) or ""
                module = module.strip("'\"")

            for child in node.children:
                if child.type == "import_clause":
                    for subchild in child.children:
                        if subchild.type == "identifier":
                            names.append(self._get_node_text(subchild, content) or "")
                        elif subchild.type == "named_imports":
                            for spec in subchild.children:
                                if spec.type == "import_specifier":
                                    name = self._get_node_text(spec.child_by_field_name("name"), content) or ""
                                    alias = self._get_node_text(spec.child_by_field_name("alias"), content) or ""
                                    if alias:
                                        names.append(f"{name} as {alias}")
                                    else:
                                        names.append(name)
                        elif subchild.type == "namespace_import":
                            alias = self._get_node_text(subchild.child_by_field_name("alias"), content) or ""
                            if alias:
                                names.append(f"* as {alias}")

            if module:
                imports.append(ImportInfo(module=module, names=names, is_from_import=True))

        elif node.type == "export_statement":
            for child in node.children:
                if child.type == "export_clause":
                    for spec in child.children:
                        if spec.type == "export_specifier":
                            pass

        for child in node.children:
            self._traverse_imports(child, content, imports)

    def _extract_variables(self, node: Node, content: str) -> List[VariableInfo]:
        variables = []
        self._traverse_variables(node, content, variables)
        return variables

    def _traverse_variables(self, node: Node, content: str, variables: List[VariableInfo]):
        if node.type in ("variable_declaration", "lexical_declaration"):
            for child in node.children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    if name_node and value_node:
                        name = self._get_node_text(name_node, content) or ""
                        value = self._get_node_text(value_node, content) or ""
                        if value_node.type not in ("arrow_function", "function_expression"):
                            variables.append(
                                VariableInfo(
                                    name=name,
                                    value=value,
                                    line=node.start_point[0] + 1,
                                )
                            )

        for child in node.children:
            self._traverse_variables(child, content, variables)

    def _extract_calls(self, node: Node, content: str) -> List[CallInfo]:
        calls = []
        self._traverse_calls(node, content, calls, "")
        return calls

    def _traverse_calls(self, node: Node, content: str, calls: List[CallInfo], current_function: str):
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                current_function = self._get_node_text(name_node, content) or ""

        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                callee = self._get_node_text(func_node, content) or ""
                args = []
                args_node = node.child_by_field_name("arguments")
                if args_node:
                    for arg in args_node.children:
                        if arg.type not in ("(", ")", ",", "[", "]"):
                            args.append(self._get_node_text(arg, content) or "")
                calls.append(
                    CallInfo(
                        caller=current_function,
                        callee=callee,
                        line=node.start_point[0] + 1,
                        arguments=args,
                    )
                )

        for child in node.children:
            self._traverse_calls(child, content, calls, current_function)

    def _get_node_text(self, node: Optional[Node], content: str) -> Optional[str]:
        if node is None:
            return None
        return content[node.start_byte:node.end_byte]
