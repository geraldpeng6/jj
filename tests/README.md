# 策略API测试脚本

本目录包含用于测试策略相关API的测试脚本。这些脚本可以帮助您测试获取策略库列表、用户策略列表和策略详情等API功能。

## 前提条件

在运行测试脚本之前，请确保：

1. 已经安装了所需的Python依赖：
   ```bash
   pip install requests
   ```

2. 已经正确配置了认证信息：
   - 复制 `data/config/auth.json.example` 到 `data/config/auth.json`
   - 在 `auth.json` 中填写您的 `token` 和 `user_id`

## 测试脚本说明

### 1. 基础测试脚本 (test_strategy_library_api.py)

这个脚本专门用于测试获取策略库列表的API功能。

**使用方法：**
```bash
python tests/test_strategy_library_api.py
```

**功能：**
- 向策略库列表API发送请求
- 将完整的请求和响应记录到日志文件中
- 提供基本的错误处理

### 2. 通用测试脚本 (test_strategy_api.py)

这个脚本可以测试获取策略库列表和用户策略列表的API功能。

**使用方法：**
```bash
# 测试策略库列表API
python tests/test_strategy_api.py --type library

# 测试用户策略列表API
python tests/test_strategy_api.py --type user

# 同时测试两种API
python tests/test_strategy_api.py --type both

# 指定API基础URL
python tests/test_strategy_api.py --url https://api.example.com
```

**参数说明：**
- `--type`, `-t`: 策略类型，可选值为 `library`（策略库）、`user`（用户策略）或 `both`（两者都测试）
- `--url`, `-u`: API基础URL，默认为 `https://api.yueniusz.com`

### 3. 完整测试脚本 (test_strategy_api_full.py)

这个脚本提供了更多的功能和选项，可以测试获取策略库列表和用户策略列表的API功能，并支持多种输出格式。

**使用方法：**
```bash
# 测试策略库列表API，使用日志输出
python tests/test_strategy_api_full.py --type library --format log

# 测试用户策略列表API，使用JSON输出
python tests/test_strategy_api_full.py --type user --format json

# 同时测试两种API，使用JSON输出并保存到文件
python tests/test_strategy_api_full.py --type both --format json --output results.json
```

**参数说明：**
- `--type`, `-t`: 策略类型，可选值为 `library`（策略库）、`user`（用户策略）或 `both`（两者都测试）
- `--url`, `-u`: API基础URL，默认为 `https://api.yueniusz.com`
- `--format`, `-f`: 输出格式，可选值为 `log`（日志输出）或 `json`（JSON输出）
- `--output`, `-o`: 输出文件路径，仅当 `format` 为 `json` 时有效

## 日志文件

所有测试脚本都会生成详细的日志文件，包含请求和响应的完整信息。日志文件保存在 `data/logs` 目录下，文件名包含测试类型和时间戳。

例如：
- `data/logs/strategy_library_list_api_test_20230101_120000.log`
- `data/logs/strategy_user_list_api_test_20230101_120000.log`

## 注意事项

1. 请确保您的认证信息是有效的，否则API请求将会失败。
2. 日志文件中会记录敏感信息，请妥善保管。
3. 如果API请求失败，请检查日志文件以获取详细的错误信息。
4. 这些测试脚本仅用于测试API功能，不会修改任何数据。
