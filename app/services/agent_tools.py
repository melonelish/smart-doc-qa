"""
Agent Tools — calculator, web_search, and function calling schemas.

Used by qa_service.py to enable LLM-driven tool selection:
    LLM decides → execute tool → feed result back → LLM generates answer.
"""

import logging
import math
import operator
import re
import ast
import sys
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
#  Function Calling JSON Schema
# ═══════════════════════════════════════════════════════════

AGENT_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "精确计算数值表达式。支持四则运算、幂运算、百分比、括号等。例如: '375/1250*100', '(336-218)/218*100', '520+680+820'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式字符串，如 '1250 - 875' 或 '(1920-1250)/1250*100'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "联网搜索补全信息。当文档中找不到相关数据时，用此工具搜索互联网获取最新资料。例如搜索行业报告、公司信息、公开数据等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大返回结果数，默认5",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# ═══════════════════════════════════════════════════════════
#  Tool Implementations
# ═══════════════════════════════════════════════════════════

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "abs": abs,
    "round": round,
    "max": max,
    "min": min,
    "sum": sum,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _SAFE_OPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
        return _SAFE_OPS[op_type](_safe_eval(node.operand))
    raise ValueError(f"不支持的表达式节点: {type(node).__name__}")


def calculator(expression: str) -> str:
    try:
        expr_str = expression.strip()

        expr_str = expr_str.replace("×", "*").replace("÷", "/")
        expr_str = expr_str.replace("％", "%").replace("%", "/100")
        expr_str = expr_str.replace(",", "")

        expr_str = re.sub(r'(?<=\d)([万亿])', r'*10**\1', expr_str)

        tree = ast.parse(expr_str, mode="eval")
        result = _safe_eval(tree)

        if result == int(result) and abs(result) < 1e15:
            return str(int(result))
        return f"{result:.6g}"
    except ZeroDivisionError:
        return "错误: 除数不能为零"
    except (SyntaxError, ValueError) as e:
        return f"表达式错误: {e}"
    except Exception as e:
        return f"计算失败: {e}"


def web_search(query: str, max_results: int = 5) -> str:
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"未找到与'{query}'相关的搜索结果。"

        parts = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            body = r.get("body", "无摘要")
            href = r.get("href", "")
            parts.append(f"[{i}] {title}\n{body}\n来源: {href}")

        return "\n\n".join(parts)
    except ImportError:
        return "错误: duckduckgo_search 未安装，请运行 pip install duckduckgo_search"
    except Exception as e:
        logger.warning(f"[agent] web_search failed: {e}")
        return f"搜索失败: {e}"


# ═══════════════════════════════════════════════════════════
#  Tool Dispatcher
# ═══════════════════════════════════════════════════════════

_TOOL_MAP = {
    "calculator": calculator,
    "web_search": web_search,
}


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    fn = _TOOL_MAP.get(name)
    if fn is None:
        return f"错误: 未知工具 '{name}'"

    try:
        return fn(**arguments)
    except TypeError as e:
        return f"参数错误: {e}"
    except Exception as e:
        logger.warning(f"[agent] Tool '{name}' execution failed: {e}")
        return f"工具执行失败: {e}"
