"""
Integration tests for the tool-calling agent implementations.
These tests hit live LLM APIs — set OPENAI_API_KEY before running.
Run from the repository root:
    pytest tests/test_agents.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.envs import get_env
from src.agents.tool_calling_agent_langchain import ToolCallingAgentLangChain
from src.agents.tool_calling_agent_openai import ToolCallingAgentOpenAI

MODEL = "gpt-4o-mini"
PROVIDER = "openai"
USER_MODEL = "gpt-4o"


def _make_env(task_index: int):
    return get_env(
        "retail",
        user_strategy="llm",
        user_model=USER_MODEL,
        user_provider=PROVIDER,
        task_split="test",
        task_index=task_index,
    )


# ── LangChain agent ──────────────────────────────────────────────────────────

def test_langchain_agent_task_1():
    env = _make_env(1)
    result = ToolCallingAgentLangChain(env.tools_info, env.wiki, MODEL, PROVIDER).solve(env, task_index=1)
    assert result.reward >= 0.0 and len(result.messages) > 0


def test_langchain_agent_task_2():
    env = _make_env(2)
    result = ToolCallingAgentLangChain(env.tools_info, env.wiki, MODEL, PROVIDER).solve(env, task_index=2)
    assert result.reward >= 0.0 and len(result.messages) > 0


# ── OpenAI Agents SDK agent ──────────────────────────────────────────────────

def test_openai_agent_task_1():
    env = _make_env(1)
    result = ToolCallingAgentOpenAI(env.tools_info, env.wiki, MODEL, PROVIDER).solve(env, task_index=1)
    assert result.reward >= 0.0 and len(result.messages) > 0


def test_openai_agent_task_2():
    env = _make_env(2)
    result = ToolCallingAgentOpenAI(env.tools_info, env.wiki, MODEL, PROVIDER).solve(env, task_index=2)
    assert result.reward >= 0.0 and len(result.messages) > 0

