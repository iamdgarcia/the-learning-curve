import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

evaluator_llm = ChatOpenAI(model="gpt-4o", temperature=0)

class EvaluationResult(BaseModel):
    score: int = Field(description="A score from 1 to 5.")
    reasoning: str = Field(description="The explanation for the score.")

parser = JsonOutputParser(pydantic_object=EvaluationResult)

eval_prompt = ChatPromptTemplate.from_template("""
You are an expert grader. 
Evaluate the following AI-generated answer against the Ground Truth.

Question: {question}
Ground Truth: {ground_truth}
AI Answer: {ai_answer}

Criteria:
1. Accuracy: Does the answer match the facts in the ground truth?
2. Completeness: Does it cover all parts of the question?

Output a JSON with a 'score' (1-5) and 'reasoning'.

{format_instructions}
""")

eval_chain = eval_prompt | evaluator_llm | parser

def evaluate_agent(question, ground_truth, ai_answer):
    print(f"--- Evaluating ---")
    print(f"Q: {question}")
    print(f"AI: {ai_answer}")
    
    result = eval_chain.invoke({
        "question": question,
        "ground_truth": ground_truth,
        "ai_answer": ai_answer,
        "format_instructions": parser.get_format_instructions()
    })
    
    print(f"Score: {result['score']}/5")
    print(f"Reasoning: {result['reasoning']}")
    return result

if __name__ == "__main__":
    # Example 1: Good Answer
    evaluate_agent(
        question="What is the capital of France?",
        ground_truth="Paris",
        ai_answer="The capital of France is Madrid."
    )
    
    # Example 2: Bad Answer
    evaluate_agent(
        question="Who wrote Hamlet?",
        ground_truth="William Shakespeare",
        ai_answer="I think it was Charles Dickens."
    )
