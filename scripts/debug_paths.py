#!/usr/bin/env python3
"""调试路径检测."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.tmux_controller import TmuxController


def debug_paths():
    """调试路径检测."""
    print("🔍 调试路径检测...\n")

    controller = TmuxController()

    # 检查所有e2e会话的路径信息
    for session in controller.server.sessions:
        if session.name.startswith("e2e-"):
            print(f"会话: {session.name}")
            for window in session.windows:
                for pane in window.panes:
                    if controller._is_running_claude(pane):
                        print(f"  Pane ID: {pane.id}")

                        # 尝试不同的路径获取方法
                        try:
                            # 方法1: current_path 属性
                            current_path = getattr(pane, "current_path", None)
                            print(f"  current_path 属性: {current_path}")
                        except Exception as e:
                            print(f"  current_path 错误: {e}")

                        try:
                            # 方法2: tmux命令获取
                            result = pane.cmd("display", "-p", "#{pane_current_path}")
                            if result and result.stdout:
                                path = str(result.stdout[0]) if result.stdout else ""
                                print(f"  pane_current_path: {path}")
                        except Exception as e:
                            print(f"  pane_current_path 错误: {e}")

                        try:
                            # 方法3: 从会话获取路径
                            session_result = session.cmd(
                                "display", "-p", "#{session_path}"
                            )
                            if session_result and session_result.stdout:
                                spath = (
                                    str(session_result.stdout[0])
                                    if session_result.stdout
                                    else ""
                                )
                                print(f"  session_path: {spath}")
                        except Exception as e:
                            print(f"  session_path 错误: {e}")

                        print()


if __name__ == "__main__":
    debug_paths()
