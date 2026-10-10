import re
from typing import Any, Dict, List, Literal

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
router_llm = ChatOpenAI(model="gpt-4o", temperature=0)


class Outline(BaseModel):
    """Represents the planner output with ordered blog sections."""

    sections: List[str] = Field(
        description="Ordered list of section titles for the blog post."
    )


class Route(BaseModel):
    """Represents the router decision for section specialization."""

    destination: Literal["explanatory", "how_to", "case_study"] = Field(
        description="Specialist style for the current section."
    )


class Review(BaseModel):
    """Represents reflective QA decision for a drafted section."""

    verdict: Literal["approve", "revise"] = Field(
        description="Whether the draft is ready or needs revision."
    )
    critique: str = Field(
        description="Short critique with concrete improvements if revision is needed."
    )


planner_parser = JsonOutputParser(pydantic_object=Outline)
planner_prompt = ChatPromptTemplate.from_template(
    """
You are a content strategist.
Create a 3-5 section outline for a blog post about: {topic}.
The outline should have a logical narrative flow and avoid redundancy.
Return JSON with a 'sections' key.

{format_instructions}
"""
)
planner_chain = planner_prompt | llm | planner_parser

router_parser = JsonOutputParser(pydantic_object=Route)
router_prompt = ChatPromptTemplate.from_template(
    """
Route this section to the best specialist style.

Section title: {section_title}
Topic: {topic}
Recent destinations: {recent_destinations}
Current section index: {section_index}
Total sections: {total_sections}

Destinations:
- explanatory: definitions, concepts, or context.
- how_to: steps, checklists, actionable guidance.
- case_study: examples, scenarios, outcomes.

Routing policy:
- Choose the best destination for this section title and position.
- Avoid using the same destination for every section when alternatives fit.
- Prefer narrative variety across a multi-section post.
- Decision table (apply in this order):
  1) If title contains "getting started", "how to", "steps", "guide",
      "best practices", or "implementation", you MUST choose `how_to`.
  2) Else if title contains "impact", "case", "example", "results",
      "community", "economic", or "outcomes", choose `case_study`.
  3) Else if title is introductory or conceptual, choose `explanatory`.
  4) Else choose the best fit while maintaining distribution across sections.
- Apply the table even when previous destinations were different.

Return JSON with a 'destination' key.

{format_instructions}
"""
)
router_chain = router_prompt | router_llm | router_parser

researcher_chains: Dict[str, Any] = {
    "explanatory": ChatPromptTemplate.from_template(
        """
You are an explanatory researcher.
Provide 4 concise bullet points for section "{section_title}".
Topic: {topic}
Prior section context: {context}
Focus on clarity, core concepts, and useful facts.
"""
    )
    | llm,
    "how_to": ChatPromptTemplate.from_template(
        """
You are a practical researcher.
Provide 4 concise bullet points for section "{section_title}".
Topic: {topic}
Prior section context: {context}
Focus on steps, best practices, and pitfalls.
"""
    )
    | llm,
    "case_study": ChatPromptTemplate.from_template(
        """
You are a case-study researcher.
Provide 4 concise bullet points for section "{section_title}".
Topic: {topic}
Prior section context: {context}
Focus on realistic examples and outcomes.
"""
    )
    | llm,
}

writer_chains: Dict[str, Any] = {
    "explanatory": ChatPromptTemplate.from_template(
        """
You are a blog writer.
Write one engaging, clear paragraph for section "{section_title}".
Use these notes:
{notes}
Keep it educational and easy to follow.
"""
    )
    | llm,
    "how_to": ChatPromptTemplate.from_template(
        """
You are a blog writer.
Write one actionable paragraph for section "{section_title}".
Use these notes:
{notes}
Keep it practical and direct.
"""
    )
    | llm,
    "case_study": ChatPromptTemplate.from_template(
        """
You are a blog writer.
Write one narrative-style paragraph for section "{section_title}".
Use these notes:
{notes}
Keep it concrete and outcome-oriented.
"""
    )
    | llm,
}

review_parser = JsonOutputParser(pydantic_object=Review)
review_prompt = ChatPromptTemplate.from_template(
    """
You are a strict editor reviewing one blog section.
Evaluate the draft for clarity, accuracy, flow, and tone.

Section: {section_title}
Draft:
{draft}

Return JSON with:
- verdict: "approve" or "revise"
- critique: short actionable feedback

{format_instructions}
"""
)
review_chain = review_prompt | llm | review_parser

revise_prompt = ChatPromptTemplate.from_template(
    """
You are a senior editor.
Rewrite the section to address the critique while preserving intent.

Section: {section_title}
Original draft:
{draft}

Critique:
{critique}

Return only the revised paragraph.
"""
)
revise_chain = revise_prompt | llm

editor_prompt = ChatPromptTemplate.from_template(
    """
You are an editor.
Polish this full blog post in markdown.
Fix grammar and improve cohesion while preserving all meaning.

Draft:
{draft}
"""
)
editor_chain = editor_prompt | llm


def slugify_topic(topic: str) -> str:
    """Convert a topic into a safe markdown filename slug."""

    slug = re.sub(r"[^a-z0-9]+", "_", topic.strip().lower())
    return slug.strip("_") or "blog_post"


def message_to_text(content: Any) -> str:
    """Normalize LLM responses into a plain string for safe downstream use."""

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: List[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict) and "text" in item:
                chunks.append(str(item["text"]))
            else:
                chunks.append(str(item))
        return "\n".join(chunks)
    return str(content)


def plan_sections(topic: str) -> List[str]:
    """Generate ordered section titles using the planning pattern."""

    outline = planner_chain.invoke(
        {
            "topic": topic,
            "format_instructions": planner_parser.get_format_instructions(),
        }
    )
    sections = outline.get("sections", [])
    if not sections:
        return [
            "Introduction",
            "Key Insights",
            "Conclusion",
        ]
    return [section.strip() for section in sections if section.strip()]


def route_section(
    section_title: str,
    topic: str,
    recent_destinations: List[str],
    section_index: int,
    total_sections: int,
) -> str:
    """Select a specialist route using LLM routing only."""

    route = router_chain.invoke(
        {
            "section_title": section_title,
            "topic": topic,
            "recent_destinations": ", ".join(recent_destinations[-3:]) or "none",
            "section_index": section_index,
            "total_sections": total_sections,
            "format_instructions": router_parser.get_format_instructions(),
        }
    )
    destination = route.get("destination", "explanatory")
    if destination not in researcher_chains:
        destination = "explanatory"
    return destination


def research_and_write_section(
    topic: str,
    section_title: str,
    destination: str,
    context: str,
) -> str:
    """Research and draft one section using specialized worker chains."""

    notes = researcher_chains[destination].invoke(
        {
            "topic": topic,
            "section_title": section_title,
            "context": context,
        }
    ).content
    notes_text = message_to_text(notes)
    drafted = writer_chains[destination].invoke(
        {"section_title": section_title, "notes": notes_text}
    ).content
    return message_to_text(drafted)


def reflect_and_improve(section_title: str, draft: str) -> str:
    """Run reflective critique and optional revision for a section."""

    review = review_chain.invoke(
        {
            "section_title": section_title,
            "draft": draft,
            "format_instructions": review_parser.get_format_instructions(),
        }
    )
    if review.get("verdict") == "approve":
        return draft
    critique = review.get("critique", "Improve clarity and flow.")
    revised = revise_chain.invoke(
        {
            "section_title": section_title,
            "draft": draft,
            "critique": critique,
        }
    ).content
    return message_to_text(revised)


def run_content_pipeline(topic: str) -> str:
    """Run end-to-end content workflow and persist final markdown file."""

    print(f"--- Starting Integrated Pipeline: {topic} ---")

    print("1) Planner: creating section plan...")
    sections = plan_sections(topic)
    print(f"Planned sections: {sections}")

    full_draft = f"# {topic}\n\n"
    context_items: List[str] = []

    print("2) Router + Researcher + Writer + Reflector: section loop...")
    route_history: List[str] = []
    for index, section_title in enumerate(sections, start=1):
        print(f"\nSection {index}: {section_title}")
        destination = route_section(
            section_title=section_title,
            topic=topic,
            recent_destinations=route_history,
            section_index=index,
            total_sections=len(sections),
        )
        route_history.append(destination)
        print(f"- Routed to: {destination}")

        context = " | ".join(context_items[-2:])
        drafted_section = research_and_write_section(
            topic=topic,
            section_title=section_title,
            destination=destination,
            context=context,
        )
        revised_section = reflect_and_improve(section_title, drafted_section)

        full_draft += f"## {section_title}\n{revised_section}\n\n"
        context_items.append(f"{section_title}: {revised_section[:120]}")

    print("\n3) Editor: polishing complete draft...")
    final_post = message_to_text(editor_chain.invoke({"draft": full_draft}).content)

    filename = f"{slugify_topic(topic)}.md"
    with open(filename, "w", encoding="utf-8") as file_handle:
        file_handle.write(final_post)

    print(f"\nSaved polished post to: {filename}")
    return filename


if __name__ == "__main__":
    run_content_pipeline("The Benefits of Urban Gardening")
