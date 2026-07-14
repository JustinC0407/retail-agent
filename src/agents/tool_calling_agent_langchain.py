"""
Tool-Calling Agent using LangGraph (LangChain).

This module implements a multi-turn conversational agent that uses Langchain's agent to handle tool calls. The agent receives a task from the
environment, invokes tools as needed, and responds to the user over multiple turns.
"""
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import Field, create_model

from src.agents.base import Agent
from src.envs.base import Env
from src.types import Action, RESPOND_ACTION_NAME, SolveResult


def _make_tool_input_schema(parameters: Dict[str, Any]):
    """Dynamically build a Pydantic model from an OpenAI-style JSON-schema parameters dict."""
    type_map = {
        "string": str,
        "number": float,
        "integer": int,
        "boolean": bool,
        "array": List[Any],
    }
    fields: Dict[str, Any] = {}
    properties = parameters.get("properties", {})
    required = set(parameters.get("required", []))
    for prop_name, prop_schema in properties.items():
        py_type = type_map.get(prop_schema.get("type", "string"), Any)
        description = prop_schema.get("description", "")
        if prop_name in required:
            fields[prop_name] = (py_type, Field(description=description))
        else:
            fields[prop_name] = (Optional[py_type], Field(default=None, description=description))
    return create_model("ToolInput", **fields)


def tools_info_to_langchain_tools(
    tools_info: List[Dict[str, Any]],
    env: Env,
    done_callback: Callable[[float], None],
) -> List[StructuredTool]:
    lc_tools = []
    for tool_info in tools_info:
        func_info = tool_info["function"]
        tool_name = func_info["name"]
        description = func_info.get("description", "")
        parameters = func_info.get("parameters", {})
        input_schema = _make_tool_input_schema(parameters)

        def make_run_tool(name):
            def run_tool(**kwargs):
                action_response = ""
                # Construct an Action with the tool name and kwargs and execute
                # it via env.step(). If the environment signals completion,
                # invoke done_callback with the reward.
                action = Action(name=name, kwargs=kwargs)
                env_response = env.step(action)
                action_response = env_response.observation
                if env_response.done:
                    done_callback(env_response.reward)
                return action_response

            return run_tool

        lc_tools.append(StructuredTool.from_function(
            func=make_run_tool(tool_name),
            name=tool_name,
            description=description,
            args_schema=input_schema,
        ))
    return lc_tools


class ToolCallingAgentLangChain(Agent):
    def __init__(
        self,
        tools_info: List[Dict[str, Any]],
        wiki: str,
        model: str,
        provider: str,
        temperature: float = 0.0,
    ):
        self.tools_info = tools_info
        self.wiki = wiki
        self.model = model
        self.provider = provider
        self.temperature = temperature

    def solve(
        self, env: Env, task_index: Optional[int] = None, max_num_steps: int = 30
    ) -> SolveResult:
        env_reset_res = env.reset(task_index=task_index)
        initial_observation = env_reset_res.observation
        info = env_reset_res.info.model_dump()

        state = {"reward": 0.0, "done": False}

        def done_callback(reward: float):
            state["done"] = True
            state["reward"] = reward

        lc_tools = tools_info_to_langchain_tools(self.tools_info, env, done_callback)

        # Instantiate a ChatOpenAI LLM and build the ReAct agent graph.
        llm = ChatOpenAI(model=self.model, temperature=self.temperature)
        graph = create_react_agent(llm, lc_tools)

        # Outer loop: one iteration = one agent turn (graph.invoke handles internal
        # tool calls). After each turn we call env.step(RESPOND) to get the user's
        # next message and feed the updated history back for the next turn.
        messages = [
            SystemMessage(content=self.wiki),
            HumanMessage(content=initial_observation),
        ]
        result = None
        for _ in range(max_num_steps):
            # Invoke the graph with the current messages list and take the
            # agent's final natural language response from the last message.
            result = graph.invoke(
                {"messages": messages},
                config={"recursion_limit": max_num_steps * 2 + 4},
            )
            agent_text = result["messages"][-1].content

            if state["done"]:
                break

            action = Action(name=RESPOND_ACTION_NAME, kwargs={"content": agent_text})
            env_response = env.step(action)
            state["reward"] = env_response.reward
            info = {**info, **env_response.info.model_dump()}

            if env_response.done:
                state["done"] = True
                break

            # Append user's reply to history for next turn
            messages = result["messages"] + [HumanMessage(content=env_response.observation)]

        if not state["done"]:
            reward_result = env.calculate_reward()
            state["reward"] = reward_result.reward

        serialized_messages = []
        for msg in (result["messages"] if result else []):
            if hasattr(msg, "model_dump"):
                serialized_messages.append(msg.model_dump())
            else:
                serialized_messages.append({"role": "unknown", "content": str(msg)})

        return SolveResult(
            reward=state["reward"],
            messages=serialized_messages,
            info=info,
            total_cost=None,
        )
