import os
import html
import requests
import streamlit as st
import certifi
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_community.tools.tavily_search import TavilySearchResults

# ==========================================
# ENV
# ==========================================
os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Atlas · Search and weather assistant",
    page_icon="🧭",
    layout="centered",
)

# ==========================================
# STYLES
# ==========================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
    --sky: #EAF1F6;
    --paper: #FFFFFF;
    --ink: #13293D;
    --ink-soft: #4E6479;
    --line: #D3DFE8;
    --sea: #0E7C86;
    --sea-deep: #0A5F67;
    --sun: #F2A93B;
}

html, body, .stApp, [class*="css"] {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    color: var(--ink);
}

.stApp {
    background:
        radial-gradient(900px 420px at 85% -10%, #FBE9C6 0%, rgba(251,233,198,0) 60%),
        var(--sky);
}

#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

.block-container {
    max-width: 760px;
    padding-top: 3.2rem;
    padding-bottom: 4rem;
}

/* ---------- Hero ---------- */
.hero h1 {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 800;
    font-size: 3.1rem;
    line-height: 1.02;
    letter-spacing: -0.03em;
    margin: 0 0 0.7rem 0;
    padding: 0;
    color: var(--ink);
}
.hero p {
    font-size: 1.08rem;
    line-height: 1.55;
    color: var(--ink-soft);
    max-width: 34rem;
    margin: 0 0 1.6rem 0;
}
.tool-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.8rem; }
.tool-pill {
    display: inline-flex; align-items: center; gap: 0.45rem;
    padding: 0.32rem 0.8rem;
    border: 1px solid var(--line);
    background: var(--paper);
    border-radius: 999px;
    font-size: 0.85rem; font-weight: 500; color: var(--ink);
}
.tool-pill .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--sea); }
.tool-pill .dot.sun { background: var(--sun); }

/* ---------- Input ---------- */
div[data-testid="stTextInput"] label { display: none; }
div[data-testid="stTextInput"] input {
    background: var(--paper);
    border: 1.5px solid var(--line);
    border-radius: 14px;
    padding: 0.95rem 1.1rem;
    font-size: 1.05rem;
    color: var(--ink);
    box-shadow: none;
}
div[data-testid="stTextInput"] input::placeholder { color: #8FA3B5; }
div[data-testid="stTextInput"] input:focus {
    border-color: var(--sea);
    box-shadow: 0 0 0 3px rgba(14, 124, 134, 0.18);
}
div[data-testid="stTextInput"] > div,
div[data-testid="stTextInput"] > div > div { border: none; background: transparent; }

/* ---------- Buttons ---------- */
.stButton > button {
    border-radius: 12px;
    border: 1.5px solid var(--line);
    background: var(--paper);
    color: var(--ink);
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 500;
    font-size: 0.92rem;
    padding: 0.55rem 0.9rem;
    transition: border-color .15s, background .15s;
}
.stButton > button:hover { border-color: var(--sea); color: var(--sea-deep); background: #F5FBFB; }
.stButton > button:focus-visible { outline: 3px solid rgba(14,124,134,.35); outline-offset: 2px; }

.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--sea);
    border-color: var(--sea);
    color: #fff;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.7rem 1.2rem;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: var(--sea-deep); border-color: var(--sea-deep); color: #fff;
}

.hint {
    font-size: 0.88rem; color: var(--ink-soft);
    margin: 1.4rem 0 0.5rem 0;
}

/* ---------- Answer card ---------- */
.answer {
    background: var(--paper);
    border: 1px solid var(--line);
    border-left: 5px solid var(--sea);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin: 1.6rem 0 1rem 0;
    box-shadow: 0 10px 30px -18px rgba(19, 41, 61, 0.35);
}
.answer .q {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    margin: 0 0 0.7rem 0;
    color: var(--ink);
}
.answer .a { font-size: 1.04rem; line-height: 1.65; color: var(--ink); white-space: pre-wrap; }

/* ---------- Weather card ---------- */
.wx {
    display: flex; align-items: center; justify-content: space-between; gap: 1rem;
    background: linear-gradient(135deg, #0E7C86 0%, #15546B 100%);
    color: #fff;
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    margin: 0 0 1rem 0;
}
.wx .city { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 1.2rem; }
.wx .desc { opacity: .85; font-size: .95rem; margin-top: .15rem; }
.wx .temp { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 2.8rem; line-height: 1; }
.wx .hum { text-align: right; font-size: .85rem; opacity: .85; margin-top: .3rem; }

/* ---------- Steps ---------- */
.step {
    border-left: 2px solid var(--line);
    padding: 0.1rem 0 0.1rem 1rem;
    margin: 0 0 0.9rem 0.3rem;
    font-size: 0.92rem;
    color: var(--ink-soft);
}
.step b { color: var(--ink); }
.step code { background: #EEF4F8; color: var(--sea-deep); padding: 0.1rem 0.4rem; border-radius: 6px; }
.step .obs { margin-top: 0.3rem; font-size: 0.86rem; white-space: pre-wrap; word-break: break-word; }

div[data-testid="stExpander"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    background: var(--paper);
}
div[data-testid="stExpander"] summary { font-weight: 500; }

@media (max-width: 640px) {
    .hero h1 { font-size: 2.3rem; }
    .wx { flex-direction: column; align-items: flex-start; }
    .wx .hum { text-align: left; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# TOOLS
# ==========================================
search_tool = TavilySearchResults(max_results=2)


@tool
def get_weather_data(city: str) -> str:
    """Fetch current weather information for a city."""
    url = (
        f"http://api.weatherstack.com/current?"
        f"access_key={WEATHERSTACK_API_KEY}&query={city}"
    )
    try:
        data = requests.get(url, timeout=10).json()
    except requests.RequestException:
        return f"Could not reach the weather service for {city}"

    if "current" not in data:
        return f"Could not fetch weather data for {city}"

    return (
        f"City: {city}\n"
        f"Temperature: {data['current']['temperature']}°C\n"
        f"Weather: {data['current']['weather_descriptions'][0]}\n"
        f"Humidity: {data['current']['humidity']}%"
    )


# ==========================================
# AGENT (cached so it is built once)
# ==========================================
@st.cache_resource
def build_agent() -> AgentExecutor:
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0, api_key=GOOGLE_API_KEY)
    tools = [search_tool, get_weather_data]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


agent_executor = build_agent()

# ==========================================
# HELPERS
# ==========================================
def esc(text) -> str:
    return html.escape(str(text))


def parse_weather(observation: str):
    """Turn the weather tool's text output into a dict, or None if it failed."""
    if not str(observation).startswith("City:"):
        return None
    out = {}
    for line in str(observation).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def render_weather_card(w: dict):
    st.markdown(
        f"""
<div class="wx">
  <div>
    <div class="city">{esc(w.get('city', ''))}</div>
    <div class="desc">{esc(w.get('weather', ''))}</div>
  </div>
  <div>
    <div class="temp">{esc(w.get('temperature', ''))}</div>
    <div class="hum">Humidity {esc(w.get('humidity', ''))}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_result(item: dict):
    for w in item["weather"]:
        render_weather_card(w)

    st.markdown(
        f"""
<div class="answer">
  <div class="q">{esc(item['query'])}</div>
  <div class="a">{esc(item['output'])}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if item["steps"]:
        with st.expander(f"How the agent got there ({len(item['steps'])} steps)"):
            for tool_name, tool_input, observation in item["steps"]:
                st.markdown(
                    f"""
<div class="step">
  <b>Used</b> <code>{esc(tool_name)}</code> with <code>{esc(tool_input)}</code>
  <div class="obs">{esc(observation)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )


def set_query(text: str):
    st.session_state.query = text


# ==========================================
# STATE
# ==========================================
if "query" not in st.session_state:
    st.session_state.query = ""
if "history" not in st.session_state:
    st.session_state.history = []

# ==========================================
# HERO
# ==========================================
st.markdown(
    """
<div class="hero">
  <h1>Ask anything.<br>Get the facts and the forecast.</h1>
  <p>Atlas searches the web and checks live weather, then puts the answer together for you.</p>
  <div class="tool-row">
    <span class="tool-pill"><span class="dot"></span>Web search</span>
    <span class="tool-pill"><span class="dot sun"></span>Live weather</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# INPUT
# ==========================================
st.text_input(
    "Your question",
    key="query",
    placeholder="Example: What is the capital of India, and what's the weather there now?",
)

run = st.button("Ask Atlas", type="primary", use_container_width=True)

st.markdown('<div class="hint">Or try one of these</div>', unsafe_allow_html=True)
examples = [
    "Capital of India and its weather now",
    "Weather in Dhaka",
    "Latest news about renewable energy",
]
cols = st.columns(len(examples))
for col, example in zip(cols, examples):
    col.button(example, key=f"ex_{example}", on_click=set_query, args=(example,), use_container_width=True)

# ==========================================
# RUN
# ==========================================
if run:
    query = st.session_state.query.strip()
    if not query:
        st.warning("Type a question first, then press Ask Atlas.")
    else:
        with st.spinner("Searching and thinking..."):
            try:
                response = agent_executor.invoke({"input": query})

                steps, weather = [], []
                for action, observation in response.get("intermediate_steps", []):
                    steps.append((action.tool, action.tool_input, observation))
                    if action.tool == "get_weather_data":
                        parsed = parse_weather(observation)
                        if parsed:
                            weather.append(parsed)

                st.session_state.history.insert(
                    0,
                    {
                        "query": query,
                        "output": response["output"],
                        "steps": steps,
                        "weather": weather,
                    },
                )
            except Exception as e:
                st.error(f"Something went wrong: {e}. Check your API keys in the .env file and try again.")

# ==========================================
# RESULTS
# ==========================================
if st.session_state.history:
    render_result(st.session_state.history[0])

    older = st.session_state.history[1:]
    if older:
        st.markdown('<div class="hint">Earlier answers</div>', unsafe_allow_html=True)
        for item in older:
            with st.expander(item["query"]):
                render_result(item)