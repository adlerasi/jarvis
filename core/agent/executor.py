"""Executor — Maps action types to tool/pyautogui/shell execution."""
from __future__ import annotations

import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any, Callable

from core.agent.task_graph import ActionType, TaskNode


class Executor:
    """Executes ACA task steps by dispatching to tools, pyautogui, or shell.

    ``tool_handlers`` — optional ``{tool_name: callable(tool_name, params) -> str}``
    ``shell_executor`` — optional ``(command: str) -> str``
    ``pyautogui_executor`` — optional ``(params: dict) -> str``

    Each execute_step() has a default 30-second timeout via ThreadPoolExecutor.
    """

    def __init__(
        self,
        tool_handlers: dict[str, Callable[[str, dict[str, Any]], str]] | None = None,
        shell_executor: Callable[[str], str] | None = None,
        pyautogui_executor: Callable[[dict[str, Any]], str] | None = None,
    ):
        self._tool_handlers: dict[str, Callable] = tool_handlers or {}
        self._shell_executor = shell_executor
        self._pyautogui_executor = pyautogui_executor
        self._step_timeout = 30

    def set_tool_handlers(self, handlers: dict[str, Callable]):
        self._tool_handlers = dict(handlers)

    def execute_step(self, node: TaskNode, _world_state: dict[str, Any] | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "success": False,
            "result": "",
            "error": None,
        }

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._run_action, node)
            try:
                output = future.result(timeout=self._step_timeout)
                result["result"] = output
                result["success"] = True
            except FuturesTimeout:
                traceback.print_exc()
                result["error"] = f"Zaman asimi ({self._step_timeout}s)"
                result["result"] = "Zaman asimi"
            except Exception as e:
                traceback.print_exc()
                result["error"] = str(e)
                result["result"] = f"Hata: {e}"

        return result

    def _run_action(self, node: TaskNode) -> str:
        if node.action_type == ActionType.TOOL:
            return self._execute_tool(node.tool_name, node.params)
        elif node.action_type == ActionType.SHELL:
            return self._execute_shell(node.params)
        elif node.action_type == ActionType.INPUT:
            return self._execute_pyautogui(node.params)
        elif node.action_type == ActionType.OBSERVE:
            return "Gozlendi."
        elif node.action_type == ActionType.WAIT:
            duration = float(node.params.get("seconds", 1))
            time.sleep(duration)
            return f"{duration}s beklendi."
        else:
            raise ValueError(f"Bilinmeyen aksiyon tipi: {node.action_type}")

    def execute_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        return self._execute_tool(tool_name, params)

    def _execute_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        handler = self._tool_handlers.get(tool_name)
        if handler:
            try:
                return handler(tool_name, params)
            except Exception as e:
                traceback.print_exc()
                return f"Arac hatasi ({tool_name}): {e}"
        return f"Arac bulunamadi: {tool_name}"

    def execute_pyautogui(self, params: dict[str, Any]) -> str:
        return self._execute_pyautogui(params)

    def _execute_pyautogui(self, params: dict[str, Any]) -> str:
        if self._pyautogui_executor is not None:
            try:
                return self._pyautogui_executor(params)
            except Exception as e:
                traceback.print_exc()
                return f"pyautogui hatasi: {e}"

        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.3

            action = params.get("action", "type")
            text = params.get("text", "")
            keys = params.get("keys", "")
            x = params.get("x")
            y = params.get("y")
            button = params.get("button", "left")
            clicks = params.get("clicks", 1)

            if action == "click":
                if x is not None and y is not None:
                    pyautogui.click(x, y, clicks=clicks, button=button)
                else:
                    pyautogui.click(clicks=clicks, button=button)
                return "Tiklama basarili."
            elif action == "double_click":
                if x is not None and y is not None:
                    pyautogui.doubleClick(x, y, button=button)
                else:
                    pyautogui.doubleClick(button=button)
                return "Cift tik basarili."
            elif action == "right_click":
                if x is not None and y is not None:
                    pyautogui.rightClick(x, y)
                else:
                    pyautogui.rightClick()
                return "Sag tik basarili."
            elif action == "type":
                pyautogui.typewrite(text or keys, interval=0.05)
                return "Yazma basarili."
            elif action == "key":
                pyautogui.press(keys)
                return f"Tus basildi: {keys}"
            elif action == "hotkey":
                combo = params.get("combo", [])
                if combo:
                    pyautogui.hotkey(*combo)
                    return f"Kisa yol: {'+'.join(combo)}"
                return "Kisa yol parametresi eksik."
            elif action == "drag":
                target_x = params.get("target_x", 0)
                target_y = params.get("target_y", 0)
                duration = params.get("duration", 0.5)
                if x is not None and y is not None:
                    pyautogui.drag(target_x - x, target_y - y, duration=duration)
                else:
                    pyautogui.drag(target_x, target_y, duration=duration)
                return "Surukleme basarili."
            elif action == "scroll":
                amount = params.get("amount", -3)
                pyautogui.scroll(amount)
                return "Kaydirma basarili."
            elif action == "move":
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y, duration=params.get("duration", 0.3))
                    return "Fare tasindi."
                return "move icin x,y gerekli."
            return f"Bilinmeyen pyautogui aksiyonu: {action}"
        except ImportError:
            return "pyautogui modulu yuklu degil."
        except Exception as e:
            traceback.print_exc()
            return f"pyautogui hatasi: {e}"

    def _execute_shell(self, params: dict[str, Any]) -> str:
        command = params.get("command", "")
        if not command:
            return "Komut belirtilmedi."
        if self._shell_executor is not None:
            try:
                return self._shell_executor(command)
            except Exception as e:
                traceback.print_exc()
                return f"Shell hatasi: {e}"
        return "Shell executor yapilandirilmamis."
