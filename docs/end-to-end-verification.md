# Codemux 端到端验证方案

## 验证目标

验证 Codemux 能够成功：
1. 发现运行 Claude Code 的 tmux 会话
2. 路由命令到指定会话
3. 执行真实命令并捕获响应
4. 正确处理多种使用场景
5. 提供友好的交互体验

## 验证环境要求

- macOS 或 Linux 系统
- tmux 已安装
- Claude Code 已安装
- Python 3.11+ 环境
- uv 包管理器

## 第一阶段：环境准备 (5分钟)

### 1.1 创建测试项目目录

```bash
# 创建测试项目目录结构
mkdir -p ~/tmp/codemux-e2e-test/{frontend,backend,docs,api}
cd ~/tmp/codemux-e2e-test

# 在每个目录创建不同类型的项目文件
echo '# Frontend React Project
## 当前任务
- [ ] 实现用户登录界面
- [ ] 添加路由配置' > frontend/README.md

echo '# Backend Node.js API
## 当前任务
- [ ] 设计用户认证API
- [ ] 连接数据库' > backend/README.md

echo '# 项目文档
## 系统架构
- 前端：React + TypeScript
- 后端：Node.js + Express' > docs/README.md

echo '# API Gateway
## 微服务路由
- 用户服务: /api/users
- 订单服务: /api/orders' > api/README.md

# 创建一些示例代码文件
cat > frontend/App.tsx << 'EOF'
import React from 'react';

function App() {
  return (
    <div className="App">
      <h1>Frontend Application</h1>
    </div>
  );
}

export default App;
EOF

cat > backend/server.js << 'EOF'
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
EOF
```

### 1.2 启动多个 Claude Code 会话

```bash
# 创建自动化启动脚本
cat > ~/tmp/start-claude-sessions.sh << 'EOF'
#!/bin/bash
echo "🚀 启动 Claude Code 端到端测试会话..."

# 清理已存在的测试会话
tmux kill-session -t e2e-frontend 2>/dev/null || true
tmux kill-session -t e2e-backend 2>/dev/null || true
tmux kill-session -t e2e-docs 2>/dev/null || true
tmux kill-session -t e2e-api 2>/dev/null || true

# 启动 Claude Code 会话
echo "启动 frontend 会话..."
tmux new-session -d -s e2e-frontend -c ~/tmp/codemux-e2e-test/frontend
tmux send-keys -t e2e-frontend 'claude' Enter

echo "启动 backend 会话..."
tmux new-session -d -s e2e-backend -c ~/tmp/codemux-e2e-test/backend
tmux send-keys -t e2e-backend 'claude' Enter

echo "启动 docs 会话..."
tmux new-session -d -s e2e-docs -c ~/tmp/codemux-e2e-test/docs
tmux send-keys -t e2e-docs 'claude' Enter

echo "启动 api 会话..."
tmux new-session -d -s e2e-api -c ~/tmp/codemux-e2e-test/api
tmux send-keys -t e2e-api 'claude' Enter

echo "✅ 4个 Claude Code 会话已启动"
tmux list-sessions | grep e2e-
echo ""
echo "⏳ 等待 Claude Code 完全启动..."
sleep 10
echo "🎯 准备就绪，可以开始测试！"
EOF

chmod +x ~/tmp/start-claude-sessions.sh
~/tmp/start-claude-sessions.sh
```

## 第二阶段：会话发现验证 (5分钟)

### 2.1 验证会话发现功能

```bash
cd ~/workspace/codemux

# 测试会话发现
echo "🔍 测试会话发现功能..."
uv run python scripts/test_discovery.py
```

**期望结果：**
- 发现 4 个 Claude Code 会话
- 会话名称格式正确：`hostname_frontend`, `hostname_backend`, `hostname_docs`, `hostname_api`
- 显示正确的目录路径

### 2.2 验证检测逻辑调试

```bash
# 如果发现失败，运行调试脚本
uv run python scripts/debug_detection.py
```

**期望结果：**
- 所有会话的 `Is Claude? True`
- 能看到 Claude Code 的启动文本内容

## 第三阶段：命令路由验证 (10分钟)

### 3.1 基础 CLI 功能测试

```bash
# 测试基础 CLI 组件
uv run python scripts/test_cli.py
```

### 3.2 真实命令执行测试

```bash
# 测试真实命令执行
uv run python scripts/test_real_commands.py
```

**期望结果：**
- 命令成功发送到 Claude Code 会话
- 获得真实响应和响应时间
- 错误处理正常工作

### 3.3 交互式命令路由测试

创建专门的端到端测试脚本：

```bash
# 创建交互式测试脚本
cat > scripts/e2e_interactive_test.py << 'EOF'
#!/usr/bin/env python3
"""端到端交互式测试脚本."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.command_router import CommandRouter
from codemux.output_processor import OutputProcessor
from codemux.tmux_controller import TmuxController
from rich.console import Console
from rich.table import Table


async def test_command_routing():
    """测试命令路由功能."""
    console = Console()
    console.print("\n🧪 [bold cyan]Codemux 端到端命令路由测试[/bold cyan]\n")

    # 初始化组件
    tmux = TmuxController()
    processor = OutputProcessor(tmux)
    router = CommandRouter(tmux, processor)

    # 发现会话
    console.print("1️⃣ 发现 Claude Code 会话...")
    sessions = tmux.discover_claude_sessions()
    router.update_sessions(sessions)

    if not sessions:
        console.print("❌ 未发现 Claude Code 会话")
        return False

    # 显示发现的会话
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("会话名称", style="cyan")
    table.add_column("目录", style="green")
    table.add_column("路径", style="yellow")

    for session in sessions:
        table.add_row(
            session['name'],
            session['dirname'],
            session['current_path'] or "unknown"
        )

    console.print(table)
    console.print()

    # 测试用例
    test_cases = [
        {
            "name": "状态查询",
            "command": "status",
            "description": "查看所有会话状态"
        },
        {
            "name": "会话切换 - frontend",
            "command": "switch to frontend",
            "description": "切换到前端项目会话"
        },
        {
            "name": "中文会话切换",
            "command": "切换到 backend",
            "description": "使用中文切换到后端会话"
        },
        {
            "name": "# 语法 - 简单命令",
            "command": "#docs pwd",
            "description": "在文档会话执行 pwd 命令"
        },
        {
            "name": "# 语法 - 文件操作",
            "command": "#frontend ls -la",
            "description": "在前端会话列出文件"
        },
        {
            "name": "当前会话命令",
            "command": "echo 'Hello from current session'",
            "description": "在当前活跃会话执行命令"
        },
        {
            "name": "模糊匹配",
            "command": "switch to api",
            "description": "模糊匹配切换到 API 会话"
        },
        {
            "name": "复杂命令",
            "command": "#backend cat README.md",
            "description": "在后端会话读取 README 文件"
        }
    ]

    # 执行测试用例
    console.print("2️⃣ 开始测试命令路由...\n")

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        console.print(f"[bold blue]测试 {i}/{total}:[/bold blue] {test_case['name']}")
        console.print(f"[dim]命令:[/dim] {test_case['command']}")
        console.print(f"[dim]说明:[/dim] {test_case['description']}")

        try:
            # 执行命令
            start_time = asyncio.get_event_loop().time()
            result = await router.route_command(test_case['command'])
            end_time = asyncio.get_event_loop().time()

            # 显示结果
            console.print(f"[green]✅ 成功[/green] (⏱️ {end_time - start_time:.1f}s)")
            console.print(f"[dim]响应:[/dim] {result[:100]}{'...' if len(result) > 100 else ''}")
            passed += 1

        except Exception as e:
            console.print(f"[red]❌ 失败[/red]: {str(e)}")

        console.print()

        # 短暂延迟避免过快执行
        if i < total:
            await asyncio.sleep(1)

    # 测试总结
    console.print(f"3️⃣ [bold green]测试完成[/bold green]")
    console.print(f"通过: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        console.print("🎉 [bold green]所有测试通过！[/bold green]")
        return True
    else:
        console.print("⚠️ [yellow]部分测试失败[/yellow]")
        return False


def main():
    """主测试入口."""
    try:
        success = asyncio.run(test_command_routing())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF

chmod +x scripts/e2e_interactive_test.py
uv run python scripts/e2e_interactive_test.py
```

**期望结果：**
- 8 个测试用例全部通过
- 状态查询显示 4 个会话
- 中英文命令都能正确处理
- `#session` 语法正常工作
- 会话切换功能正常
- 命令执行有实际响应

## 第四阶段：交互式 CLI 验证 (15分钟)

### 4.1 启动交互式 CLI

```bash
# 启动交互式 CLI
uv run codemux
```

### 4.2 手动测试序列

在 CLI 中依次执行以下命令：

```bash
# 1. 查看帮助
help

# 2. 查看会话状态
status

# 3. 切换到前端会话
switch to frontend

# 4. 查看当前状态（应该显示 frontend 会话为当前会话）
status

# 5. 在当前会话执行命令
pwd

# 6. 使用 # 语法在其他会话执行命令
#backend pwd

# 7. 中文命令测试
切换到 docs

# 8. 执行文件操作
ls -la

# 9. 切换到 API 会话并执行命令
#api cat README.md

# 10. 测试模糊匹配
switch to back

# 11. 测试错误处理
switch to nonexistent

# 12. 刷新会话列表
refresh

# 13. 退出
quit
```

### 4.3 验证检查点

**CLI 界面检查：**
- [ ] 启动时显示欢迎信息和帮助提示
- [ ] 提示符显示当前会话信息 `codemux(hostname_frontend)> `
- [ ] 命令响应格式清晰，包含会话名和执行时间
- [ ] 错误信息友好明确
- [ ] 帮助信息完整准确

**命令执行检查：**
- [ ] `status` - 显示 4 个会话，当前会话有 `*` 标记
- [ ] `switch to frontend` - 成功切换，提示符更新
- [ ] `pwd` - 在当前会话执行，返回正确路径
- [ ] `#backend pwd` - 跨会话执行，返回不同路径
- [ ] `切换到 docs` - 中文命令正常工作
- [ ] `ls -la` - 文件列表命令正常执行
- [ ] `switch to back` - 模糊匹配到 backend 会话
- [ ] `switch to nonexistent` - 显示错误和可用会话列表
- [ ] `refresh` - 重新发现会话

## 第五阶段：压力和稳定性测试 (10分钟)

### 5.1 并发命令测试

```bash
# 创建并发测试脚本
cat > scripts/stress_test.py << 'EOF'
#!/usr/bin/env python3
"""压力测试脚本."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.command_router import CommandRouter
from codemux.output_processor import OutputProcessor
from codemux.tmux_controller import TmuxController
from rich.console import Console


async def run_concurrent_commands():
    """运行并发命令测试."""
    console = Console()
    console.print("🔥 [bold red]Codemux 压力测试[/bold red]\n")

    # 初始化
    tmux = TmuxController()
    processor = OutputProcessor(tmux)
    router = CommandRouter(tmux, processor)

    sessions = tmux.discover_claude_sessions()
    router.update_sessions(sessions)

    if len(sessions) < 2:
        console.print("❌ 需要至少 2 个会话进行压力测试")
        return False

    # 测试命令列表
    commands = [
        "#frontend pwd",
        "#backend ls",
        "#docs pwd",
        "#api ls -la",
        "status",
        "switch to frontend",
        "#backend echo 'test'",
        "#docs cat README.md"
    ]

    console.print(f"📋 准备执行 {len(commands)} 个并发命令...")

    # 记录开始时间
    start_time = time.time()

    # 创建并发任务
    tasks = []
    for i, cmd in enumerate(commands):
        task = asyncio.create_task(
            router.route_command(cmd),
            name=f"cmd_{i}_{cmd[:20]}"
        )
        tasks.append(task)

    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    total_time = end_time - start_time

    # 分析结果
    success_count = 0
    error_count = 0

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            console.print(f"❌ 命令 {i+1} 失败: {result}")
            error_count += 1
        else:
            console.print(f"✅ 命令 {i+1} 成功")
            success_count += 1

    # 显示统计信息
    console.print(f"\n📊 [bold cyan]压力测试结果[/bold cyan]")
    console.print(f"总命令数: {len(commands)}")
    console.print(f"成功: {success_count}")
    console.print(f"失败: {error_count}")
    console.print(f"成功率: {success_count/len(commands)*100:.1f}%")
    console.print(f"总时间: {total_time:.2f}s")
    console.print(f"平均响应时间: {total_time/len(commands):.2f}s")

    return error_count == 0


async def test_session_stability():
    """测试会话稳定性."""
    console = Console()
    console.print("\n🔄 [bold yellow]会话稳定性测试[/bold yellow]")

    tmux = TmuxController()

    # 连续发现会话 10 次
    for i in range(10):
        sessions = tmux.discover_claude_sessions()
        console.print(f"第 {i+1} 次发现: {len(sessions)} 个会话")
        await asyncio.sleep(0.5)

    console.print("✅ 会话发现稳定性测试完成")
    return True


async def main():
    """主测试函数."""
    console = Console()

    # 运行并发测试
    success1 = await run_concurrent_commands()

    # 运行稳定性测试
    success2 = await test_session_stability()

    if success1 and success2:
        console.print("\n🎉 [bold green]所有压力测试通过！[/bold green]")
        return True
    else:
        console.print("\n⚠️ [red]部分压力测试失败[/red]")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断")
        sys.exit(1)
EOF

chmod +x scripts/stress_test.py
uv run python scripts/stress_test.py
```

### 5.2 长时间运行测试

```bash
# 创建长时间运行测试
cat > scripts/longevity_test.py << 'EOF'
#!/usr/bin/env python3
"""长时间运行测试."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.command_router import CommandRouter
from codemux.output_processor import OutputProcessor
from codemux.tmux_controller import TmuxController
from rich.console import Console


async def longevity_test(duration_minutes=5):
    """长时间运行测试."""
    console = Console()
    console.print(f"⏰ [bold green]长时间运行测试 ({duration_minutes} 分钟)[/bold green]\n")

    tmux = TmuxController()
    processor = OutputProcessor(tmux)
    router = CommandRouter(tmux, processor)

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    cycle = 0
    total_commands = 0
    total_errors = 0

    commands = ["status", "#frontend pwd", "#backend ls", "switch to docs"]

    while time.time() < end_time:
        cycle += 1
        console.print(f"🔄 周期 {cycle}")

        # 重新发现会话
        sessions = tmux.discover_claude_sessions()
        router.update_sessions(sessions)

        # 执行测试命令
        for cmd in commands:
            try:
                result = await router.route_command(cmd)
                total_commands += 1
                console.print(f"  ✅ {cmd}")
            except Exception as e:
                total_errors += 1
                console.print(f"  ❌ {cmd}: {e}")

        # 等待下一个周期
        await asyncio.sleep(10)

    # 显示总结
    console.print(f"\n📈 [bold cyan]长时间测试总结[/bold cyan]")
    console.print(f"运行时间: {duration_minutes} 分钟")
    console.print(f"完成周期: {cycle}")
    console.print(f"总命令数: {total_commands}")
    console.print(f"错误数: {total_errors}")
    console.print(f"错误率: {total_errors/total_commands*100:.2f}%" if total_commands > 0 else "N/A")

    return total_errors == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(longevity_test(2))  # 2分钟测试
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断")
        sys.exit(1)
EOF

chmod +x scripts/longevity_test.py
uv run python scripts/longevity_test.py
```

## 第六阶段：性能基准测试 (5分钟)

### 6.1 响应时间基准测试

```bash
# 创建性能基准测试
cat > scripts/benchmark_test.py << 'EOF'
#!/usr/bin/env python3
"""性能基准测试."""

import asyncio
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.command_router import CommandRouter
from codemux.output_processor import OutputProcessor
from codemux.tmux_controller import TmuxController
from rich.console import Console
from rich.table import Table


async def benchmark_commands():
    """命令执行性能基准测试."""
    console = Console()
    console.print("🏁 [bold blue]Codemux 性能基准测试[/bold blue]\n")

    tmux = TmuxController()
    processor = OutputProcessor(tmux)
    router = CommandRouter(tmux, processor)

    sessions = tmux.discover_claude_sessions()
    router.update_sessions(sessions)

    if not sessions:
        console.print("❌ 未发现会话")
        return False

    # 基准测试用例
    benchmarks = [
        {"name": "会话发现", "func": lambda: tmux.discover_claude_sessions()},
        {"name": "状态查询", "func": lambda: router.handle_status_query()},
        {"name": "会话切换", "func": lambda: asyncio.run(router.handle_session_command("frontend", ""))},
        {"name": "简单命令", "func": lambda: asyncio.run(router.route_command("#frontend pwd"))},
    ]

    results = {}

    for benchmark in benchmarks:
        console.print(f"🏃 测试: {benchmark['name']}")
        times = []

        # 每个测试运行 5 次
        for i in range(5):
            start = time.time()
            try:
                result = benchmark['func']()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                console.print(f"  ❌ 运行 {i+1} 失败: {e}")
                continue
            end = time.time()

            execution_time = (end - start) * 1000  # 转换为毫秒
            times.append(execution_time)
            console.print(f"  运行 {i+1}: {execution_time:.1f}ms")

        if times:
            results[benchmark['name']] = {
                'min': min(times),
                'max': max(times),
                'avg': statistics.mean(times),
                'median': statistics.median(times)
            }

    # 显示基准测试结果
    console.print(f"\n📊 [bold cyan]性能基准测试结果[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("测试项目", style="cyan")
    table.add_column("最小值 (ms)", style="green")
    table.add_column("最大值 (ms)", style="red")
    table.add_column("平均值 (ms)", style="yellow")
    table.add_column("中位数 (ms)", style="blue")

    for name, stats in results.items():
        table.add_row(
            name,
            f"{stats['min']:.1f}",
            f"{stats['max']:.1f}",
            f"{stats['avg']:.1f}",
            f"{stats['median']:.1f}"
        )

    console.print(table)

    # 性能评估
    console.print(f"\n🎯 [bold green]性能评估[/bold green]")

    benchmarks_check = [
        ("会话发现", "avg", 2000, "会话发现应在 2s 内完成"),
        ("状态查询", "avg", 100, "状态查询应在 100ms 内完成"),
        ("会话切换", "avg", 200, "会话切换应在 200ms 内完成"),
        ("简单命令", "avg", 5000, "简单命令应在 5s 内完成")
    ]

    all_passed = True
    for name, metric, threshold, description in benchmarks_check:
        if name in results:
            value = results[name][metric]
            if value <= threshold:
                console.print(f"✅ {description}: {value:.1f}ms (目标: ≤{threshold}ms)")
            else:
                console.print(f"⚠️ {description}: {value:.1f}ms (目标: ≤{threshold}ms)")
                all_passed = False

    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(benchmark_commands())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断")
        sys.exit(1)
EOF

chmod +x scripts/benchmark_test.py
uv run python scripts/benchmark_test.py
```

## 第七阶段：清理和总结 (3分钟)

### 7.1 清理测试环境

```bash
# 创建清理脚本
cat > ~/tmp/cleanup-e2e-test.sh << 'EOF'
#!/bin/bash
echo "🧹 清理端到端测试环境..."

# 停止所有测试会话
echo "停止 Claude Code 测试会话..."
tmux kill-session -t e2e-frontend 2>/dev/null || true
tmux kill-session -t e2e-backend 2>/dev/null || true
tmux kill-session -t e2e-docs 2>/dev/null || true
tmux kill-session -t e2e-api 2>/dev/null || true

# 删除测试目录
echo "删除测试文件..."
rm -rf ~/tmp/codemux-e2e-test
rm -f ~/tmp/start-claude-sessions.sh
rm -f ~/tmp/cleanup-e2e-test.sh

# 验证清理结果
echo "验证清理结果..."
tmux list-sessions 2>/dev/null | grep e2e- || echo "✅ 所有测试会话已清理"
[ ! -d ~/tmp/codemux-e2e-test ] && echo "✅ 测试目录已删除"

echo "🎉 清理完成！"
EOF

chmod +x ~/tmp/cleanup-e2e-test.sh
~/tmp/cleanup-e2e-test.sh
```

### 7.2 验证总结检查清单

完成所有测试后，检查以下项目：

#### ✅ 核心功能验证
- [ ] **会话发现**: 能够发现多个 Claude Code 会话
- [ ] **命令路由**: 正确路由命令到指定会话
- [ ] **真实执行**: 实际执行命令并获得响应
- [ ] **响应捕获**: 正确捕获和处理 Claude Code 输出
- [ ] **时间测量**: 准确测量命令响应时间

#### ✅ 交互功能验证
- [ ] **状态查询**: `status` 命令显示所有会话
- [ ] **会话切换**: `switch to` 和中文命令正常工作
- [ ] **# 语法**: `#session command` 跨会话执行
- [ ] **模糊匹配**: 部分会话名匹配正常工作
- [ ] **错误处理**: 友好的错误信息和建议

#### ✅ 稳定性验证
- [ ] **并发处理**: 多个命令并发执行无问题
- [ ] **长时间运行**: 持续运行无内存泄漏或崩溃
- [ ] **错误恢复**: 临时错误后能正常恢复
- [ ] **会话监控**: 会话变化能及时发现

#### ✅ 性能验证
- [ ] **会话发现**: < 2秒
- [ ] **状态查询**: < 100ms
- [ ] **会话切换**: < 200ms
- [ ] **命令执行**: < 5秒 (简单命令)

## 测试脚本汇总

所有测试脚本都已创建在 `scripts/` 目录下：

1. `scripts/e2e_interactive_test.py` - 交互式命令路由测试
2. `scripts/stress_test.py` - 压力和并发测试
3. `scripts/longevity_test.py` - 长时间运行测试
4. `scripts/benchmark_test.py` - 性能基准测试

## 预期测试结果

如果 Codemux 工作正常，应该看到：

- ✅ **100% 基础功能测试通过**
- ✅ **95%+ 压力测试成功率**
- ✅ **0 错误的长时间运行**
- ✅ **所有性能指标达标**

这个端到端验证方案全面测试了 Codemux 的核心功能、稳定性和性能，确保在真实使用场景下能够稳定可靠地工作。
