# Retail Customer-Service Tool-Calling Agent

A [τ-bench](https://arxiv.org/abs/2406.12045)-style retail customer-support agent. The agent
holds multi-turn conversations with a customer and operates over an in-memory mock database of
**users**, **orders**, and **products**, using a fixed set of tools to authenticate the customer,
look things up, and make changes to orders. Its behavior is governed by a written support policy
in [`src/envs/retail/wiki.md`](src/envs/retail/wiki.md) — the agent must confirm the customer's
identity, get explicit authorization before mutating the database, and follow the return/exchange
rules laid out there.

## How it works

- **Environment** (`src/envs/retail/`) — a mock retail backend. Orders, products, and users live in
  JSON files under `src/envs/retail/data/` and are loaded into memory at the start of each task, so
  every run starts from a clean, deterministic state.
- **Tools** (`src/envs/retail/tools/`) — 16 tools the agent can call:
  - Authentication / lookup: `find_user_id_by_email`, `find_user_id_by_name_zip`,
    `get_user_details`, `get_order_details`, `get_product_details`, `list_all_product_types`
  - Order changes: `cancel_pending_order`, `modify_pending_order_items`,
    `modify_pending_order_payment`, `modify_pending_order_address`,
    `return_delivered_order_items`, `exchange_delivered_order_items`, `modify_user_address`
  - Utility / control: `calculate`, `think`, `transfer_to_human_agents`
- **Simulated user** (`src/envs/user.py`) — an LLM plays the customer, driving the conversation from
  a task instruction so full multi-turn dialogues can be run automatically.
- **Evaluation** — each task specifies the expected database mutations and required outputs. After a
  conversation, the environment compares the final state against the expectation to produce a reward.
  Running each task multiple times yields a **Pass^k** metric (the fraction of tasks solved correctly
  in all _k_ independent trials), which rewards reliability, not just occasional success.

### Two interchangeable agent implementations

The same agent logic is provided on two frameworks, selectable at run time via
`run.py --agent-strategy`:

| `--agent-strategy`        | Implementation                                        |
| ------------------------- | ----------------------------------------------------- |
| `tool-calling-langchain`  | LangGraph `create_react_agent` (LangChain)            |
| `tool-calling-openai`     | OpenAI Agents SDK (`Agent` + `Runner`)                |
| `tool-calling`            | Baseline direct tool-calling loop (via LiteLLM)       |

## Setup

```bash
pip install -r requirements.txt
```

Set your OpenAI API key as an environment variable (placeholder shown — use your own key, and never
commit a real key to the repository):

```bash
export OPENAI_API_KEY="your_key_here"
```

## Running evaluations

Run the full task split with the LangGraph agent:

```bash
python run.py --agent-strategy tool-calling-langchain --model gpt-4o-mini
```

Or with the OpenAI Agents SDK implementation:

```bash
python run.py --agent-strategy tool-calling-openai --model gpt-4o-mini
```

Useful flags:

- `--num-trials N` — run each task _N_ times (needed for a Pass^k > 1 estimate)
- `--task-split {test,part3}` — which set of tasks to evaluate
- `--task-ids 0 7 8` — run only specific tasks
- `--start-index` / `--end-index` — run a contiguous range of tasks
- `--temperature` — sampling temperature for the agent model (default `0.0`)
- `--max-concurrency` — number of tasks to run in parallel
- `--log-dir` — where trajectory JSON files are written (default `results/`)

Run `python run.py --help` for the full list.

## Tests

```bash
pytest tests/ -v
```

`tests/test_tools.py` sanity-checks the tool implementations against fixed mock data;
`tests/test_agents.py` runs the agents end-to-end and requires a valid `OPENAI_API_KEY`.

## Sample results

The [`results/`](results/) directory holds sample evaluation trajectories (JSON) from prior runs of
the LangGraph and OpenAI Agents SDK implementations on `gpt-4o-mini`, kept as a showcase of the
output format.
