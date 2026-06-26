#!/usr/bin/env python3
"""
Linus Dev Tools - 开发者工具合集技能
提供加密、编码、网络、令牌、数据格式等常用开发工具
"""

import argparse
import hashlib
import hmac
import base64
import json
import re
import secrets
import string
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 加密工具模块 ====================

class CryptoTools:
    """加密工具类 - 提供 MD5、SHA、AES、Base64 等加密算法"""

    @staticmethod
    def md5(text: str, uppercase: bool = False) -> str:
        """MD5 加密"""
        result = hashlib.md5(text.encode()).hexdigest()
        return result.upper() if uppercase else result

    @staticmethod
    def sha1(text: str, uppercase: bool = False) -> str:
        """SHA1 加密"""
        result = hashlib.sha1(text.encode()).hexdigest()
        return result.upper() if uppercase else result

    @staticmethod
    def sha256(text: str, uppercase: bool = False) -> str:
        """SHA256 加密"""
        result = hashlib.sha256(text.encode()).hexdigest()
        return result.upper() if uppercase else result

    @staticmethod
    def sha512(text: str, uppercase: bool = False) -> str:
        """SHA512 加密"""
        result = hashlib.sha512(text.encode()).hexdigest()
        return result.upper() if uppercase else result

    @staticmethod
    def hmac_sha256(text: str, key: str, uppercase: bool = False) -> str:
        """HMAC-SHA256 加密"""
        result = hmac.new(key.encode(), text.encode(), hashlib.sha256).hexdigest()
        return result.upper() if uppercase else result

    @staticmethod
    def base64_encode(text: str) -> str:
        """Base64 编码"""
        return base64.b64encode(text.encode()).decode()

    @staticmethod
    def base64_decode(text: str) -> str:
        """Base64 解码"""
        try:
            return base64.b64decode(text.encode()).decode()
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def url_encode(text: str) -> str:
        """URL 编码"""
        from urllib.parse import quote
        return quote(text)

    @staticmethod
    def url_decode(text: str) -> str:
        """URL 解码"""
        from urllib.parse import unquote
        return unquote(text)


# ==================== 网络工具模块 ====================

class NetworkTools:
    """网络工具类 - 端口生成、IP 工具、时间戳转换等"""

    COMMON_PORTS = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        993: "IMAPS",
        995: "POP3S",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        6379: "Redis",
        8080: "HTTP-Proxy",
        8443: "HTTPS-Alt",
        27017: "MongoDB"
    }

    @staticmethod
    def generate_ports(start: int = 1, end: int = 65535, count: int = 10) -> List[int]:
        """生成随机端口号"""
        import random
        return random.sample(range(start, min(end, start + 1000)), min(count, 100))

    @staticmethod
    def check_common_port(port: int) -> str:
        """查询常见端口用途"""
        return NetworkTools.COMMON_PORTS.get(port, "未知/非常用端口")

    @staticmethod
    def timestamp_to_datetime(timestamp: int, unit: str = 'seconds') -> str:
        """时间戳转日期时间"""
        try:
            if unit == 'milliseconds':
                timestamp = timestamp / 1000
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def datetime_to_timestamp(datetime_str: str, format: str = '%Y-%m-%d %H:%M:%S') -> int:
        """日期时间转时间戳"""
        try:
            dt = datetime.strptime(datetime_str, format)
            return int(dt.timestamp())
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def get_current_timestamp(unit: str = 'seconds') -> int:
        """获取当前时间戳"""
        ts = time.time()
        return int(ts) if unit == 'seconds' else int(ts * 1000)

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """验证 IP 地址格式"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip):
            parts = ip.split('.')
            return all(0 <= int(p) <= 255 for p in parts)
        return False

    @staticmethod
    def validate_domain(domain: str) -> bool:
        """验证域名格式"""
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))

    @staticmethod
    def ip_to_int(ip: str) -> int:
        """IP 地址转整数"""
        parts = ip.split('.')
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])

    @staticmethod
    def int_to_ip(num: int) -> str:
        """整数转 IP 地址"""
        return f"{(num >> 24) & 255}.{(num >> 16) & 255}.{(num >> 8) & 255}.{num & 255}"


# ==================== 令牌工具模块 ====================

class TokenTools:
    """令牌工具类 - Token 生成、校验、签名等"""

    JWT_HEADER = '{"alg":"HS256","typ":"JWT"}'

    @staticmethod
    def generate_uuid() -> str:
        """生成 UUID"""
        return str(uuid.uuid4())

    @staticmethod
    def generate_uuid_short() -> str:
        """生成短 UUID（无连字符）"""
        return uuid.uuid4().hex

    @staticmethod
    def generate_token(length: int = 32, use_hex: bool = False) -> str:
        """生成随机 Token"""
        if use_hex:
            return secrets.token_hex(length // 2)
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_api_key(prefix: str = 'sk') -> str:
        """生成 API Key（类似 sk-xxx 格式）"""
        random_part = secrets.token_hex(24)
        return f"{prefix}-{random_part}"

    @staticmethod
    def validate_uuid(token: str) -> bool:
        """验证 UUID 格式"""
        try:
            uuid.UUID(token)
            return True
        except ValueError:
            return False

    @staticmethod
    def generate_jwt(payload: Dict[str, Any], secret: str, algorithm: str = 'HS256') -> str:
        """生成 JWT Token"""
        header = TokenTools.JWT_HEADER
        header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')

        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')

        return f"{message}.{signature_b64}"

    @staticmethod
    def decode_jwt(token: str, secret: Optional[str] = None) -> Dict[str, Any]:
        """解码 JWT Token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return {"error": "Invalid JWT format"}

            header_b64, payload_b64, _ = parts

            # 补全 padding
            header_b64 += '=' * (4 - len(header_b64) % 4)
            payload_b64 += '=' * (4 - len(payload_b64) % 4)

            header = json.loads(base64.urlsafe_b64decode(header_b64))
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))

            result = {"header": header, "payload": payload}

            if secret:
                # 验证签名
                message = f"{header_b64.rstrip('=')}.{payload_b64.rstrip('=')}"
                expected_sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
                expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
                result["signature_valid"] = (expected_sig_b64 == token.split('.')[2])

            return result
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def generate_signature(params: Dict[str, Any], secret: str, algorithm: str = 'md5') -> str:
        """生成请求签名"""
        # 按 key 排序
        sorted_params = sorted(params.items())
        # 拼接字符串
        query_string = '&'.join(f"{k}={v}" for k, v in sorted_params)
        # 添加密钥
        sign_string = f"{query_string}&key={secret}"

        if algorithm == 'md5':
            return hashlib.md5(sign_string.encode()).hexdigest().upper()
        elif algorithm == 'sha256':
            return hashlib.sha256(sign_string.encode()).hexdigest().upper()
        else:
            return hashlib.md5(sign_string.encode()).hexdigest().upper()

    @staticmethod
    def verify_signature(params: Dict[str, Any], sign: str, secret: str, algorithm: str = 'md5') -> bool:
        """验证签名"""
        expected_sign = TokenTools.generate_signature(params, secret, algorithm)
        return expected_sign.upper() == sign.upper()


# ==================== 数据格式工具模块 ====================

class DataFormatTools:
    """数据格式工具类 - JSON、CSV、XML 等格式转换"""

    @staticmethod
    def json_format(text: str, indent: int = 2) -> str:
        """格式化 JSON"""
        try:
            obj = json.loads(text)
            return json.dumps(obj, indent=indent, ensure_ascii=False)
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def json_minify(text: str) -> str:
        """压缩 JSON"""
        try:
            obj = json.loads(text)
            return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def csv_to_json(csv_text: str) -> str:
        """CSV 转 JSON"""
        try:
            lines = csv_text.strip().split('\n')
            if len(lines) < 2:
                return "Error: CSV 需要至少包含表头和数据行"

            headers = [h.strip() for h in lines[0].split(',')]
            result = []

            for line in lines[1:]:
                values = [v.strip() for v in line.split(',')]
                row = {headers[i]: values[i] for i in range(len(headers))}
                result.append(row)

            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def json_to_csv(json_text: str) -> str:
        """JSON 转 CSV"""
        try:
            data = json.loads(json_text)
            if not isinstance(data, list) or len(data) == 0:
                return "Error: JSON 必须是对象数组"

            headers = list(data[0].keys())
            lines = [','.join(headers)]

            for item in data:
                values = [str(item.get(h, '')) for h in headers]
                lines.append(','.join(values))

            return '\n'.join(lines)
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def escape_html(text: str) -> str:
        """HTML 转义"""
        import html
        return html.escape(text)

    @staticmethod
    def unescape_html(text: str) -> str:
        """HTML 反转义"""
        import html
        return html.unescape(text)


# ==================== 颜色输出工具 ====================

class ColorOutput:
    """彩色输出工具"""

    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }

    @staticmethod
    def colorize(text: str, color: str = 'reset', bold: bool = False) -> str:
        """给文本着色"""
        color_code = ColorOutput.COLORS.get(color, '')
        bold_code = ColorOutput.COLORS['bold'] if bold else ''
        reset = ColorOutput.COLORS['reset']
        return f"{bold_code}{color_code}{text}{reset}"


# ==================== 主程序 ====================

def print_banner():
    """打印横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║           Linus Dev Tools - 开发者工具合集                ║
║                    Version 1.0.0                          ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(ColorOutput.colorize(banner, 'cyan', bold=True))


def cmd_crypto(args):
    """加密工具命令"""
    crypto = CryptoTools()

    if args.action == 'md5':
        result = crypto.md5(args.text, args.uppercase)
        print(f"MD5: {result}")
    elif args.action == 'sha1':
        result = crypto.sha1(args.text, args.uppercase)
        print(f"SHA1: {result}")
    elif args.action == 'sha256':
        result = crypto.sha256(args.text, args.uppercase)
        print(f"SHA256: {result}")
    elif args.action == 'sha512':
        result = crypto.sha512(args.text, args.uppercase)
        print(f"SHA512: {result}")
    elif args.action == 'hmac':
        result = crypto.hmac_sha256(args.text, args.key, args.uppercase)
        print(f"HMAC-SHA256: {result}")
    elif args.action == 'base64-encode':
        result = crypto.base64_encode(args.text)
        print(f"Base64 Encoded: {result}")
    elif args.action == 'base64-decode':
        result = crypto.base64_decode(args.text)
        print(f"Base64 Decoded: {result}")
    elif args.action == 'url-encode':
        result = crypto.url_encode(args.text)
        print(f"URL Encoded: {result}")
    elif args.action == 'url-decode':
        result = crypto.url_decode(args.text)
        print(f"URL Decoded: {result}")


def cmd_network(args):
    """网络工具命令"""
    network = NetworkTools()

    if args.action == 'gen-ports':
        ports = network.generate_ports(args.start, args.end, args.count)
        print(f"生成的随机端口号 ({len(ports)}个):")
        for port in ports:
            usage = network.check_common_port(port)
            print(f"  {port} - {usage}")
    elif args.action == 'check-port':
        usage = network.check_common_port(args.port)
        print(f"端口 {args.port}: {usage}")
    elif args.action == 'ts-to-datetime':
        result = network.timestamp_to_datetime(args.timestamp, args.unit)
        print(f"时间戳 {args.timestamp} -> {result}")
    elif args.action == 'datetime-to-ts':
        result = network.datetime_to_timestamp(args.datetime, args.format)
        print(f"日期时间 {args.datetime} -> {result}")
    elif args.action == 'now':
        ts_sec = network.get_current_timestamp('seconds')
        ts_ms = network.get_current_timestamp('milliseconds')
        print(f"当前时间戳:\n  秒：{ts_sec}\n  毫秒：{ts_ms}")
    elif args.action == 'validate-ip':
        result = network.validate_ip(args.ip)
        status = ColorOutput.colorize("有效", 'green') if result else ColorOutput.colorize("无效", 'red')
        print(f"IP 地址 {args.ip}: {status}")
    elif args.action == 'validate-domain':
        result = network.validate_domain(args.domain)
        status = ColorOutput.colorize("有效", 'green') if result else ColorOutput.colorize("无效", 'red')
        print(f"域名 {args.domain}: {status}")
    elif args.action == 'ip-to-int':
        result = network.ip_to_int(args.ip)
        print(f"IP {args.ip} -> 整数：{result}")
    elif args.action == 'int-to-ip':
        result = network.int_to_ip(args.num)
        print(f"整数 {args.num} -> IP: {result}")


def cmd_token(args):
    """令牌工具命令"""
    token = TokenTools()

    if args.action == 'uuid':
        result = token.generate_uuid()
        print(f"UUID: {result}")
    elif args.action == 'uuid-short':
        result = token.generate_uuid_short()
        print(f"UUID (短): {result}")
    elif args.action == 'token':
        result = token.generate_token(args.length, args.hex)
        print(f"Token: {result}")
    elif args.action == 'api-key':
        result = token.generate_api_key(args.prefix)
        print(f"API Key: {result}")
    elif args.action == 'validate-uuid':
        result = token.validate_uuid(args.uuid)
        status = ColorOutput.colorize("有效", 'green') if result else ColorOutput.colorize("无效", 'red')
        print(f"UUID {args.uuid}: {status}")
    elif args.action == 'jwt-generate':
        payload = json.loads(args.payload) if args.payload else {}
        result = token.generate_jwt(payload, args.secret)
        print(f"JWT Token:\n{result}")
    elif args.action == 'jwt-decode':
        result = token.decode_jwt(args.token, args.secret)
        print(f"JWT 解码结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    elif args.action == 'sign':
        params = json.loads(args.params) if args.params else {}
        result = token.generate_signature(params, args.secret, args.algo)
        print(f"签名 ({args.algo.upper()}): {result}")
    elif args.action == 'verify-sign':
        params = json.loads(args.params) if args.params else {}
        result = token.verify_signature(params, args.sign, args.secret, args.algo)
        status = ColorOutput.colorize("有效", 'green') if result else ColorOutput.colorize("无效", 'red')
        print(f"签名验证：{status}")


def cmd_format(args):
    """数据格式工具命令"""
    fmt = DataFormatTools()

    if args.action == 'json-format':
        result = fmt.json_format(args.text, args.indent)
        print(result)
    elif args.action == 'json-minify':
        result = fmt.json_minify(args.text)
        print(result)
    elif args.action == 'csv-to-json':
        result = fmt.csv_to_json(args.text)
        print(result)
    elif args.action == 'json-to-csv':
        result = fmt.json_to_csv(args.text)
        print(result)
    elif args.action == 'escape-html':
        result = fmt.escape_html(args.text)
        print(f"HTML Escaped: {result}")
    elif args.action == 'unescape-html':
        result = fmt.unescape_html(args.text)
        print(f"HTML Unescaped: {result}")


def cmd_ai(args):
    """AI 调用命令"""
    print(ColorOutput.colorize("AI 调用功能", 'purple', bold=True))
    print(f"模型：{args.model}")
    print(f"提示词：{args.prompt}")
    print()

    # 模拟 AI 响应（实际使用时可集成真实 AI API）
    ai_response = {
        "status": "success",
        "model": args.model,
        "prompt": args.prompt,
        "response": "这是一个模拟的 AI 响应。配置 API KEY 后可调用真实 AI 服务。",
        "timestamp": datetime.now().isoformat()
    }

    print(json.dumps(ai_response, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description='Linus Dev Tools - 开发者工具合集',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 加密工具
  python main.py crypto md5 "hello world"
  python main.py crypto sha256 "password" --uppercase
  python main.py crypto base64-encode "hello"

  # 网络工具
  python main.py network gen-ports --count 5
  python main.py network now
  python main.py network ts-to-datetime 1700000000

  # 令牌工具
  python main.py token uuid
  python main.py token api-key --prefix sk
  python main.py token sign --params '{"app_id":"123","ts":1700000000}' --secret mykey

  # 数据格式
  python main.py format json-format --text '{"name":"test"}'
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='命令类型')

    # 加密工具命令
    crypto_parser = subparsers.add_parser('crypto', help='加密工具')
    crypto_parser.add_argument('action', choices=['md5', 'sha1', 'sha256', 'sha512', 'hmac',
                                                   'base64-encode', 'base64-decode',
                                                   'url-encode', 'url-decode'],
                              help='加密操作')
    crypto_parser.add_argument('text', nargs='?', default='', help='输入文本')
    crypto_parser.add_argument('--key', help='HMAC 密钥')
    crypto_parser.add_argument('--uppercase', action='store_true', help='输出大写')
    crypto_parser.set_defaults(func=cmd_crypto)

    # 网络工具命令
    network_parser = subparsers.add_parser('network', help='网络工具')
    network_parser.add_argument('action', choices=['gen-ports', 'check-port', 'ts-to-datetime',
                                                    'datetime-to-ts', 'now', 'validate-ip',
                                                    'validate-domain', 'ip-to-int', 'int-to-ip'],
                               help='网络操作')
    network_parser.add_argument('--text', help='输入文本')
    network_parser.add_argument('--start', type=int, default=1, help='端口范围起始')
    network_parser.add_argument('--end', type=int, default=65535, help='端口范围结束')
    network_parser.add_argument('--count', type=int, default=10, help='生成端口数量')
    network_parser.add_argument('--port', type=int, help='端口号')
    network_parser.add_argument('--timestamp', type=int, help='时间戳')
    network_parser.add_argument('--unit', choices=['seconds', 'milliseconds'], default='seconds', help='时间戳单位')
    network_parser.add_argument('--datetime', help='日期时间字符串')
    network_parser.add_argument('--format', default='%Y-%m-%d %H:%M:%S', help='日期时间格式')
    network_parser.add_argument('--ip', help='IP 地址')
    network_parser.add_argument('--domain', help='域名')
    network_parser.add_argument('--num', type=int, help='整数')
    network_parser.set_defaults(func=cmd_network)

    # 令牌工具命令
    token_parser = subparsers.add_parser('token', help='令牌工具')
    token_parser.add_argument('action', choices=['uuid', 'uuid-short', 'token', 'api-key',
                                                  'validate-uuid', 'jwt-generate', 'jwt-decode',
                                                  'sign', 'verify-sign'],
                             help='令牌操作')
    token_parser.add_argument('--length', type=int, default=32, help='Token 长度')
    token_parser.add_argument('--hex', action='store_true', help='使用十六进制')
    token_parser.add_argument('--prefix', default='sk', help='API Key 前缀')
    token_parser.add_argument('--uuid', help='待验证的 UUID')
    token_parser.add_argument('--payload', help='JWT Payload (JSON)')
    token_parser.add_argument('--secret', default='secret', help='密钥')
    token_parser.add_argument('--token', help='JWT Token')
    token_parser.add_argument('--params', help='签名参数 (JSON)')
    token_parser.add_argument('--sign', help='待验证的签名')
    token_parser.add_argument('--algo', choices=['md5', 'sha256'], default='md5', help='签名算法')
    token_parser.set_defaults(func=cmd_token)

    # 数据格式命令
    format_parser = subparsers.add_parser('format', help='数据格式工具')
    format_parser.add_argument('action', choices=['json-format', 'json-minify', 'csv-to-json',
                                                   'json-to-csv', 'escape-html', 'unescape-html'],
                              help='格式化操作')
    format_parser.add_argument('--text', required=True, help='输入文本')
    format_parser.add_argument('--indent', type=int, default=2, help='JSON 缩进')
    format_parser.set_defaults(func=cmd_format)

    # AI 调用命令
    ai_parser = subparsers.add_parser('ai', help='AI 调用')
    ai_parser.add_argument('--prompt', required=True, help='提示词')
    ai_parser.add_argument('--model', default='claude', choices=['claude', 'gpt', 'qwen'],
                          help='AI 模型')
    ai_parser.add_argument('--api-key', help='API Key')
    ai_parser.set_defaults(func=cmd_ai)

    args = parser.parse_args()

    if args.command is None:
        print_banner()
        parser.print_help()
    else:
        args.func(args)


if __name__ == '__main__':
    main()
