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
            session["name"], session["dirname"], session["current_path"] or "unknown"
        )

    console.print(table)
    console.print()

    # 测试用例
    test_cases = [
        {"name": "状态查询", "command": "status", "description": "查看所有会话状态"},
        {
            "name": "会话切换 - frontend",
            "command": "switch to frontend",
            "description": "切换到前端项目会话",
        },
        {
            "name": "中文会话切换",
            "command": "切换到 backend",
            "description": "使用中文切换到后端会话",
        },
        {
            "name": "# 语法 - 简单命令",
            "command": "#docs pwd",
            "description": "在文档会话执行 pwd 命令",
        },
        {
            "name": "# 语法 - 文件操作",
            "command": "#frontend ls -la",
            "description": "在前端会话列出文件",
        },
        {
            "name": "当前会话命令",
            "command": "echo 'Hello from current session'",
            "description": "在当前活跃会话执行命令",
        },
        {
            "name": "模糊匹配",
            "command": "switch to api",
            "description": "模糊匹配切换到 API 会话",
        },
        {
            "name": "复杂命令",
            "command": "#backend cat README.md",
            "description": "在后端会话读取 README 文件",
        },
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
            result = await router.route_command(test_case["command"])
            end_time = asyncio.get_event_loop().time()

            # 显示结果
            console.print(f"[green]✅ 成功[/green] (⏱️ {end_time - start_time:.1f}s)")
            console.print(
                f"[dim]响应:[/dim] {result[:100]}{'...' if len(result) > 100 else ''}"
            )
            passed += 1

        except Exception as e:
            console.print(f"[red]❌ 失败[/red]: {str(e)}")

        console.print()

        # 短暂延迟避免过快执行
        if i < total:
            await asyncio.sleep(1)

    # 测试总结
    console.print("3️⃣ [bold green]测试完成[/bold green]")
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
