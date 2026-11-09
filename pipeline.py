import time
from typing import Callable, Optional

from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# Keys yahi rahengi CLI aur Streamlit dono mein
STEP_ORDER = ["search", "reader", "writer", "critic"]

SEARCH_CHARS_FOR_READER = 2000


def run_research_pipeline(
    topic: str,
    on_step: Optional[Callable[[str], None]] = None,
    on_result: Optional[Callable[[str, str], None]] = None,
) -> dict:
    """
    Research pipeline: search -> reader -> writer -> critic.

    on_step(step)           : har step shuru hone se pehle call hota hai
    on_result(step, output) : har step complete hone ke baad call hota hai

    Returns dict with keys: search, reader, writer, critic (jo complete hue),
    plus optionally:
      "error"    : {"step": ..., "message": ...} agar pipeline beech mein fail hui
      "warnings" : list[str] non-fatal issues (jaise scraping fail)
    """
    state: dict = {}
    warnings: list[str] = []

    def start(step: str):
        if on_step:
            on_step(step)

    def finish(step: str, output: str):
        state[step] = output
        if on_result:
            on_result(step, output)

    current = None
    try:
        # Step 1: Search
        current = "search"
        start(current)
        search_agent = build_search_agent()
        sr = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        finish(current, sr["messages"][-1].content)

        # Step 2: Reader (fail ho to bhi aage badho, search results se report ban jayegi)
        current = "reader"
        start(current)
        try:
            reader_agent = build_reader_agent()
            rr = reader_agent.invoke({
                "messages": [("user",
                    f"Based on the following search results about '{topic}', "
                    f"pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{state['search'][:SEARCH_CHARS_FOR_READER]}"
                )]
            })
            finish(current, rr["messages"][-1].content)
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            warnings.append(f"Reader step fail hua, report sirf search results pe based hai ({msg})")
            finish(current, f"[Scraping failed: {msg}]")

        # Step 3: Writer
        current = "writer"
        start(current)
        research_combined = (
            f"SEARCH RESULTS:\n{state['search']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['reader']}"
        )
        finish(current, writer_chain.invoke({
            "topic": topic,
            "research": research_combined,
        }))

        # Step 4: Critic
        current = "critic"
        start(current)
        finish(current, critic_chain.invoke({"report": state["writer"]}))

    except Exception as e:
        state["error"] = {"step": current, "message": f"{type(e).__name__}: {e}"}

    if warnings:
        state["warnings"] = warnings
    return state


# ── CLI ───────────────────────────────────────────────────────────────────────
STEP_LABELS = {
    "search": "Step 1 - Search agent is working ...",
    "reader": "Step 2 - Reader agent is scraping top resources ...",
    "writer": "Step 3 - Writer is drafting the report ...",
    "critic": "Step 4 - Critic is reviewing the report ...",
}


def _cli_on_step(step: str):
    print("\n" + "=" * 50)
    print(STEP_LABELS[step])
    print("=" * 50)


def _cli_on_result(step: str, output: str):
    print(f"\n[{step.upper()} OUTPUT]\n{output}")


if __name__ == "__main__":
    topic = input("\nEnter a research topic: ").strip()
    if not topic:
        print("Topic khali hai. Dobara try kar.")
        raise SystemExit(1)

    result = run_research_pipeline(topic, on_step=_cli_on_step, on_result=_cli_on_result)

    for w in result.get("warnings", []):
        print(f"\n[WARNING] {w}")

    if "error" in result:
        err = result["error"]
        print(f"\n[ERROR] '{err['step']}' step fail ho gaya: {err['message']}")

    if "writer" in result:
        filename = f"research_report_{int(time.time())}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result["writer"])
        print(f"\nReport saved: {filename}")