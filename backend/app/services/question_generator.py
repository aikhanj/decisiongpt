"""Question Generator - Generates candidate questions from templates."""

from app.schemas.question import CandidateQuestion
from app.schemas.canvas import CanvasState


class QuestionGenerator:
    """
    Generates candidate questions using templates and domain knowledge.

    For MVP, focuses on template-based generation.
    Future: Can integrate AI generation for custom questions.
    """

    def generate_initial_question_pool(
        self,
        situation_text: str,
        decision_type: str,
        initial_canvas: CanvasState,
    ) -> list[CandidateQuestion]:
        """
        Generate initial pool of 15-20 candidate questions.

        Sources:
        1. Template-based (domain-specific)
        2. Critical field questions
        3. Universal questions that apply to all decisions

        Args:
            situation_text: User's situation description
            decision_type: Type of decision (career, financial, relationship, etc.)
            initial_canvas: Initial canvas state

        Returns:
            List of candidate questions
        """
        pool = []

        # Add domain-specific template questions
        pool.extend(self._get_template_questions(decision_type))

        # Add critical field questions if fields missing
        pool.extend(self._generate_critical_field_questions(initial_canvas))

        # Add universal questions
        pool.extend(self._get_universal_questions())

        return pool

    def _get_template_questions(self, decision_type: str) -> list[CandidateQuestion]:
        """
        Get pre-built high-quality questions for decision domain.

        Args:
            decision_type: career, financial, relationship, personal, business, etc.

        Returns:
            List of template questions for this domain
        """
        templates = {
            "career": [
                CandidateQuestion(
                    id="career_deadline",
                    question="What is your deadline for making this decision?",
                    answer_type="text",
                    why_this_question="Knowing your timeline helps prioritize speed vs thoroughness in decision-making",
                    what_it_changes="Sets urgency level and may limit options that take too long to implement",
                    priority=80,
                    targets_canvas_field="timeline",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="career_relocation",
                    question="Is relocation an option for you?",
                    answer_type="yes_no",
                    why_this_question="Location flexibility significantly affects which opportunities are viable",
                    what_it_changes="Eliminates options that require moving if relocation isn't possible (hard constraint)",
                    priority=85,
                    targets_canvas_field="constraints",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="career_priorities",
                    question="What matters more to you: salary growth or work-life balance?",
                    answer_type="single_select",
                    choices=["Salary growth", "Work-life balance", "Both equally", "Neither - something else matters more"],
                    why_this_question="Understanding your core priorities helps evaluate which opportunities align with your values",
                    what_it_changes="Weights the criteria for evaluating options - high weight on your chosen priority",
                    priority=90,
                    targets_canvas_field="criteria",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="career_growth",
                    question="How important is learning and skill development in this decision?",
                    answer_type="single_select",
                    choices=["Critical", "Important", "Nice to have", "Not important"],
                    why_this_question="Growth opportunities vary significantly between options and affect long-term satisfaction",
                    what_it_changes="Adds 'growth potential' as a weighted criterion in option evaluation",
                    priority=70,
                    targets_canvas_field="criteria",
                ),
            ],
            "financial": [
                CandidateQuestion(
                    id="financial_budget",
                    question="What is your budget or financial constraint for this decision?",
                    answer_type="text",
                    why_this_question="Financial limits are often hard constraints that eliminate non-viable options",
                    what_it_changes="Filters out options that exceed your budget (hard constraint)",
                    priority=95,
                    targets_canvas_field="constraints",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="financial_timeline",
                    question="What is your investment timeline or when do you need this money?",
                    answer_type="text",
                    why_this_question="Timeline affects risk tolerance and appropriate investment/spending strategies",
                    what_it_changes="Sets timeline constraint and influences risk assessment",
                    priority=85,
                    targets_canvas_field="timeline",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="financial_risk",
                    question="How comfortable are you with financial risk?",
                    answer_type="single_select",
                    choices=["Very risk-averse", "Somewhat cautious", "Moderate risk tolerance", "Comfortable with high risk"],
                    why_this_question="Risk tolerance fundamentally shapes which financial options are appropriate for you",
                    what_it_changes="Adjusts option evaluation to favor lower/higher risk based on your comfort level",
                    priority=90,
                    targets_canvas_field="criteria",
                    critical_variable=True,
                ),
            ],
            "relationship": [
                CandidateQuestion(
                    id="relationship_timeline",
                    question="Do you have a timeline or deadline for making this decision?",
                    answer_type="text",
                    why_this_question="Emotional decisions benefit from appropriate pacing - neither rushed nor indefinitely delayed",
                    what_it_changes="Sets a boundary on decision timeline to prevent analysis paralysis",
                    priority=70,
                    targets_canvas_field="timeline",
                ),
                CandidateQuestion(
                    id="relationship_priority",
                    question="What is your main objective: maximizing your long-term happiness, minimizing pain, or fulfilling obligations?",
                    answer_type="single_select",
                    choices=["Long-term happiness", "Minimizing pain/conflict", "Fulfilling obligations", "Multiple goals"],
                    why_this_question="Clarifying your core objective helps identify criteria that truly matter",
                    what_it_changes="Sets the primary decision criterion that options will be evaluated against",
                    priority=95,
                    targets_canvas_field="criteria",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="relationship_dealbreakers",
                    question="Are there any absolute deal-breakers or non-negotiable aspects?",
                    answer_type="text",
                    why_this_question="Identifying hard boundaries eliminates options that violate your core values",
                    what_it_changes="Adds hard constraints that filter out incompatible options",
                    priority=85,
                    targets_canvas_field="constraints",
                    critical_variable=True,
                ),
            ],
            "personal": [
                CandidateQuestion(
                    id="personal_impact",
                    question="Who else will be significantly affected by this decision?",
                    answer_type="text",
                    why_this_question="Understanding stakeholders helps identify constraints and criteria beyond just your preferences",
                    what_it_changes="Adds context about stakeholders and may add criteria about their wellbeing",
                    priority=75,
                    targets_canvas_field="context",
                ),
                CandidateQuestion(
                    id="personal_values",
                    question="What values or principles are most important to you in this situation?",
                    answer_type="text",
                    why_this_question="Values alignment is often the difference between satisfaction and regret",
                    what_it_changes="Adds criteria based on your core values (e.g., authenticity, fairness, growth)",
                    priority=85,
                    targets_canvas_field="criteria",
                    critical_variable=True,
                ),
            ],
            "business": [
                CandidateQuestion(
                    id="business_budget",
                    question="What is your budget or resource constraint for this initiative?",
                    answer_type="text",
                    why_this_question="Budget constraints eliminate options that aren't financially viable",
                    what_it_changes="Sets hard financial constraint on options",
                    priority=90,
                    targets_canvas_field="constraints",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="business_timeline",
                    question="What is your timeline or deadline for this decision?",
                    answer_type="text",
                    why_this_question="Business decisions often have market timing or opportunity costs",
                    what_it_changes="Sets timeline constraint and affects which options are feasible",
                    priority=85,
                    targets_canvas_field="timeline",
                    critical_variable=True,
                ),
                CandidateQuestion(
                    id="business_success",
                    question="How do you define success for this initiative?",
                    answer_type="text",
                    why_this_question="Clear success metrics ensure options are evaluated against the right goals",
                    what_it_changes="Defines primary success criteria that guide option selection",
                    priority=90,
                    targets_canvas_field="criteria",
                    critical_variable=True,
                ),
            ],
        }

        # Get template questions for this type, or fall back to 'other'
        return templates.get(decision_type, templates.get("personal", []))

    def _generate_critical_field_questions(
        self, canvas: CanvasState
    ) -> list[CandidateQuestion]:
        """
        Generate questions for critical missing canvas fields.

        Args:
            canvas: Current canvas state

        Returns:
            Questions targeting missing critical fields
        """
        questions = []

        # If no statement, ask for clarification
        if not canvas.statement:
            questions.append(
                CandidateQuestion(
                    id="clarify_statement",
                    question="Can you summarize the decision you're trying to make in one clear sentence?",
                    answer_type="text",
                    why_this_question="A clear decision statement frames the entire decision-making process",
                    what_it_changes="Sets the decision statement that all options will address",
                    priority=100,
                    targets_canvas_field="statement",
                    critical_variable=True,
                )
            )

        # If no criteria, ask what matters
        if len(canvas.criteria) == 0:
            questions.append(
                CandidateQuestion(
                    id="identify_criteria",
                    question="What factors are most important to you in making this decision?",
                    answer_type="text",
                    why_this_question="Knowing what matters helps evaluate options against your actual priorities",
                    what_it_changes="Identifies the key criteria that will be used to score and compare options",
                    priority=95,
                    targets_canvas_field="criteria",
                    critical_variable=True,
                )
            )

        # If no constraints, ask about deal-breakers
        if len(canvas.constraints) == 0:
            questions.append(
                CandidateQuestion(
                    id="identify_constraints",
                    question="Do you have any absolute requirements or deal-breakers?",
                    answer_type="text",
                    why_this_question="Hard constraints eliminate options early, saving time on non-viable paths",
                    what_it_changes="Sets non-negotiable requirements that filter out incompatible options",
                    priority=85,
                    targets_canvas_field="constraints",
                    critical_variable=True,
                )
            )

        return questions

    def _get_universal_questions(self) -> list[CandidateQuestion]:
        """
        Get universal questions that apply to all decision types.

        These are lower priority and asked later if needed.

        Returns:
            List of universal questions
        """
        return [
            CandidateQuestion(
                id="universal_context",
                question="Is there any additional context or background that would help understand your situation?",
                answer_type="text",
                why_this_question="Additional context can reveal constraints or criteria that aren't immediately obvious",
                what_it_changes="Adds context bullets that inform the decision analysis",
                priority=50,
                targets_canvas_field="context",
            ),
            CandidateQuestion(
                id="universal_urgency",
                question="How urgent is this decision? Do you have a deadline?",
                answer_type="text",
                why_this_question="Urgency affects how thoroughly we analyze vs how quickly we decide",
                what_it_changes="Sets timeline and affects the depth of analysis (quick mode vs deep mode)",
                priority=60,
                targets_canvas_field="timeline",
            ),
        ]
