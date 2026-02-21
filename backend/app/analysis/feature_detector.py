import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class FeatureType(str, Enum):
    SCHEDULED_TASK = "scheduled_task"
    SSO = "sso"
    MIDDLEWARE = "middleware"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    DATABASE = "database"
    WEBSOCKET = "websocket"
    AUTH = "auth"
    LOGGING = "logging"
    MONITORING = "monitoring"
    EMAIL = "email"
    STORAGE = "storage"


@dataclass
class SystemFeature:
    type: FeatureType
    name: str
    description: str
    file_path: str
    line: int
    config: Dict = field(default_factory=dict)
    framework: str = ""
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "file_path": self.file_path,
            "line": self.line,
            "config": self.config,
            "framework": self.framework
        }


class SystemFeatureDetector:
    FEATURE_PATTERNS = {
        FeatureType.SCHEDULED_TASK: {
            "patterns": [
                r'@scheduler\.task',
                r'@celery\.task',
                r'@celery\.app\.task',
                r'APScheduler',
                r'schedule\.every\(',
                r'cron\.schedule',
                r'node-cron',
                r'node-schedule',
                r'@Scheduled',
                r'@EnableScheduling',
                r'setInterval',
                r'setTimeout',
            ],
            "extract": [
                r'@scheduler\.task.*?def\s+(\w+)',
                r'@celery\.task.*?def\s+(\w+)',
                r'def\s+(\w+)\s*\([^)]*\)\s*.*@scheduler',
                r'@Scheduled.*?public\s+\w+\s+(\w+)',
            ],
            "description": "定时任务"
        },
        FeatureType.SSO: {
            "patterns": [
                r'flask_sso',
                r'django-allauth',
                r'authlib',
                r'python-saml',
                r'passport-saml',
                r'passport-oauth2',
                r'OAuth2',
                r'OIDC',
                r'OpenID',
                r'SAML',
                r'CasAuthenticationProvider',
                r'@EnableOAuth2Sso',
            ],
            "extract": [],
            "description": "单点登录(SSO)"
        },
        FeatureType.MIDDLEWARE: {
            "patterns": [
                r'@middleware',
                r'class\s+\w+Middleware',
                r'app\.use\(',
                r'add_middleware',
                r'CORSMiddleware',
                r'AuthenticationMiddleware',
                r'SessionMiddleware',
                r'@Component.*Middleware',
            ],
            "extract": [
                r'class\s+(\w+Middleware)',
                r'@middleware\s*\n\s*def\s+(\w+)',
            ],
            "description": "中间件"
        },
        FeatureType.CACHE: {
            "patterns": [
                r'redis',
                r'Redis\(',
                r'memcached',
                r'MemcachedClient',
                r'cachetools',
                r'@cache',
                r'@Cacheable',
                r'@CacheEvict',
                r'CacheManager',
                r'node-cache',
            ],
            "extract": [
                r'redis\.Redis\([^)]*host\s*=\s*["\']([^"\']+)["\']',
                r'Redis\([^)]*host\s*=\s*["\']([^"\']+)["\']',
            ],
            "description": "缓存系统"
        },
        FeatureType.MESSAGE_QUEUE: {
            "patterns": [
                r'celery',
                r'Celery\(',
                r'rabbitmq',
                r'pika',
                r'kafka',
                r'KafkaConsumer',
                r'KafkaProducer',
                r'bull',
                r'bullmq',
                r'@RabbitListener',
                r'@KafkaListener',
                r'JmsTemplate',
            ],
            "extract": [
                r'Celery\([\'"]([^\'"]+)[\'"]',
                r'@RabbitListener\(queues\s*=\s*["\']([^"\']+)["\']',
            ],
            "description": "消息队列"
        },
        FeatureType.DATABASE: {
            "patterns": [
                r'sqlalchemy',
                r'SQLAlchemy',
                r'create_engine',
                r'sessionmaker',
                r'mongoose',
                r'MongoClient',
                r'psycopg2',
                r'pg',
                r'mysql',
                r'MySQLdb',
                r'DataSource',
                r'@Entity',
                r'JpaRepository',
                r'@Repository',
            ],
            "extract": [
                r'create_engine\(["\']([^"\']+)["\']',
                r'mongoose\.connect\(["\']([^"\']+)["\']',
            ],
            "description": "数据库"
        },
        FeatureType.WEBSOCKET: {
            "patterns": [
                r'WebSocket',
                r'websocket',
                r'SocketIO',
                r'socket\.io',
                r'@WebSocket',
                r'@ServerEndpoint',
                r'WebSocketHandler',
                r'useWebSocket',
            ],
            "extract": [
                r'@ServerEndpoint\(["\']([^"\']+)["\']',
                r'WebSocket\(["\']([^"\']+)["\']',
            ],
            "description": "WebSocket"
        },
        FeatureType.AUTH: {
            "patterns": [
                r'JWT',
                r'jwt',
                r'jsonwebtoken',
                r'OAuth2PasswordBearer',
                r'Passport',
                r'passport',
                r'bcrypt',
                r'argon2',
                r'AuthenticationManager',
                r'@PreAuthorize',
                r'@Secured',
            ],
            "extract": [
                r'OAuth2PasswordBearer\([^)]*tokenUrl\s*=\s*["\']([^"\']+)["\']',
            ],
            "description": "认证系统"
        },
        FeatureType.LOGGING: {
            "patterns": [
                r'logging\.getLogger',
                r'winston',
                r'log4js',
                r'pino',
                r'@Slf4j',
                r'Logger',
                r'LoggerFactory',
                r'LogManager',
            ],
            "extract": [
                r'logging\.getLogger\(["\']([^"\']+)["\']',
                r'LoggerFactory\.getLogger\((\w+)\.class\)',
            ],
            "description": "日志系统"
        },
        FeatureType.MONITORING: {
            "patterns": [
                r'prometheus',
                r'Prometheus',
                r'grafana',
                r'datadog',
                r'sentry',
                r'Sentry',
                r'newrelic',
                r'@Timed',
                r'@Metered',
                r'Micrometer',
                r'opentelemetry',
            ],
            "extract": [
                r'sentry_sdk\.init\([^)]*dsn\s*=\s*["\']([^"\']+)["\']',
            ],
            "description": "监控系统"
        },
        FeatureType.EMAIL: {
            "patterns": [
                r'smtplib',
                r'SMTP',
                r'sendgrid',
                r'SendGrid',
                r'mailgun',
                r'nodemailer',
                r'JavaMailSender',
                r'@Email',
            ],
            "extract": [
                r'smtplib\.SMTP\(["\']([^"\']+)["\']',
            ],
            "description": "邮件服务"
        },
        FeatureType.STORAGE: {
            "patterns": [
                r'boto3',
                r'aws-sdk',
                r'AWS',
                r'S3',
                r'azure-storage',
                r'google-cloud-storage',
                r'minio',
                r'MinioClient',
                r'@StorageService',
            ],
            "extract": [
                r'boto3\.client\(["\'](\w+)["\']',
            ],
            "description": "存储服务"
        }
    }
    
    FRAMEWORK_PATTERNS = {
        'fastapi': [r'from fastapi', r'import fastapi', r'FastAPI\('],
        'flask': [r'from flask', r'import flask', r'Flask\('],
        'django': [r'from django', r'import django', r'DJANGO_SETTINGS'],
        'express': [r'express\(\)', r"require\(['\"]express['\"]\)", r"from ['\"]express['\"]"],
        'nestjs': [r'@Module', r'@Controller', r'@Injectable'],
        'spring': [r'@SpringBootApplication', r'@RestController', r'@Service'],
        'react': [r'from react', r"import.*from ['\"]react['\"]", r'React\.Component'],
        'vue': [r'from vue', r"import.*from ['\"]vue['\"]", r'createApp'],
        'nextjs': [r'from next', r"import.*from ['\"]next['\"]"],
    }
    
    def detect(self, content: str, file_path: str) -> List[SystemFeature]:
        features = []
        lines = content.split('\n')
        
        detected_framework = self._detect_framework(content)
        
        for feature_type, config in self.FEATURE_PATTERNS.items():
            for pattern in config["patterns"]:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    name = self._extract_name(content, match, config.get("extract", []))
                    
                    feature_config = self._extract_config(content, match, feature_type)
                    
                    features.append(SystemFeature(
                        type=feature_type,
                        name=name,
                        description=config["description"],
                        file_path=file_path,
                        line=line_num,
                        config=feature_config,
                        framework=detected_framework
                    ))
        
        return self._deduplicate_features(features)
    
    def _detect_framework(self, content: str) -> str:
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return framework
        return "unknown"
    
    def _extract_name(self, content: str, match, extract_patterns: List[str]) -> str:
        for pattern in extract_patterns:
            try:
                name_match = re.search(pattern, content[match.start():match.start() + 200])
                if name_match:
                    return name_match.group(1)
            except Exception:
                pass
        
        return match.group(0)
    
    def _extract_config(self, content: str, match, feature_type: FeatureType) -> Dict:
        config = {}
        
        start = max(0, match.start() - 50)
        end = min(len(content), match.end() + 200)
        context = content[start:end]
        
        host_match = re.search(r'host\s*[:=]\s*["\']([^"\']+)["\']', context)
        if host_match:
            config['host'] = host_match.group(1)
        
        port_match = re.search(r'port\s*[:=]\s*(\d+)', context)
        if port_match:
            config['port'] = int(port_match.group(1))
        
        url_match = re.search(r'url\s*[:=]\s*["\']([^"\']+)["\']', context)
        if url_match:
            config['url'] = url_match.group(1)
        
        return config
    
    def _deduplicate_features(self, features: List[SystemFeature]) -> List[SystemFeature]:
        seen = set()
        unique_features = []
        
        for feature in features:
            key = (feature.type, feature.file_path, feature.line)
            if key not in seen:
                seen.add(key)
                unique_features.append(feature)
        
        return unique_features
    
    def detect_all(self, content: str, file_path: str) -> Dict:
        features = self.detect(content, file_path)
        
        summary = {
            "total_features": len(features),
            "by_type": {},
            "file_path": file_path
        }
        
        for feature in features:
            type_name = feature.type.value
            if type_name not in summary["by_type"]:
                summary["by_type"][type_name] = []
            summary["by_type"][type_name].append(feature.name)
        
        return {
            "features": features,
            "summary": summary
        }
