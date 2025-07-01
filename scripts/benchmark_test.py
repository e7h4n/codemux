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
        {
            "name": "会话切换",
            "func": lambda: asyncio.run(router.handle_session_command("frontend", "")),
        },
        {
            "name": "简单命令",
            "func": lambda: asyncio.run(router.route_command("#frontend pwd")),
        },
    ]

    results = {}

    for benchmark in benchmarks:
        console.print(f"🏃 测试: {benchmark['name']}")
        times = []

        # 每个测试运行 5 次
        for i in range(5):
            start = time.time()
            try:
                result = benchmark["func"]()
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
            results[benchmark["name"]] = {
                "min": min(times),
                "max": max(times),
                "avg": statistics.mean(times),
                "median": statistics.median(times),
            }

    # 显示基准测试结果
    console.print("\n📊 [bold cyan]性能基准测试结果[/bold cyan]")
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
            f"{stats['median']:.1f}",
        )

    console.print(table)

    # 性能评估
    console.print("\n🎯 [bold green]性能评估[/bold green]")

    benchmarks_check = [
        ("会话发现", "avg", 2000, "会话发现应在 2s 内完成"),
        ("状态查询", "avg", 100, "状态查询应在 100ms 内完成"),
        ("会话切换", "avg", 200, "会话切换应在 200ms 内完成"),
        ("简单命令", "avg", 5000, "简单命令应在 5s 内完成"),
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
