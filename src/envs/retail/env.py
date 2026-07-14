

from src.envs.base import Env
from src.envs.retail.data import load_data
from src.envs.retail.rules import RULES
from src.envs.retail.tools import ALL_TOOLS
from src.envs.retail.wiki import WIKI
from typing import Optional, Union
from src.envs.user import UserStrategy


class MockRetailDomainEnv(Env):
    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
    ):
        match task_split:
            case "test":
                from src.envs.retail.tasks_test import TASKS_TEST as tasks
            case "part3":
                from src.envs.retail.tasks_part3 import TASKS_PART3 as tasks
            case _:
                raise ValueError(f"Unknown task split: {task_split}")
        super().__init__(
            data_load_func=load_data,
            tools=ALL_TOOLS,
            tasks=tasks,
            wiki=WIKI,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
        )
        self.terminate_tools = ["transfer_to_human_agents"]
