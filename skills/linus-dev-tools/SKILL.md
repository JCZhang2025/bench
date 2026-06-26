# Linus Dev Tools - OpenClaw 技能集成文档

## 技能信息

- **名称**: linus-dev-tools
- **版本**: 1.0.0
- **类别**: 开发工具
- **描述**: 开发者工具合集，提供加密、编码、网络、令牌、数据格式转换等常用工具

## 安装方式

```bash
# 通过 OpenClaw 安装
/skill install linus-dev-tools
```

## 使用方式

### 加密工具 (crypto)

```bash
# MD5 加密
/skill linus-dev-tools crypto md5 "hello world"

# SHA256 加密
/skill linus-dev-tools crypto sha256 "password"

# HMAC-SHA256
/skill linus-dev-tools crypto hmac "data" --key "secret"

# Base64 编码/解码
/skill linus-dev-tools crypto base64-encode "hello"
/skill linus-dev-tools crypto base64-decode "aGVsbG8="

# URL 编码/解码
/skill linus-dev-tools crypto url-encode "hello world"
/skill linus-dev-tools crypto url-decode "hello%20world"
```

### 网络工具 (network)

```bash
# 生成随机端口
/skill linus-dev-tools network gen-ports --count 5

# 查询端口用途
/skill linus-dev-tools network check-port --port 8080

# 时间戳转日期
/skill linus-dev-tools network ts-to-datetime --timestamp 1700000000

# 日期转时间戳
/skill linus-dev-tools network datetime-to-ts --datetime "2024-01-01 12:00:00"

# 获取当前时间戳
/skill linus-dev-tools network now

# 验证 IP 地址
/skill linus-dev-tools network validate-ip --ip "192.168.1.1"

# 验证域名
/skill linus-dev-tools network validate-domain --domain "example.com"

# IP 与整数转换
/skill linus-dev-tools network ip-to-int --ip "192.168.1.1"
/skill linus-dev-tools network int-to-ip --num 3232235777
```

### 令牌工具 (token)

```bash
# 生成 UUID
/skill linus-dev-tools token uuid

# 生成短 UUID
/skill linus-dev-tools token uuid-short

# 生成随机 Token
/skill linus-dev-tools token token --length 32

# 生成 API Key
/skill linus-dev-tools token api-key --prefix sk

# 验证 UUID
/skill linus-dev-tools token validate-uuid --uuid "550e8400-e29b-41d4-a716-446655440000"

# 生成 JWT
/skill linus-dev-tools token jwt-generate --payload '{"user_id":123}' --secret "mysecret"

# 解码 JWT
/skill linus-dev-tools token jwt-decode --token "eyJhbG..." --secret "mysecret"

# 生成签名
/skill linus-dev-tools token sign --params '{"app_id":"123","ts":1700000000}' --secret "mykey"

# 验证签名
/skill linus-dev-tools token verify-sign --params '{"app_id":"123"}' --sign "ABC123" --secret "mykey"
```

### 数据格式工具 (format)

```bash
# 格式化 JSON
/skill linus-dev-tools format json-format --text '{"name":"test","value":123}'

# 压缩 JSON
/skill linus-dev-tools format json-minify --text '{ "name": "test" }'

# CSV 转 JSON
/skill linus-dev-tools format csv-to-json --text "name,age\nAlice,25\nBob,30"

# JSON 转 CSV
/skill linus-dev-tools format json-to-csv --text '[{"name":"Alice","age":25}]'

# HTML 转义
/skill linus-dev-tools format escape-html --text "<script>alert(1)</script>"

# HTML 反转义
/skill linus-dev-tools format unescape-html --text "&lt;script&gt;"
```

### AI 调用 (ai)

```bash
# 调用 AI
/skill linus-dev-tools ai --prompt "解释什么是 RESTful API" --model claude
```

## 工具分类

### 加密工具
| 工具 | 描述 |
|------|------|
| md5 | MD5 哈希加密 |
| sha1 | SHA1 哈希加密 |
| sha256 | SHA256 哈希加密 |
| sha512 | SHA512 哈希加密 |
| hmac | HMAC-SHA256 加密 |
| base64-encode | Base64 编码 |
| base64-decode | Base64 解码 |
| url-encode | URL 编码 |
| url-decode | URL 解码 |

### 网络工具
| 工具 | 描述 |
|------|------|
| gen-ports | 生成随机端口号 |
| check-port | 查询端口用途 |
| ts-to-datetime | 时间戳转日期 |
| datetime-to-ts | 日期转时间戳 |
| now | 获取当前时间戳 |
| validate-ip | 验证 IP 地址 |
| validate-domain | 验证域名 |
| ip-to-int | IP 转整数 |
| int-to-ip | 整数转 IP |

### 令牌工具
| 工具 | 描述 |
|------|------|
| uuid | 生成 UUID |
| uuid-short | 生成短 UUID |
| token | 生成随机 Token |
| api-key | 生成 API Key |
| validate-uuid | 验证 UUID |
| jwt-generate | 生成 JWT |
| jwt-decode | 解码 JWT |
| sign | 生成签名 |
| verify-sign | 验证签名 |

### 数据格式工具
| 工具 | 描述 |
|------|------|
| json-format | 格式化 JSON |
| json-minify | 压缩 JSON |
| csv-to-json | CSV 转 JSON |
| json-to-csv | JSON 转 CSV |
| escape-html | HTML 转义 |
| unescape-html | HTML 反转义 |

### AI 工具
| 工具 | 描述 |
|------|------|
| ai | AI 调用（支持 Claude/GPT/Qwen） |

## 定价说明

- **免费版**: 每日 100 次操作，所有功能可用
- **Pro 版**: $9.99/月，无限次操作，支持 100 次 AI 调用

## 依赖要求

- Python >= 3.9.0
- 无外部依赖（使用标准库）
