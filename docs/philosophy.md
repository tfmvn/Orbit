# Philosophy

Orbit is infrastructure for running AI agents, not a chat interface. That
framing drives a few concrete decisions:

## Runtime, not request/response

A chatbot's unit of work is a conversational turn. Orbit's unit of work is a
job that can run for minutes, hours, or days, survive process restarts, and
be inspected or cancelled mid-flight. This is why the backend is async-first
from the start, and why the `Runtime` interface talks about starting,
cancelling, and checking the status of jobs rather than "sending a message."

## Local-first

Orbit should run entirely on a developer's machine with nothing more than
Python, Node, and (optionally) Docker. Any external, cloud-hosted dependency
— a hosted model API, a managed vector database — should be an optional
`ModelProvider`/`MemoryProvider` implementation, never a requirement to boot
the system.

## Boring foundations, interesting agents

The complexity in Orbit should live in the agent logic — planning
strategies, memory architectures, tool sandboxing — not in the scaffolding
around it. That's why this foundation phase deliberately keeps things
simple: one settings object, one logging setup, dependency injection wired
in one place, versioned routes. None of it is exciting, and that's the
point — it should be easy to reason about years from now, long after the
interesting parts have been built on top of it.

## Interfaces are commitments, not paperwork

Defining `Runtime`, `Planner`, `ToolProvider`, `MemoryProvider`, and
`ModelProvider` as empty interfaces before writing any agent logic is a
deliberate constraint: it forces the eventual implementations to fit a
contract that was designed with the HTTP layer and DI wiring in mind, rather
than being retrofitted after the fact. If an interface turns out to be
wrong once real implementation starts, it should be changed deliberately and
explicitly — not worked around.

## Extend by adding, not by restructuring

The `packages/` directory already contains a slot for every subsystem Orbit
is known to need (`runtime`, `planner`, `tools`, `memory`, `providers`).
Adding one of these should mean writing code inside its existing folder and
wiring it into `core/dependencies.py` — never renaming or moving files that
already exist. A repository that has to be restructured every time a major
feature is added is a sign the foundation wasn't designed far enough ahead;
this phase tries to avoid that trap without overbuilding for needs that
aren't concrete yet.
