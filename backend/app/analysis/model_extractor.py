import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ModelField:
    name: str
    type: str
    nullable: bool = False
    primary_key: bool = False
    description: str = ""
    default: Optional[str] = None
    foreign_key: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "description": self.description,
            "default": self.default,
            "foreign_key": self.foreign_key
        }


@dataclass
class DataModel:
    name: str
    file_path: str
    line: int
    fields: List[ModelField] = field(default_factory=list)
    table_name: str = ""
    model_type: str = "sqlalchemy"
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line": self.line,
            "fields": [f.to_dict() for f in self.fields],
            "table_name": self.table_name,
            "model_type": self.model_type,
            "description": self.description
        }


class ModelExtractor:
    SQLALCHEMY_PATTERNS = {
        "class": r'class\s+(\w+)\(.*(?:Base|Model).*\):',
        "table": r'__tablename__\s*=\s*["\']([^"\']+)["\']',
        "column": r'(\w+)\s*=\s*Column\(([^)]+)\)',
        "relationship": r'(\w+)\s*=\s*relationship\(["\']([^"\']+)["\']',
    }
    
    PRISMA_PATTERNS = {
        "model": r'model\s+(\w+)\s*\{([^}]+)\}',
        "field": r'^\s*(\w+)\s+(\w+)(?:\s+(@@|\@))?',
    }
    
    TYPEORM_PATTERNS = {
        "entity": r'@Entity\(["\']?([^"\'\)]*)["\']?\)\s*(?:export\s+)?class\s+(\w+)',
        "column": r'@Column\(([^)]*)\)\s*(?:\w+\s*:\s*)?(\w+)(?:\s*:\s*)?(\w+)?',
        "primary": r'@PrimaryGeneratedColumn\(([^)]*)\)\s*(?:\w+\s*:\s*)?(\w+)',
    }
    
    DJANGO_PATTERNS = {
        "model": r'class\s+(\w+)\(.*(?:models\.Model|Model)\):',
        "field": r'(\w+)\s*=\s*models\.(\w+)(?:Field)?\(([^)]*)\)',
    }
    
    MONGOOSE_PATTERNS = {
        "schema": r'(?:const|let|var)\s+(\w+Schema)\s*=\s*new\s+Schema\(([^)]+)\)',
        "model": r'(?:const|let|var)\s+(\w+)\s*=\s*(?:mongoose\.)?model\(["\']([^"\']+)["\']',
        "field": r'(\w+):\s*\{[^}]*type:\s*(\w+)',
    }
    
    def extract_sqlalchemy(self, content: str, file_path: str) -> List[DataModel]:
        models = []
        lines = content.split('\n')
        
        class_matches = list(re.finditer(self.SQLALCHEMY_PATTERNS["class"], content))
        
        for match in class_matches:
            class_name = match.group(1)
            class_start = match.start()
            class_end = self._find_class_end(content, class_start)
            class_body = content[class_start:class_end]
            
            table_name = class_name.lower()
            table_match = re.search(self.SQLALCHEMY_PATTERNS["table"], class_body)
            if table_match:
                table_name = table_match.group(1)
            
            fields = []
            for col_match in re.finditer(self.SQLALCHEMY_PATTERNS["column"], class_body):
                field_name = col_match.group(1)
                column_def = col_match.group(2)
                
                field = self._parse_sqlalchemy_column(field_name, column_def)
                fields.append(field)
            
            line_num = content[:class_start].count('\n') + 1
            
            models.append(DataModel(
                name=class_name,
                file_path=file_path,
                line=line_num,
                fields=fields,
                table_name=table_name,
                model_type="sqlalchemy"
            ))
        
        return models
    
    def _parse_sqlalchemy_column(self, name: str, column_def: str) -> ModelField:
        field_type = "unknown"
        nullable = True
        primary_key = False
        default = None
        foreign_key = None
        
        type_match = re.search(r'(\w+)(?:\(|$)', column_def)
        if type_match:
            field_type = type_match.group(1)
        
        if 'primary_key=True' in column_def:
            primary_key = True
            nullable = False
        
        if 'nullable=False' in column_def:
            nullable = False
        
        if 'nullable=True' in column_def:
            nullable = True
        
        default_match = re.search(r'default\s*=\s*([^,\)]+)', column_def)
        if default_match:
            default = default_match.group(1).strip()
        
        fk_match = re.search(r'ForeignKey\(["\']([^"\']+)["\']', column_def)
        if fk_match:
            foreign_key = fk_match.group(1)
        
        return ModelField(
            name=name,
            type=field_type,
            nullable=nullable,
            primary_key=primary_key,
            default=default,
            foreign_key=foreign_key
        )
    
    def extract_prisma(self, content: str, file_path: str) -> List[DataModel]:
        models = []
        
        for match in re.finditer(self.PRISMA_PATTERNS["model"], content):
            model_name = match.group(1)
            model_body = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            
            fields = []
            for line in model_body.split('\n'):
                line = line.strip()
                if not line or line.startswith('//') or line.startswith('@@'):
                    continue
                
                field_match = re.match(r'^(\w+)\s+(\w+)', line)
                if field_match:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    
                    nullable = '?' in line
                    primary_key = '@id' in line
                    
                    fields.append(ModelField(
                        name=field_name,
                        type=field_type,
                        nullable=nullable,
                        primary_key=primary_key
                    ))
            
            models.append(DataModel(
                name=model_name,
                file_path=file_path,
                line=line_num,
                fields=fields,
                table_name=model_name.lower(),
                model_type="prisma"
            ))
        
        return models
    
    def extract_typeorm(self, content: str, file_path: str) -> List[DataModel]:
        models = []
        
        for match in re.finditer(self.TYPEORM_PATTERNS["entity"], content):
            table_name = match.group(1) or ""
            class_name = match.group(2)
            
            class_start = match.start()
            class_end = self._find_class_end(content, class_start)
            class_body = content[class_start:class_end]
            
            line_num = content[:class_start].count('\n') + 1
            
            fields = []
            
            for primary_match in re.finditer(self.TYPEORM_PATTERNS["primary"], class_body):
                field_name = primary_match.group(2)
                fields.append(ModelField(
                    name=field_name,
                    type="number",
                    nullable=False,
                    primary_key=True
                ))
            
            for col_match in re.finditer(self.TYPEORM_PATTERNS["column"], class_body):
                col_config = col_match.group(1)
                field_name = col_match.group(2)
                field_type = col_match.group(3) or "string"
                
                nullable = 'nullable: true' in col_config
                
                fields.append(ModelField(
                    name=field_name,
                    type=field_type,
                    nullable=nullable,
                    primary_key=False
                ))
            
            models.append(DataModel(
                name=class_name,
                file_path=file_path,
                line=line_num,
                fields=fields,
                table_name=table_name or class_name.lower(),
                model_type="typeorm"
            ))
        
        return models
    
    def extract_django(self, content: str, file_path: str) -> List[DataModel]:
        models = []
        
        for match in re.finditer(self.DJANGO_PATTERNS["model"], content):
            class_name = match.group(1)
            class_start = match.start()
            class_end = self._find_class_end(content, class_start)
            class_body = content[class_start:class_end]
            
            line_num = content[:class_start].count('\n') + 1
            
            fields = []
            for field_match in re.finditer(self.DJANGO_PATTERNS["field"], class_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                field_config = field_match.group(3)
                
                nullable = 'null=True' in field_config or 'blank=True' in field_config
                primary_key = 'primary_key=True' in field_config
                
                fields.append(ModelField(
                    name=field_name,
                    type=field_type,
                    nullable=nullable,
                    primary_key=primary_key
                ))
            
            models.append(DataModel(
                name=class_name,
                file_path=file_path,
                line=line_num,
                fields=fields,
                table_name=class_name.lower(),
                model_type="django"
            ))
        
        return models
    
    def extract_mongoose(self, content: str, file_path: str) -> List[DataModel]:
        models = []
        
        for match in re.finditer(self.MONGOOSE_PATTERNS["model"], content):
            var_name = match.group(1)
            collection_name = match.group(2)
            
            line_num = content[:match.start()].count('\n') + 1
            
            schema_match = re.search(
                rf'(?:const|let|var)\s+{var_name}Schema\s*=\s*new\s+Schema\(([^)]+)\)',
                content
            )
            
            fields = []
            if schema_match:
                schema_body = schema_match.group(1)
                
                for field_match in re.finditer(self.MONGOOSE_PATTERNS["field"], schema_body):
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    
                    fields.append(ModelField(
                        name=field_name,
                        type=field_type,
                        nullable=True,
                        primary_key=field_name == '_id'
                    ))
            
            models.append(DataModel(
                name=var_name,
                file_path=file_path,
                line=line_num,
                fields=fields,
                table_name=collection_name,
                model_type="mongoose"
            ))
        
        return models
    
    def detect_orm(self, content: str) -> str:
        if 'sqlalchemy' in content.lower() or 'Column(' in content:
            return 'sqlalchemy'
        if 'prisma' in content.lower() or re.search(r'model\s+\w+\s*\{', content):
            return 'prisma'
        if '@Entity' in content or 'typeorm' in content.lower():
            return 'typeorm'
        if 'models.Model' in content or 'from django.db' in content:
            return 'django'
        if 'mongoose' in content.lower() or 'new Schema(' in content:
            return 'mongoose'
        return 'unknown'
    
    def extract(self, content: str, file_path: str) -> List[DataModel]:
        orm_type = self.detect_orm(content)
        
        if orm_type == 'sqlalchemy':
            return self.extract_sqlalchemy(content, file_path)
        elif orm_type == 'prisma':
            return self.extract_prisma(content, file_path)
        elif orm_type == 'typeorm':
            return self.extract_typeorm(content, file_path)
        elif orm_type == 'django':
            return self.extract_django(content, file_path)
        elif orm_type == 'mongoose':
            return self.extract_mongoose(content, file_path)
        
        return []
    
    def _find_class_end(self, content: str, start: int) -> int:
        lines_after = content[start:].split('\n')
        indent_level = None
        end_offset = 0
        
        for i, line in enumerate(lines_after):
            if i == 0:
                continue
            
            if line.strip() and not line.strip().startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                
                if indent_level is None:
                    indent_level = current_indent
                elif current_indent < indent_level and line.strip():
                    break
            
            end_offset += len(line) + 1
        
        return start + end_offset
    
    def get_model_summary(self, models: List[DataModel]) -> Dict:
        summary = {
            "total_models": len(models),
            "total_fields": sum(len(m.fields) for m in models),
            "by_type": {},
            "models": []
        }
        
        for model in models:
            if model.model_type not in summary["by_type"]:
                summary["by_type"][model.model_type] = 0
            summary["by_type"][model.model_type] += 1
            
            summary["models"].append({
                "name": model.name,
                "table": model.table_name,
                "fields": len(model.fields)
            })
        
        return summary
