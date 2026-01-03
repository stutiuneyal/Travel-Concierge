import os
import getpass #pass values as passwords in the terminal
from langchain_openai import ChatOpenAI

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = getpass.getpass()

os.environ["OPENAI_API_KEY"] = "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"

model = ChatOpenAI(model="gpt-4.1")

from workflow import build_workflow

workflow = build_workflow()

if __name__ == "__main__":
    q = input("Ask: ").strip()
    out = workflow.invoke(
        {"query": q, "routes": [], "results": [], "final_answer": ""}
    )
    print("\n" + out["final_answer"])
