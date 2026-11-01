# Wenya 后端测试运行说明

本文说明如何在本项目中配置并运行 `tests/` 下的接口与服务测试，以及如何判断测试是否成功。


---

## 1. 前置条件

- 操作系统：Windows（本项目当前目录结构为 Windows 环境）
- Python：建议 3.11（项目内已有 `.venv`）
- 当前工作目录：项目根目录

---

## 2. 测试环境配置

## 2.1 使用项目现有虚拟环境（推荐）

项目中已经有虚拟环境：`.venv`

在 PowerShell 中执行：

```powershell
.\.venv\Scripts\Activate.ps1
python --version
```

如果激活脚本受策略限制，可直接使用虚拟环境里的 Python：

```powershell
.\.venv\Scripts\python.exe --version
```

## 2.2 如果 `.venv` 不存在（可选）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

安装项目依赖：

```powershell
python -m pip install -r requirements.txt
```

> 说明：`requirements.txt` 已包含运行 Flask 服务与执行 `tests/` 所需的核心依赖。

## 2.3 配置真实 AI 测试环境变量（必需，用于 AI 相关用例）

优先使用测试配置文件（高于系统环境变量）：

- 配置文件路径：`tests\test_ai.env`
- 已提供模板（tests\test_ai.env.example）
- 将 tests\test_ai.env.example 复制成 tests\test_ai.env，并修改配置值
- 读取优先级：`tests\test_ai.env` > 系统环境变量

如果你不使用 `tests\test_ai.env`，也可以在 PowerShell 中设置：

```powershell
$env:TEST_REAL_AI_API_KEY = "你的真实 APIKey"
$env:TEST_REAL_AI_PROVIDER = "openai"      # 可选，默认 openai
$env:TEST_REAL_AI_API_BASE = ""             # 可选，自定义网关时填写
$env:TEST_REAL_AI_MODEL = ""                # 可选，指定模型时填写
$env:TEST_REAL_AI_ENABLE_THINKING = "false" # 可选，默认 false（aliyun 建议关闭以提速）
```

说明：
- 必填环境变量：`TEST_REAL_AI_API_KEY`
- 可选环境变量：`TEST_REAL_AI_PROVIDER`、`TEST_REAL_AI_API_BASE`、`TEST_REAL_AI_MODEL`、`TEST_REAL_AI_ENABLE_THINKING`
- 未设置 `TEST_REAL_AI_API_KEY` 时，AI 集成测试会被 `skip`，并在 pytest 输出中提示被跳过的 API 覆盖范围。
- 测试中强制 `AI_MOCK_MODE=False`，不会走模拟评分/模拟对话分支。
- pytest 结束时会额外输出 `AI integration tests skipped` 汇总段，明确列出"被跳过的 API + 跳过原因 + 需要配置的变量"。

当缺少 `TEST_REAL_AI_API_KEY` 时，以下 API 覆盖会被跳过：

- `POST /api/writing/{writing_id}/submit`
- `POST /api/writing/{writing_id}/ai-chat`
- `GET /api/ranking/overall`
- `GET /api/ranking/progress`
- `GET /api/ranking/dimension/{dimension}`
- `GET /api/ranking/my-growth-curve`
- `POST /api/community/publish/{writing_id}`
- `POST /api/community/works/{work_id}/report`
- `GET /api/community/works/{work_id}/report`
- `GET /api/memory/fragments`
- `GET /api/memory/context`
- `GET /api/memory/aggregate`
- `GET /api/memory/stats`

## 2.4 登录态与匿名接口（测试前置说明）

注册接口已从后端下线（`POST /api/auth/register`、`POST /api/auth/send-guardian-code`），测试不得通过 API 注册账号：

- 用户由 `tests/conftest.py` 的 `make_user` 夹具直接写库创建（含监护人与 `is_guardian_verified=True`）
- 登录态由 `login` 夹具调用 `POST /api/auth/login` 建立，测试 Client 自动保持会话 Cookie

允许匿名访问（未登录直接返回 200，无需 `make_user`/`login`）：

- `GET /api/health`
- `GET /api/compliance/info`
- `GET /api/challenges`
- `GET /api/challenges/{challenge_id}`
- `GET /api/materials`
- `GET /api/community/works`
- `GET /api/community/works/{work_id}`
- `GET /api/community/works/{work_id}/comments`
- `GET /api/community/featured`

其余接口均需登录，未登录访问返回 `401`（由 `app.py` 的 `unauthorized_handler` 统一输出 JSON）。

> 注意：匿名范围刻意只包含静态内容与已做隐私脱敏的社区只读接口。`/api/ranking/*` 返回未成年人昵称/头像/分数，未经产品与合规确认不得放开匿名。

---

## 3. 如何运行测试

## 3.1 运行全部测试

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

## 3.2 运行单个测试文件

例如运行 API 契约测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api_writing.py -q
```

例如运行认证测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api_auth.py -q
```

## 3.3 查看更详细日志

```powershell
.\.venv\Scripts\python.exe -m pytest tests -vv
```

---

## 4. 如何判断测试成功

满足以下任一标准即可判断本次执行成功：

1. 命令退出码（Exit Code）为 `0`
2. pytest 最后汇总显示全部通过，例如：

```text
================== 35 passed in 8.42s ==================
```

---

## 5. 如何判断测试失败

出现以下情况表示失败：

- 汇总中出现 `failed` / `error`，例如：

```text
=========== 2 failed, 33 passed in 9.10s ===========
```

- 或命令退出码非 `0`

可先用下列命令查看首个失败后立即停止，便于快速定位：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -x -vv
```

---

## 6. 常见问题排查

## 6.1 `pytest` 命令不可识别

不要直接用 `pytest`，改用：

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

## 6.2 依赖缺失（`ModuleNotFoundError`）

先确认用的是哪个解释器，不要直接往全局环境装包。`.venv` 与系统 Python 可能同为 3.14.x，**光看版本号分不出来**：

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
python -c "import sys; print(sys.executable)"
```

典型现象：`python -m pytest tests -q` 时全部用例在 setup 阶段报
`ModuleNotFoundError: No module named 'requests'`（导入点在
`services/api_client.py`，收集阶段即触发），而改用 `.\.venv\Scripts\python.exe -m pytest`
则全绿。原因是系统解释器只装了部分依赖（且版本漂移：SQLAlchemy 2.1.6 / pytest 9.2.0），
缺 `requests`；`.venv` 才与 `requirements.txt` 的 pin 一致。

正确做法是始终使用 `.venv`，而不是给系统 Python 补装：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

> 另注：系统 Python 里存在遗留包 `dotenv 0.9.9`，与 `python-dotenv` 争抢
> `import dotenv`（`tests/conftest.py` 用到 `from dotenv import dotenv_values`）。
> 若出现莫名的 dotenv 导入错误，优先怀疑解释器用错，而不是代码。

## 6.3 `dotenv` / 其他导入异常

按 6.2 确认解释器后，用 `.\.venv\Scripts\python.exe -m pip list` 与
`requirements.txt` 逐项比对版本，必要时重装 `.venv`（第 2.2 节）。

## 6.4 个别历史测试不稳定

先跑新增或核心测试文件确认主链路：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api_auth.py tests\test_api_common.py tests\test_api_writing.py -q
```

---

## 7. 推荐执行顺序（CI/本地）

1. 先跑契约与核心接口：
   - `tests\test_api_auth.py`
   - `tests\test_api_common.py`
   - `tests\test_api_writing.py`
2. 再跑其余测试：
   - `tests\test_api_ranking.py`
   - `tests\test_api_community.py`
   - `tests\test_api_memory.py`
3. 最后运行全部 `tests` 做回归确认。
