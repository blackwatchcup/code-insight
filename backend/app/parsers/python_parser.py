import tree_sitter_python as tspython
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


class PythonParser(BaseParser):
    def __init__(self):
        self.parser = Parser()
        self.parser.set_language(Language(tspython.language(), "python"))

    def get_language(self) -> str:
        return "python"

    def get_supported_extensions(self) -> List[str]:
        return [".py"]

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
                language="python",
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
                language="python",
                error=str(e),
            )

    def _extract_functions(self, node: Node, content: str) -> List[FunctionInfo]:
        functions = []
        for child in node.children:
            if child.type == "function_definition":
                func = self._parse_function(child, content)
                functions.append(func)
            elif child.type == "decorated_definition":
                inner = child.child_by_field_name("definition")
                if inner and inner.type == "function_definition":
                    func = self._parse_function(inner, content)
                    decorators = self._extract_decorators(child, content)
                    functions.append(
                        FunctionInfo(
                            name=func.name,
                            start_line=func.start_line,
                            end_line=func.end_line,
                            parameters=func.parameters,
                            return_type=func.return_type,
                            docstring=func.docstring,
                            body=func.body,
                            decorators=decorators,
                            is_async=func.is_async,
                            is_method=func.is_method,
                        )
                    )
        return functions

    def _parse_function(self, node: Node, content: str) -> FunctionInfo:
        name = self._get_node_text(node.child_by_field_name("name"), content) or ""
        
        is_async = False
        for child in node.children:
            if child.type == "async":
                is_async = True
                break

        parameters = self._extract_parameters(node, content)
        return_type = self._get_node_text(node.child_by_field_name("return_type"), content) or ""
        docstring = self._extract_docstring(node, content)
        body = self._get_node_text(node.child_by_field_name("body"), content) or ""

        return FunctionInfo(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            body=body,
            is_async=is_async,
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
            elif child.type == "typed_parameter":
                name = self._get_node_text(child.child_by_field_name("name"), content) or ""
                type_ann = self._get_node_text(child.child_by_field_name("type"), content) or ""
                parameters.append(ParameterInfo(name=name, type_annotation=type_ann))
            elif child.type == "default_parameter":
                name = self._get_node_text(child.child_by_field_name("name"), content) or ""
                default = self._get_node_text(child.child_by_field_name("value"), content) or ""
                type_ann = self._get_node_text(child.child_by_field_name("type"), content) or ""
                parameters.append(
                    ParameterInfo(name=name, type_annotation=type_ann, default_value=default)
                )
            elif child.type == "typed_default_parameter":
                name = self._get_node_text(child.child_by_field_name("name"), content) or ""
                default = self._get_node_text(child.child_by_field_name("value"), content) or ""
                type_ann = self._get_node_text(child.child_by_field_name("type"), content) or ""
                parameters.append(
                    ParameterInfo(name=name, type_annotation=type_ann, default_value=default)
                )
            elif child.type == "list_splat_pattern":
                name = self._get_node_text(child, content) or ""
                parameters.append(ParameterInfo(name=name))
            elif child.type == "dictionary_splat_pattern":
                name = self._get_node_text(child, content) or ""
                parameters.append(ParameterInfo(name=name))

        return parameters

    def _extract_classes(self, node: Node, content: str) -> List[ClassInfo]:
        classes = []
        for child in node.children:
            if child.type == "class_definition":
                cls = self._parse_class(child, content)
                classes.append(cls)
            elif child.type == "decorated_definition":
                inner = child.child_by_field_name("definition")
                if inner and inner.type == "class_definition":
                    cls = self._parse_class(inner, content)
                    decorators = self._extract_decorators(child, content)
                    classes.append(
                        ClassInfo(
                            name=cls.name,
                            start_line=cls.start_line,
                            end_line=cls.end_line,
                            methods=cls.methods,
                            attributes=cls.attributes,
                            docstring=cls.docstring,
                            base_classes=cls.base_classes,
                            decorators=decorators,
                        )
                    )
        return classes

    def _parse_class(self, node: Node, content: str) -> ClassInfo:
        name = self._get_node_text(node.child_by_field_name("name"), content) or ""
        docstring = self._extract_docstring(node, content)
        base_classes = self._extract_base_classes(node, content)

        methods = []
        attributes = []

        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "function_definition":
                    method = self._parse_function(child, content)
                    methods.append(
                        FunctionInfo(
                            name=method.name,
                            start_line=method.start_line,
                            end_line=method.end_line,
                            parameters=method.parameters,
                            return_type=method.return_type,
                            docstring=method.docstring,
                            body=method.body,
                            decorators=method.decorators,
                            is_async=method.is_async,
                            is_method=True,
                        )
                    )
                elif child.type == "expression_statement":
                    expr = child.child(0)
                    if expr and expr.type == "assignment":
                        left = expr.child_by_field_name("left")
                        if left:
                            attr_name = self._get_node_text(left, content) or ""
                            attr_value = self._get_node_text(expr.child_by_field_name("right"), content) or ""
                            attributes.append({"name": attr_name, "value": attr_value})

        return ClassInfo(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            methods=methods,
            attributes=attributes,
            docstring=docstring,
            base_classes=base_classes,
        )

    def _extract_base_classes(self, node: Node, content: str) -> List[str]:
        base_classes = []
        arg_list = node.child_by_field_name("superclasses")
        if arg_list:
            for child in arg_list.children:
                if child.type in ("identifier", "attribute", "subscript"):
                    base_classes.append(self._get_node_text(child, content) or "")
        return base_classes

    def _extract_imports(self, node: Node, content: str) -> List[ImportInfo]:
        imports = []
        for child in node.children:
            if child.type == "import_statement":
                names = []
                for name_node in child.children:
                    if name_node.type == "dotted_name":
                        names.append(self._get_node_text(name_node, content) or "")
                    elif name_node.type == "aliased_import":
                        name = self._get_node_text(name_node.child_by_field_name("name"), content) or ""
                        alias = self._get_node_text(name_node.child_by_field_name("alias"), content) or ""
                        names.append(f"{name} as {alias}")
                if names:
                    imports.append(
                        ImportInfo(module=names[0], names=names, is_from_import=False)
                    )
            elif child.type == "import_from_statement":
                module = ""
                names = []
                for subchild in child.children:
                    if subchild.type == "dotted_name":
                        module = self._get_node_text(subchild, content) or ""
                    elif subchild.type == "wildcard_import":
                        names.append("*")
                    elif subchild.type == "import_list":
                        for name_node in subchild.children:
                            if name_node.type == "identifier":
                                names.append(self._get_node_text(name_node, content) or "")
                            elif name_node.type == "aliased_import":
                                name = self._get_node_text(name_node.child_by_field_name("name"), content) or ""
                                alias = self._get_node_text(name_node.child_by_field_name("alias"), content) or ""
                                names.append(f"{name} as {alias}")
                imports.append(
                    ImportInfo(module=module, names=names, is_from_import=True)
                )
        return imports

    def _extract_variables(self, node: Node, content: str) -> List[VariableInfo]:
        variables = []
        for child in node.children:
            if child.type == "expression_statement":
                expr = child.child(0)
                if expr and expr.type == "assignment":
                    left = expr.child_by_field_name("left")
                    if left and left.type == "identifier":
                        name = self._get_node_text(left, content) or ""
                        value = self._get_node_text(expr.child_by_field_name("right"), content) or ""
                        variables.append(
                            VariableInfo(
                                name=name,
                                value=value,
                                line=child.start_point[0] + 1,
                                scope="module",
                            )
                        )
            elif child.type == "annotated_assignment":
                left = child.child_by_field_name("left")
                if left and left.type == "identifier":
                    name = self._get_node_text(left, content) or ""
                    type_ann = self._get_node_text(child.child_by_field_name("type"), content) or ""
                    value = self._get_node_text(child.child_by_field_name("value"), content) or ""
                    variables.append(
                        VariableInfo(
                            name=name,
                            type_annotation=type_ann,
                            value=value,
                            line=child.start_point[0] + 1,
                            scope="module",
                        )
                    )
        return variables

    def _extract_calls(self, node: Node, content: str) -> List[CallInfo]:
        calls = []
        self._traverse_calls(node, content, calls, "")
        return calls

    def _traverse_calls(self, node: Node, content: str, calls: List[CallInfo], current_function: str):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                current_function = self._get_node_text(name_node, content) or ""

        if node.type == "call":
            func_node = node.child_by_field_name("function")
            if func_node:
                callee = self._get_node_text(func_node, content) or ""
                args = []
                args_node = node.child_by_field_name("arguments")
                if args_node:
                    for arg in args_node.children:
                        if arg.type not in ("(", ")", ","):
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

    def _extract_docstring(self, node: Node, content: str) -> str:
        body = node.child_by_field_name("body")
        if body and body.child_count > 0:
            first_stmt = body.child(0)
            if first_stmt and first_stmt.type == "expression_statement":
                expr = first_stmt.child(0)
                if expr and expr.type == "string":
                    docstring = self._get_node_text(expr, content) or ""
                    if docstring.startswith(('"""', "'''")):
                        docstring = docstring[3:-3]
                    elif docstring.startswith(('"', "'")):
                        docstring = docstring[1:-1]
                    return docstring
        return ""

    def _extract_decorators(self, node: Node, content: str) -> List[str]:
        decorators = []
        for child in node.children:
            if child.type == "decorator":
                decorator_text = self._get_node_text(child, content) or ""
                if decorator_text.startswith("@"):
                    decorator_text = decorator_text[1:]
                decorators.append(decorator_text)
        return decorators

    def _get_node_text(self, node: Optional[Node], content: str) -> Optional[str]:
        if node is None:
            return None
        return content[node.start_byte:node.end_byte]
