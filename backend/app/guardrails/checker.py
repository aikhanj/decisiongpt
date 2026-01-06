import re
from dataclasses import dataclass
from typing import Optional

from app.schemas.move import Move


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation."""

    rule: str
    severity: str  # "error" or "warning"
    description: str
    field: str  # Which field triggered the violation


class GuardrailChecker:
    """Checks moves against gentleman guardrails."""

    # Hard reject patterns - any match is a violation
    HARD_REJECT_PATTERNS = [
        (r"keep\s+(texting|messaging|calling)\s+until", "Persistence after no response"),
        (r"make\s+her\s+jealous", "Jealousy manipulation"),
        (r"neg\s+her|backhanded\s+compliment", "Negging/backhanded compliments"),
        (r"lie\s+about|make\s+up|fabricate", "Deception"),
        (r"guilt\s+(her|trip)", "Guilt manipulation"),
        (r"don'?t\s+take\s+no", "Persistence after rejection"),
        (r"pressure\s+her|force\s+her", "Pressure tactics"),
        (r"ignore\s+(her\s+)?boundaries", "Boundary violation"),
        (r"get\s+her\s+drunk|when\s+she'?s\s+drunk", "Exploitation of intoxication"),
        (r"follow\s+her|show\s+up\s+uninvited", "Stalking behavior"),
    ]

    # Warning patterns - flag but don't block
    WARNING_PATTERNS = [
        (r"triple\s+text", "Triple texting is rarely advisable"),
        (r"late\s+night\s+(text|message|call)", "Late night messaging may indicate poor timing"),
        (r"drunk\s+text", "Messaging while intoxicated"),
        (r"emotional\s+dump", "Emotional dumping early on"),
    ]

    # Maximum words for scripts to prevent wall-of-text
    MAX_SCRIPT_WORDS = 75

    def check_move(self, move: Move, additional_guardrails: list[str] = None) -> list[GuardrailViolation]:
        """
        Check a move for guardrail violations.

        Args:
            move: The move to check
            additional_guardrails: Template-specific guardrails to add

        Returns:
            List of violations found
        """
        violations = []

        # Check scripts
        for script_type in ["direct", "softer"]:
            script = getattr(move.scripts, script_type)
            violations.extend(self._check_text(script, f"scripts.{script_type}"))

            # Check word count
            word_count = len(script.split())
            if word_count > self.MAX_SCRIPT_WORDS:
                violations.append(
                    GuardrailViolation(
                        rule="wall_of_text",
                        severity="error",
                        description=f"Script exceeds {self.MAX_SCRIPT_WORDS} words ({word_count} words)",
                        field=f"scripts.{script_type}",
                    )
                )

        # Check branches
        for branch_type in ["warm", "neutral", "cold"]:
            branch = getattr(move.branches, branch_type)
            violations.extend(self._check_text(branch.script, f"branches.{branch_type}.script"))
            violations.extend(self._check_text(branch.next_move, f"branches.{branch_type}.next_move"))

        # Check move title and descriptions
        violations.extend(self._check_text(move.title, "title"))
        violations.extend(self._check_text(move.when_to_use, "when_to_use"))

        return violations

    def _check_text(self, text: str, field: str) -> list[GuardrailViolation]:
        """Check a text field against patterns."""
        violations = []
        text_lower = text.lower()

        # Check hard reject patterns
        for pattern, description in self.HARD_REJECT_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(
                    GuardrailViolation(
                        rule=pattern,
                        severity="error",
                        description=description,
                        field=field,
                    )
                )

        # Check warning patterns
        for pattern, description in self.WARNING_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(
                    GuardrailViolation(
                        rule=pattern,
                        severity="warning",
                        description=description,
                        field=field,
                    )
                )

        return violations

    def has_errors(self, violations: list[GuardrailViolation]) -> bool:
        """Check if any violations are errors."""
        return any(v.severity == "error" for v in violations)


def check_move_guardrails(
    move: Move, additional_guardrails: list[str] = None
) -> tuple[bool, list[GuardrailViolation]]:
    """
    Convenience function to check move guardrails.

    Returns:
        Tuple of (is_valid, violations)
    """
    checker = GuardrailChecker()
    violations = checker.check_move(move, additional_guardrails)
    is_valid = not checker.has_errors(violations)
    return is_valid, violations
