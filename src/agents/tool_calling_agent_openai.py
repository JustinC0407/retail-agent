"""
Tool-Calling Agent using the OpenAI Agents SDK.

This module implements a multi-turn conversational agent that uses the OpenAI
Agents SDK to handle tool calls. The agent receives a task from the environment,
invokes tools as needed, and responds to the user over multiple turns.
"""
import json
from typing import Any, Callable, Dict, List, Optional

from agents import Agent as OpenAIAgent, Runner
from agents.tool import FunctionTool
import litellm

from src.agents.base import Agent
from src.envs.base import Env
from src.types import Action, RESPOND_ACTION_NAME, SolveResult


def tools_info_to_oai_tools(
    tools_info: List[Dict[str, Any]],
    env: Env,
    done_callback: Callable[[float], None],
) -> List[FunctionTool]:
    oai_tools = []
    for tool_info in tools_info:
        func_info = tool_info["function"]
        tool_name = func_info["name"]
        description = func_info.get("description", "")
        parameters = func_info.get("parameters", {})

        def make_handler(name):
            async def on_invoke_tool(ctx, args_json: str) -> str:
                action_response = ""
                # Construct an Action with the tool name and kwargs and execute
                # it via env.step(). If the environment signals completion,
                # invoke done_callback with the reward.
                kwargs = json.loads(args_json)
                action = Action(name=name, kwargs=kwargs)
                env_response = env.step(action)
                action_response = env_response.observation
                if env_response.done:
                    done_callback(env_response.reward)
                return action_response
            
            return on_invoke_tool

        oai_tools.append(FunctionTool(
            name=tool_name,
            description=description,
            params_json_schema=parameters,
            on_invoke_tool=make_handler(tool_name),
        ))
    return oai_tools


class ToolCallingAgentOpenAI(Agent):
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
        total_cost = 0.0
        env_reset_res = env.reset(task_index=task_index)
        obs = env_reset_res.observation
        info = env_reset_res.info.model_dump()
        pricing = litellm.model_cost.get(self.model, {})
        input_rate = pricing.get("input_cost_per_token", 0.0)
        output_rate = pricing.get("output_cost_per_token", 0.0)


        state = {"reward": 0.0, "done": False}

        def done_callback(reward: float):
            state["done"] = True
            state["reward"] = reward

        openai_agent_tools = tools_info_to_oai_tools(self.tools_info, env, done_callback)
        # Instantiate the OpenAI Agents SDK agent.
        openai_agent = OpenAIAgent(
            name="Retail Customer Service Agent",
            instructions=self.wiki,
            model=self.model,
            tools=openai_agent_tools,
        )

        input_messages = [{"role": "user", "content": obs}]  # initial user's request
        for _ in range(max_num_steps):
            if state["done"]:
                break
            
            # Run the agent on the current input messages, capture its final
            # natural language response, and accumulate the token cost.
            result = Runner.run_sync(
                openai_agent,
                input_messages,
                max_turns=max_num_steps,
            )
            agent_text = result.final_output

            for raw_response in getattr(result, "raw_responses", []):
                usage = getattr(raw_response, "usage", None)
                if usage is None:
                    continue

                input_tokens = (
                    getattr(usage, "input_tokens", None)
                    or getattr(usage, "prompt_tokens", None)
                    or 0
                )
                output_tokens = (
                    getattr(usage, "output_tokens", None)
                    or getattr(usage, "completion_tokens", None)
                    or 0
                )
                total_cost += input_tokens * input_rate + output_tokens * output_rate

            if total_cost == 0:
                total_cost = 1e-12

            action = Action(name=RESPOND_ACTION_NAME, kwargs={"content": agent_text})
            env_response = env.step(action)
            state["reward"] = env_response.reward
            info = {**info, **env_response.info.model_dump()}

            if env_response.done:
                state["done"] = True
                break

            # Append user's reply to history for next turn
            input_messages = result.to_input_list() + [
                {"role": "user", "content": env_response.observation}
            ]

        if not state["done"]:
            reward_result = env.calculate_reward()
            state["reward"] = reward_result.reward

        messages = []
        for item in result.to_input_list():
            if isinstance(item, dict):
                messages.append(item)
            else:
                messages.append({"role": "unknown", "content": str(item)})

        return SolveResult(
            reward=state["reward"],
            messages=messages,
            info=info,
            total_cost=total_cost,
        )
