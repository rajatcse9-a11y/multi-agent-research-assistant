from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv
import os
load_dotenv()

# model setup
llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    temperature=0,
    max_retries=3,
)



def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=(
            "You are a web research assistant. Call the web_search tool once or twice. "
            "Then return the findings as a list where EVERY item has its exact Title, "
            "URL (copied verbatim from the tool output) and a one-line summary. "
            "Use only information from the tool results. Do not add facts, numbers or "
            "sources that are not in the tool results."
        ),
    )


def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "From the given search results, pick the single most relevant URL and call "
            "scrape_url exactly once on it. Then return the scraped text (cleaned, no "
            "extra commentary). If there is no URL in the input, reply with: NO URL FOUND."
        ),
    )    


# writer chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

# critic chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()