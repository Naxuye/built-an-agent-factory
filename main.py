# -*- coding: utf-8 -*-
# filename: main.py
import asyncio
import os
import sys
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)

    base_key = os.getenv("DEEPSEEK_API_KEY")
    if base_key:
        if not os.getenv("DEEPSEEK_REASONER_API_KEY"):
            os.environ["DEEPSEEK_REASONER_API_KEY"] = base_key
        if not os.getenv("DEEPSEEK_CHAT_API_KEY"):
            os.environ["DEEPSEEK_CHAT_API_KEY"] = base_key
        print("[System] DeepSeek API 已就绪")

    if not os.getenv("DEEPSEEK_REASONER_API_KEY"):
        print("[System] 警告：DeepSeek API Key 未配置")
else:
    print(f"[Fatal] 未找到配置文件：{env_path}")

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def print_ignition_info(target_dir):
    main_py_path = os.path.join(target_dir, "main.py")

    info = Text()
    info.append(f"项目已保存\n", style="bold green")
    info.append(f"路径: {target_dir}\n", style="white")
    info.append(f"运行: ", style="bold white")

    if os.path.exists(main_py_path):
        display_cmd = f"python \"{main_py_path}\""
    else:
        display_cmd = f"cd /d \"{target_dir}\""

    info.append(display_cmd, style="bold green underline")

    console.print(Panel(info, title="[bold green]项目已生成[/bold green]", border_style="green", expand=False))

async def main():
    try:
        from langgraph_workflow import naxuye_app
    except ImportError as e:
        console.print(f"[bold red]核心逻辑加载失败: {e}[/bold red]")
        return

    console.print(Panel.fit(
        "[bold]NAXUYE-AGENT V5.5[/bold]\n"
        "[dim]DeepSeek | Zhipu | Aliyun[/dim]",
        border_style="blue"
    ))

    while True:
        target = console.input("\n[bold]输入建设目标 (quit 退出): [/bold]")
        if target.lower() == 'quit':
            break

        initial_state = {
            "input": target,
            "chat_history": [],
            "plan": {},
            "intelligence": "",
            "active_node": {},
            "draft": [],
            "passed_slots": [],
            "audit_report": {"score": 0, "advice": "", "error_type": "NONE"},
            "retry_count": 0,
            "error_log": [],
            "final_path": "",
            "final_decision": "",
            "target_components": [],
            "batch_retry_count": 0,
            "agent_name": "",
            "input_schema": {},
            "trigger_keywords": [],
            "test_cases": []
        }

        console.print("\n[dim]正在处理...[/dim]")

        final_save_path = None

        try:
            async for output in naxuye_app.astream(initial_state):
                for node_name, state_update in output.items():
                    console.print(f"[bold]>>>[/bold] {node_name} 完成")

                    if node_name == "planner":
                        plan = state_update.get("plan", {})
                        if plan.get("error"):
                            console.print(f"    ┗ [red]Planner 错误: {plan['error']}[/red]")

                    if node_name == "reviewer":
                        report = state_update.get("audit_report", {})
                        score = report.get("score", 0)
                        retry_count = state_update.get("retry_count", 0)
                        error_type = report.get("error_type", "")

                        if error_type in ["SAFETY_INTERCEPT", "PLANNER_FAILURE", "CRITICAL_FAILURE"]:
                            status = f"[bold white on red] {error_type} [/bold white on red]"
                        else:
                            status = "[bold white on green] PASS [/bold white on green]" if score >= 80 else "[bold white on red] REJECT [/bold white on red]"

                        console.print(f"    ┗ {status} 得分: {score} | 重试: {retry_count}")

                    if node_name == "smoke_test":
                        report = state_update.get("audit_report", {})
                        if report.get("error_type") == "SMOKE_TEST_FAILURE":
                            console.print(f"    ┗ [bold white on red] SMOKE TEST FAILED [/bold white on red] {report.get('summary', '')}")
                        else:
                            console.print(f"    ┗ [bold white on green] SMOKE TEST PASSED [/bold white on green]")

                    if node_name == "logistic":
                        report_text = state_update.get("final_decision", "")
                        console.print(Panel(report_text, border_style="green"))
                        final_save_path = state_update.get("final_path")

        except Exception as e:
            console.print(f"[bold red]执行异常: {e}[/bold red]")

        if not final_save_path:
            try:
                factory_root = os.getenv("NAXUYE_WORKSPACE", os.path.join(os.path.expanduser("~"), "naxuye-workspace", "agent_factory"))
                if os.path.exists(factory_root):
                    dirs = [os.path.join(factory_root, d) for d in os.listdir(factory_root)
                            if os.path.isdir(os.path.join(factory_root, d)) and "_SAFE" in d]
                    if dirs:
                        final_save_path = max(dirs, key=os.path.getmtime)
                        console.print(f"[dim]路径: {final_save_path}[/dim]")
            except Exception as path_err:
                console.print(f"[dim red]路径查找失败: {path_err}[/dim red]")

        if final_save_path:
            print_ignition_info(final_save_path)
        else:
            console.print("[bold red]警告：项目未能成功保存。[/bold red]")

    console.print("[dim]已退出。[/dim]")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[dim]已中断。[/dim]")
    except Exception as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        input("\n按任意键退出...")
