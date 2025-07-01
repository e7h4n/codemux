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
        "#docs cat README.md",
    ]

    console.print(f"📋 准备执行 {len(commands)} 个并发命令...")

    # 记录开始时间
    start_time = time.time()

    # 创建并发任务
    tasks = []
    for i, cmd in enumerate(commands):
        task = asyncio.create_task(
            router.route_command(cmd), name=f"cmd_{i}_{cmd[:20]}"
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
    console.print("\n📊 [bold cyan]压力测试结果[/bold cyan]")
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
