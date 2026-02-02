from browser_use import Agent, Browser, BrowserProfile, ChatBrowserUse, ChatOpenAI
from browser_use.llm.deepseek.chat import ChatDeepSeek
from dotenv import load_dotenv
import asyncio
import argparse
import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).parent
RESUME_PATH = BASE_DIR / "resume" / "Artem_Tolochkov_Software-Engineer_2025.pdf"
PROBLEMATIC_SITES_PATH = BASE_DIR / "problematic_sites.txt"


load_dotenv()
if os.getenv("OPENAI_API_KEY") is None and os.getenv("OPEN_AI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_AI_API_KEY")


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "deepseek":
        return ChatDeepSeek(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
        )
    if provider in ("browser_use", "browser-use", "browseruse"):
        return ChatBrowserUse()
    model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    return ChatOpenAI(model=model)


def get_browser():
    profile_dir = BASE_DIR / "browser_profile"
    profile = BrowserProfile(
        is_local=True,
        headless=False,
        user_data_dir=profile_dir,
        window_size={"width": 1366, "height": 768},
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"),
        highlight_elements=False,
        dom_highlight_elements=False,
        args=[
            "--disable-quic",
            "--dns-prefetch-disable",
            "--disable-variations",
            "--disable-features=PreconnectToOrigins,PrefetchPrivacyChanges",
            "--disable-features=DnsOverHttps,AsyncDns",
            "--disable-features=VizDisplayCompositor",
        ],
    )
    return Browser(browser_profile=profile)


BLACKLIST = "Greenhouse"

PROMPT_PREFIX = (
    "open 'linkedin.com/jobs/search/?f_WT=2&geoId=92000000&keywords=frontend developer&start=500' "
    "apply to everything including external sites. I MEAN EVERYTHING EVEN IF IT IS NOT REMOTE OR NOT A JOB. "
    f"When a resume/CV is required, upload this file: {RESUME_PATH}. If there's a too messy input files with shadow DOM or iframe or something, just drop the vacancy and move on."
    f"When you drop a vacancy because of captcha, messy/shadow DOM/iframe inputs, or being stuck for many steps, append a new line with the company name to this file: {PROBLEMATIC_SITES_PATH}. One entry per line, do not overwrite existing content."
    "and remember to never visit that company's site again"
    "do not stop. Ever. Apply to all jobs endlessly."
    "unsure about an answer or don't know? make up an answer that they want to hear"
    "if captcha appears or you're stuck for many steps, leave the page and move on"
    "skip anything that mentions india, lakhs or rupees"
    "apply to all jobs you can find using the following instructions:\n\n"
)


TOKENS_PROMPT = (
    "1 open github.com/signup?source=login and create GitHub account with email johncash23871+ITERATOR@gmail.com where ITERATOR is from 2 to infinity. Password is a random string. Complete aiduo challenge if prompted\n\n"
    "2 open mail.google.com and copy verification code from GitHub to the previous tab\n\n"
    "3 open cloud.browser-use.com and signup with GitHub\n\n"
    "4 open cloud.browser-use.com/settings?tab=api-keys and create a new api key, writing it down in a txt file"
)


def get_task(mode: str):
    if mode == "tokens":
        return TOKENS_PROMPT
    instructions_path = BASE_DIR / "instructions.txt"
    instructions = (
        ("\n\n" + instructions_path.read_text(encoding="utf-8").strip() + "\n\n")
        if instructions_path.exists()
        else ""
    )
    profile_path = BASE_DIR / "instructions.json"
    profile_text = ""
    if profile_path.exists():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile_text = "\n\nHere is the candidate profile data in JSON format:\n" + json.dumps(
            profile, ensure_ascii=False
        )
    return PROMPT_PREFIX + instructions + profile_text


async def run_agent(mode: str):
    browser = get_browser()
    llm = get_llm()
    agent = Agent(
        task=get_task(mode),
        llm=llm,
        browser=browser,
        available_file_paths=[str(RESUME_PATH), str(PROBLEMATIC_SITES_PATH)],
    )

    history = await agent.run(max_steps=1_000_000)
    return history


async def main(mode: str):
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider in ("browser_use", "browser-use", "browseruse"):
        keys_env = os.getenv("BROWSER_USE_API_KEYS")
        keys = [
            k.strip()
            for k in (keys_env.split(",") if keys_env else [])
            if k.strip()
        ]
        single_key = os.getenv("BROWSER_USE_API_KEY")
        if not keys and single_key:
            keys = [single_key]
        if not keys:
            raise RuntimeError("No BROWSER_USE_API_KEYS or BROWSER_USE_API_KEY set")
        i = 0
        while True:
            os.environ["BROWSER_USE_API_KEY"] = keys[i]
            try:
                history = await run_agent(mode)
                if "insufficient credits" in str(history).lower():
                    i = (i + 1) % len(keys)
                    continue
            except Exception as e:
                msg = str(e).lower()
                if "insufficient credits" in msg:
                    i = (i + 1) % len(keys)
                    continue
                raise
    else:
        await run_agent(mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["applying", "tokens"],
        default="applying",
    )
    args = parser.parse_args()
    asyncio.run(main(args.mode))
    