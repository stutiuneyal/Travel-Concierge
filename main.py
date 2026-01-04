import os
import getpass #pass values as passwords in the terminal
from langchain_openai import ChatOpenAI

os.environ["LANGSMITH_TRACING"] = "true"

assert os.getenv("LANGSMITH_API_KEY"), "LANGSMITH_API_KEY not set"
assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY not set"

print(os.getenv("OPENAI_API_KEY"))

model = ChatOpenAI(model="gpt-4.1")

from workflow import build_workflow

workflow = build_workflow()

if __name__ == "__main__":
    q = input("Ask: ").strip()
    out = workflow.invoke(
        {"query": q, "routes": [], "results": [], "final_answer": ""}
    )
    print("\n" + out["final_answer"])
