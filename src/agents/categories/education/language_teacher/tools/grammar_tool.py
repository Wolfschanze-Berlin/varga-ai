"""
Grammar Tool - Handles grammar rules, patterns, and corrections.
Provides grammar checking, rule explanation, and practice generation.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from src.log_service import get_logger
from src.tools.base.base_tool import BaseTool


class GrammarCategory(Enum):
    """Categories of grammar rules."""
    VERB_TENSES = "verb_tenses"
    ARTICLES = "articles"
    PREPOSITIONS = "prepositions"
    PRONOUNS = "pronouns"
    ADJECTIVES = "adjectives"
    ADVERBS = "adverbs"
    SENTENCE_STRUCTURE = "sentence_structure"
    CONDITIONALS = "conditionals"
    PASSIVE_VOICE = "passive_voice"
    REPORTED_SPEECH = "reported_speech"
    MODALS = "modals"
    GERUNDS_INFINITIVES = "gerunds_infinitives"


class ErrorSeverity(Enum):
    """Severity levels for grammar errors."""
    MINOR = "minor"          # Small mistakes that don't affect meaning
    MODERATE = "moderate"    # Errors that make sentences awkward
    MAJOR = "major"         # Errors that affect meaning or comprehension
    CRITICAL = "critical"   # Errors that make sentences incomprehensible


@dataclass
class GrammarRule:
    """A grammar rule with explanation and examples."""
    rule_id: str
    category: GrammarCategory
    language: str
    title: str
    explanation: str
    examples_correct: List[str] = field(default_factory=list)
    examples_incorrect: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    difficulty_level: str = "intermediate"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GrammarError:
    """A detected grammar error."""
    text: str
    error_start: int
    error_end: int
    error_type: GrammarCategory
    severity: ErrorSeverity
    message: str
    suggestion: str
    rule_id: Optional[str] = None
    explanation: Optional[str] = None


@dataclass
class GrammarCheck:
    """Result of grammar checking."""
    original_text: str
    errors: List[GrammarError] = field(default_factory=list)
    corrected_text: str = ""
    confidence_score: float = 0.0
    suggestions_count: int = 0


class GrammarTool(BaseTool):
    """
    Tool for grammar checking, rule explanation, and pattern matching.
    Provides grammar correction suggestions and educational content.
    """
    
    def __init__(self):
        """Initialize the grammar tool."""
        super().__init__()
        self.logger = get_logger("grammar_tool")
        
        # Grammar rules database
        self.grammar_rules: Dict[str, GrammarRule] = {}
        
        # Common error patterns
        self.error_patterns: Dict[GrammarCategory, List[Dict]] = {}
        
        # Language-specific settings
        self.language_settings = {
            "english": {
                "articles": ["a", "an", "the"],
                "common_prepositions": ["in", "on", "at", "by", "for", "with", "from", "to"],
                "irregular_verbs": {
                    "go": {"past": "went", "past_participle": "gone"},
                    "have": {"past": "had", "past_participle": "had"},
                    "be": {"past": ["was", "were"], "past_participle": "been"}
                }
            }
        }
    
    async def setup(self) -> bool:
        """Setup the grammar tool with rules and patterns."""
        try:
            await self._load_grammar_rules()
            await self._initialize_error_patterns()
            
            self.logger.info("Grammar Tool setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Grammar Tool: {e}")
            return False
    
    async def _load_grammar_rules(self) -> None:
        """Load grammar rules for different categories."""
        
        # Verb Tenses Rules
        self.grammar_rules["present_simple"] = GrammarRule(
            rule_id="present_simple",
            category=GrammarCategory.VERB_TENSES,
            language="english",
            title="Present Simple Tense",
            explanation="Use present simple for habits, facts, and general truths. Form: Subject + base verb (+ s for he/she/it)",
            examples_correct=[
                "I work every day.",
                "She plays tennis on weekends.",
                "The sun rises in the east."
            ],
            examples_incorrect=[
                "I am work every day.",
                "She play tennis on weekends.",
                "The sun is rise in the east."
            ],
            patterns=[r"\b(I|you|we|they)\s+\w+\b", r"\b(he|she|it)\s+\w+s\b"],
            difficulty_level="beginner"
        )
        
        self.grammar_rules["present_continuous"] = GrammarRule(
            rule_id="present_continuous",
            category=GrammarCategory.VERB_TENSES,
            language="english",
            title="Present Continuous Tense",
            explanation="Use present continuous for actions happening now or temporary actions. Form: Subject + am/is/are + verb-ing",
            examples_correct=[
                "I am working right now.",
                "She is playing tennis at the moment.",
                "We are studying English this semester."
            ],
            examples_incorrect=[
                "I working right now.",
                "She is play tennis at the moment.",
                "We are study English this semester."
            ],
            patterns=[r"\b(am|is|are)\s+\w+ing\b"],
            difficulty_level="beginner"
        )
        
        # Articles Rules
        self.grammar_rules["articles_a_an"] = GrammarRule(
            rule_id="articles_a_an",
            category=GrammarCategory.ARTICLES,
            language="english",
            title="Articles: A vs An",
            explanation="Use 'a' before consonant sounds, 'an' before vowel sounds. It's about the sound, not the letter!",
            examples_correct=[
                "a cat", "an apple", "a university", "an hour"
            ],
            examples_incorrect=[
                "an cat", "a apple", "an university", "a hour"
            ],
            patterns=[r"\ba\s+[aeiou]", r"\ban\s+[^aeiou]"],
            difficulty_level="beginner"
        )
        
        # Prepositions Rules
        self.grammar_rules["time_prepositions"] = GrammarRule(
            rule_id="time_prepositions",
            category=GrammarCategory.PREPOSITIONS,
            language="english",
            title="Time Prepositions: In, On, At",
            explanation="Use 'in' for months/years/seasons, 'on' for days/dates, 'at' for specific times",
            examples_correct=[
                "in January", "on Monday", "at 3 o'clock",
                "in summer", "on Christmas Day", "at midnight"
            ],
            examples_incorrect=[
                "on January", "in Monday", "in 3 o'clock",
                "at summer", "in Christmas Day", "on midnight"
            ],
            difficulty_level="elementary"
        )
        
        # Subject-Verb Agreement
        self.grammar_rules["subject_verb_agreement"] = GrammarRule(
            rule_id="subject_verb_agreement",
            category=GrammarCategory.SENTENCE_STRUCTURE,
            language="english",
            title="Subject-Verb Agreement",
            explanation="Verbs must agree with their subjects in number. Singular subjects take singular verbs.",
            examples_correct=[
                "He goes to work every day.",
                "They go to work every day.",
                "The book is on the table.",
                "The books are on the table."
            ],
            examples_incorrect=[
                "He go to work every day.",
                "They goes to work every day.",
                "The book are on the table.",
                "The books is on the table."
            ],
            difficulty_level="elementary"
        )
    
    async def _initialize_error_patterns(self) -> None:
        """Initialize common error detection patterns."""
        
        self.error_patterns[GrammarCategory.VERB_TENSES] = [
            {
                "pattern": r"\b(I|you|we|they)\s+(don't|doesn't)\b",
                "message": "Use 'don't' with I, you, we, they. Use 'doesn't' with he, she, it.",
                "severity": ErrorSeverity.MODERATE
            },
            {
                "pattern": r"\b(he|she|it)\s+don't\b",
                "message": "Use 'doesn't' with he, she, it.",
                "severity": ErrorSeverity.MODERATE
            }
        ]
        
        self.error_patterns[GrammarCategory.ARTICLES] = [
            {
                "pattern": r"\ba\s+[aeiouAEIOU]",
                "message": "Use 'an' before vowel sounds.",
                "severity": ErrorSeverity.MINOR
            },
            {
                "pattern": r"\ban\s+[^aeiouAEIOU\s]",
                "message": "Use 'a' before consonant sounds.",
                "severity": ErrorSeverity.MINOR
            }
        ]
        
        self.error_patterns[GrammarCategory.SENTENCE_STRUCTURE] = [
            {
                "pattern": r"\b(he|she|it)\s+(\w+)(?<!s)\b",
                "message": "Add 's' to verbs with he, she, it in present simple.",
                "severity": ErrorSeverity.MODERATE
            }
        ]
    
    async def check_grammar(self, text: str, language: str = "english") -> GrammarCheck:
        """
        Check grammar in the provided text.
        
        Args:
            text: Text to check
            language: Language code
            
        Returns:
            GrammarCheck result with errors and suggestions
        """
        try:
            errors = []
            
            # Check for different types of errors
            errors.extend(await self._check_verb_tense_errors(text))
            errors.extend(await self._check_article_errors(text))
            errors.extend(await self._check_preposition_errors(text))
            errors.extend(await self._check_subject_verb_agreement(text))
            
            # Generate corrected text
            corrected_text = await self._generate_corrected_text(text, errors)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(text, errors)
            
            return GrammarCheck(
                original_text=text,
                errors=errors,
                corrected_text=corrected_text,
                confidence_score=confidence,
                suggestions_count=len(errors)
            )
            
        except Exception as e:
            self.logger.error(f"Error checking grammar: {e}")
            return GrammarCheck(original_text=text)
    
    async def _check_verb_tense_errors(self, text: str) -> List[GrammarError]:
        """Check for verb tense errors."""
        errors = []
        
        # Check for don't/doesn't confusion
        dont_pattern = r"\b(he|she|it)\s+don't\b"
        for match in re.finditer(dont_pattern, text, re.IGNORECASE):
            error = GrammarError(
                text=text,
                error_start=match.start(),
                error_end=match.end(),
                error_type=GrammarCategory.VERB_TENSES,
                severity=ErrorSeverity.MODERATE,
                message="Use 'doesn't' with he, she, it",
                suggestion=match.group().replace("don't", "doesn't"),
                rule_id="subject_verb_agreement"
            )
            errors.append(error)
        
        return errors
    
    async def _check_article_errors(self, text: str) -> List[GrammarError]:
        """Check for article errors (a/an)."""
        errors = []
        
        # Check for 'a' before vowel sounds
        a_vowel_pattern = r"\ba\s+[aeiouAEIOU]\w*"
        for match in re.finditer(a_vowel_pattern, text):
            # Skip exceptions like "a university" (u sounds like 'you')
            word = match.group().split()[1].lower()
            if not word.startswith(('uni', 'eur', 'use')):  # Common exceptions
                error = GrammarError(
                    text=text,
                    error_start=match.start(),
                    error_end=match.end(),
                    error_type=GrammarCategory.ARTICLES,
                    severity=ErrorSeverity.MINOR,
                    message="Use 'an' before vowel sounds",
                    suggestion=match.group().replace('a ', 'an '),
                    rule_id="articles_a_an"
                )
                errors.append(error)
        
        # Check for 'an' before consonant sounds
        an_consonant_pattern = r"\ban\s+[^aeiouAEIOU\s]\w*"
        for match in re.finditer(an_consonant_pattern, text):
            # Skip exceptions like "an hour" (h is silent)
            word = match.group().split()[1].lower()
            if not word.startswith(('h', 'x')):  # Common silent h words need better handling
                error = GrammarError(
                    text=text,
                    error_start=match.start(),
                    error_end=match.end(),
                    error_type=GrammarCategory.ARTICLES,
                    severity=ErrorSeverity.MINOR,
                    message="Use 'a' before consonant sounds",
                    suggestion=match.group().replace('an ', 'a '),
                    rule_id="articles_a_an"
                )
                errors.append(error)
        
        return errors
    
    async def _check_preposition_errors(self, text: str) -> List[GrammarError]:
        """Check for common preposition errors."""
        errors = []
        
        # Common time preposition errors
        time_errors = [
            (r"\bon\s+(January|February|March|April|May|June|July|August|September|October|November|December)", "in"),
            (r"\bin\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", "on"),
            (r"\bin\s+\d{1,2}:\d{2}", "at")
        ]
        
        for pattern, correct_prep in time_errors:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                error = GrammarError(
                    text=text,
                    error_start=match.start(),
                    error_end=match.end(),
                    error_type=GrammarCategory.PREPOSITIONS,
                    severity=ErrorSeverity.MODERATE,
                    message=f"Use '{correct_prep}' for this time expression",
                    suggestion=re.sub(r'^(on|in|at)', correct_prep, match.group(), flags=re.IGNORECASE),
                    rule_id="time_prepositions"
                )
                errors.append(error)
        
        return errors
    
    async def _check_subject_verb_agreement(self, text: str) -> List[GrammarError]:
        """Check for subject-verb agreement errors."""
        errors = []
        
        # Simple check for missing 's' in third person singular
        # This is a simplified pattern and would need more sophisticated NLP for accuracy
        third_person_pattern = r"\b(he|she|it)\s+(\w+)(?<!s|es|ies)\b"
        
        # Common verbs that should end in 's'
        common_verbs = ['go', 'do', 'have', 'want', 'like', 'work', 'live', 'play', 'eat', 'drink']
        
        for match in re.finditer(third_person_pattern, text, re.IGNORECASE):
            verb = match.group(2).lower()
            if verb in common_verbs and not verb.endswith(('s', 'ed', 'ing')):
                suggestion = match.group().replace(verb, verb + 's' if not verb.endswith('s') else verb)
                
                error = GrammarError(
                    text=text,
                    error_start=match.start(),
                    error_end=match.end(),
                    error_type=GrammarCategory.SENTENCE_STRUCTURE,
                    severity=ErrorSeverity.MODERATE,
                    message="Add 's' to verbs with he, she, it in present simple",
                    suggestion=suggestion,
                    rule_id="subject_verb_agreement"
                )
                errors.append(error)
        
        return errors
    
    async def _generate_corrected_text(self, text: str, errors: List[GrammarError]) -> str:
        """Generate corrected version of the text."""
        corrected = text
        
        # Sort errors by position (reverse order to maintain positions)
        sorted_errors = sorted(errors, key=lambda x: x.error_start, reverse=True)
        
        for error in sorted_errors:
            # Extract the error portion and replace with suggestion
            corrected = (
                corrected[:error.error_start] + 
                error.suggestion + 
                corrected[error.error_end:]
            )
        
        return corrected
    
    def _calculate_confidence_score(self, text: str, errors: List[GrammarError]) -> float:
        """Calculate confidence score for the grammar check."""
        if not text.strip():
            return 0.0
        
        # Simple scoring based on error density and severity
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        error_weight = sum(
            4 if error.severity == ErrorSeverity.CRITICAL else
            3 if error.severity == ErrorSeverity.MAJOR else
            2 if error.severity == ErrorSeverity.MODERATE else 1
            for error in errors
        )
        
        # Calculate score (higher errors = lower score)
        score = max(0.0, 1.0 - (error_weight / word_count))
        return round(score, 2)
    
    async def explain_rule(self, rule_id: str) -> Optional[str]:
        """
        Get explanation for a specific grammar rule.
        
        Args:
            rule_id: Grammar rule identifier
            
        Returns:
            Formatted explanation or None if not found
        """
        rule = self.grammar_rules.get(rule_id)
        if not rule:
            return None
        
        explanation = f"**{rule.title}**\n\n"
        explanation += f"{rule.explanation}\n\n"
        
        if rule.examples_correct:
            explanation += "**Correct Examples:**\n"
            for example in rule.examples_correct:
                explanation += f"✅ {example}\n"
        
        if rule.examples_incorrect:
            explanation += "\n**Incorrect Examples:**\n"
            for example in rule.examples_incorrect:
                explanation += f"❌ {example}\n"
        
        return explanation
    
    async def get_rules_by_category(self, category: GrammarCategory) -> List[GrammarRule]:
        """Get all rules for a specific category."""
        return [rule for rule in self.grammar_rules.values() if rule.category == category]
    
    async def suggest_practice_exercises(self, errors: List[GrammarError]) -> List[str]:
        """
        Suggest practice exercises based on detected errors.
        
        Args:
            errors: List of grammar errors
            
        Returns:
            List of exercise suggestions
        """
        exercises = []
        
        # Group errors by category
        error_categories = {}
        for error in errors:
            if error.error_type not in error_categories:
                error_categories[error.error_type] = 0
            error_categories[error.error_type] += 1
        
        # Generate exercises for each category
        for category, count in error_categories.items():
            if category == GrammarCategory.VERB_TENSES:
                exercises.append("Practice verb tenses with fill-in-the-blank exercises")
                exercises.append("Complete sentences using the correct form of 'do/does' and 'don't/doesn't'")
            
            elif category == GrammarCategory.ARTICLES:
                exercises.append("Practice choosing between 'a' and 'an' in sentences")
                exercises.append("Complete sentences with the correct article (a, an, the)")
            
            elif category == GrammarCategory.PREPOSITIONS:
                exercises.append("Practice time prepositions (in, on, at) with dates and times")
                exercises.append("Complete sentences with the correct preposition")
            
            elif category == GrammarCategory.SENTENCE_STRUCTURE:
                exercises.append("Practice subject-verb agreement with third person singular")
                exercises.append("Correct sentences with agreement errors")
        
        return exercises[:5]  # Limit to 5 suggestions
    
    def format_grammar_check_result(self, check: GrammarCheck) -> str:
        """Format grammar check results for display."""
        if not check.errors:
            return f"✅ **Great grammar!** No errors detected.\n\nConfidence: {check.confidence_score:.0%}"
        
        result = f"📝 **Grammar Check Results**\n\n"
        result += f"**Original:** {check.original_text}\n"
        result += f"**Corrected:** {check.corrected_text}\n\n"
        
        result += f"**Errors found:** {len(check.errors)}\n"
        result += f"**Confidence:** {check.confidence_score:.0%}\n\n"
        
        result += "**Details:**\n"
        for i, error in enumerate(check.errors, 1):
            severity_icon = {
                ErrorSeverity.MINOR: "🟡",
                ErrorSeverity.MODERATE: "🟠", 
                ErrorSeverity.MAJOR: "🔴",
                ErrorSeverity.CRITICAL: "⚫"
            }.get(error.severity, "⚪")
            
            result += f"{i}. {severity_icon} {error.message}\n"
            result += f"   💡 **Suggestion:** {error.suggestion}\n"
            if error.rule_id:
                result += f"   📚 **Rule:** {error.rule_id}\n"
            result += "\n"
        
        return result
    
    async def get_grammar_tips(self, difficulty_level: str = "beginner") -> List[str]:
        """Get grammar tips for a specific difficulty level."""
        tips = {
            "beginner": [
                "Remember: 'I go' but 'he goes' (add 's' for he/she/it)",
                "Use 'a' before consonants, 'an' before vowels: 'a cat', 'an apple'",
                "Don't forget: 'I don't' but 'he doesn't'",
                "Use 'in' for months (in January), 'on' for days (on Monday), 'at' for times (at 3 PM)"
            ],
            "elementary": [
                "Present continuous: I am working (right now)",
                "Present simple: I work (every day, habit)",
                "Use 'the' when talking about something specific",
                "Prepositions can be tricky - practice with common phrases"
            ],
            "intermediate": [
                "Perfect tenses show connection between past and present",
                "Use passive voice to focus on the action, not the doer",
                "Conditional sentences: If I had time, I would travel",
                "Reported speech changes tenses: 'I am happy' → He said he was happy"
            ],
            "advanced": [
                "Use subjunctive mood for hypothetical situations",
                "Master complex sentence structures with multiple clauses",
                "Understand subtle differences in modal verbs",
                "Practice with idiomatic expressions and phrasal verbs"
            ]
        }
        
        return tips.get(difficulty_level, tips["beginner"])
    
    async def cleanup(self) -> None:
        """Clean up grammar tool resources."""
        self.grammar_rules.clear()
        self.error_patterns.clear()
        self.logger.info("Grammar Tool cleaned up")