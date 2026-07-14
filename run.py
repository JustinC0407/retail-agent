import argparse
from src.types import RunConfig
from src.run import run


def parse_args() -> RunConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-trials", type=int, default=1)
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="The model to use for the agent",
    )
    parser.add_argument(
        "--agent-strategy",
        type=str,
        default="tool-calling-langchain",
        choices=["tool-calling", "tool-calling-langchain", "tool-calling-openai"],
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="The sampling temperature for the action model",
    )
    parser.add_argument(
        "--task-split",
        type=str,
        default="part3",
        choices=["test", "part3"],
        help="The split of tasks to run",
    )
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=-1, help="Run all tasks if -1")
    parser.add_argument("--task-ids", type=int, nargs="+", help="(Optional) run only the tasks with the given IDs")
    parser.add_argument("--log-dir", type=str, default="results")
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=1,
        help="Number of tasks to run in parallel",
    )
    parser.add_argument("--seed", type=int, default=10)
    args = parser.parse_args()
    print(args)
    return RunConfig(
        model=args.model,
        num_trials=args.num_trials,
        agent_strategy=args.agent_strategy,
        temperature=args.temperature,
        task_split=args.task_split,
        start_index=args.start_index,
        end_index=args.end_index,
        task_ids=args.task_ids,
        log_dir=args.log_dir,
        max_concurrency=args.max_concurrency,
        seed=args.seed,
    )


def main():
    config = parse_args()
    run(config)


if __name__ == "__main__":
    main()
