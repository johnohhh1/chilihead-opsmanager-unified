"""
Entity extraction schema and utilities for AI agents
Prevents example names from being treated as real entities
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import re
from datetime import datetime

@dataclass
class Entity:
    """Represents an extracted entity with metadata"""
    name: str
    entity_type: str  # 'person', 'location', 'vendor', 'system'
    confidence: float  # 0-100
    context: str  # Where/how it was mentioned
    is_example: bool = False  # Flag for example data
    frequency: int = 1  # How many times mentioned

class EntityExtractor:
    """Smart entity extraction that differentiates examples from real data"""

    # Known example names from prompts/instructions
    EXAMPLE_NAMES = {
        'hannah', 'blake', 'sarah', 'mike', 'zimmerman',
        'pedro',  # Old test data
        'john',   # User's actual name, but often in examples
    }

    # Common words that look like names but aren't
    COMMON_WORDS = {
        'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'Where', 'When',
        'Email', 'Subject', 'From', 'Date', 'Time', 'Today', 'Tomorrow', 'Yesterday',
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        'January', 'February', 'March', 'April', 'May', 'June', 'July',
        'August', 'September', 'October', 'November', 'December',
        'Morning', 'Afternoon', 'Evening', 'Night', 'Week', 'Month', 'Year',
        'Server', 'Client', 'Database', 'System', 'Error', 'Warning', 'Message',
        'Budget', 'Target', 'Actual', 'Variance', 'Sales', 'Labor', 'Food',
        'Please', 'Also', 'However', 'Therefore', 'Moreover', 'Furthermore',
        'Analysis', 'Report', 'Summary', 'Review', 'Update', 'Status',
        'Urgent', 'Important', 'Critical', 'Normal', 'Low', 'High',
        'First', 'Second', 'Third', 'Last', 'Next', 'Previous',
        'New', 'Old', 'Current', 'Recent', 'Latest', 'Updated',
        'Yes', 'No', 'Maybe', 'Confirmed', 'Pending', 'Complete',
        'He', 'She', 'They', 'It', 'We', 'You', 'I',
        'Manager', 'District', 'Regional', 'Corporate', 'Team'
    }

    # Patterns that indicate example context
    EXAMPLE_PATTERNS = [
        r'(?i)example[s]?[:]\s*',
        r'(?i)e\.g\.\s*',
        r'(?i)for instance\s*',
        r'(?i)such as\s*',
        r'✓\s*".*?"',  # Example with checkmark
        r'✗\s*".*?"',  # Example with X mark
    ]

    @classmethod
    def extract_entities(cls, text: str, context_source: str = 'unknown') -> List[Entity]:
        """
        Extract entities from text with context awareness

        Args:
            text: The text to extract entities from
            context_source: Where this text came from ('email', 'prompt', 'memory', etc.)

        Returns:
            List of Entity objects with metadata
        """
        entities = []

        # Check if we're in an example section
        is_example_context = any(re.search(pattern, text) for pattern in cls.EXAMPLE_PATTERNS)

        # Extract potential person names (single capitalized words only)
        # We'll handle last names separately
        name_pattern = r'\b([A-Z][a-z]+)\b'
        words = re.findall(name_pattern, text)

        # Filter out words that are definitely not names
        potential_names = [w for w in words if w not in cls.COMMON_WORDS]

        # Look for actual names (not titles or common words)
        names = []
        for word in potential_names:
            # Skip if it's a known title that precedes a name
            if word in {'District', 'Regional', 'General', 'Assistant', 'Senior', 'Junior'}:
                # Look for the actual name after the title
                pattern = rf'\b{re.escape(word)}\s+(?:Manager\s+)?([A-Z][a-z]+)\b'
                match = re.search(pattern, text)
                if match:
                    actual_name = match.group(1)
                    if actual_name not in cls.COMMON_WORDS:
                        names.append(actual_name)
            else:
                names.append(word)

        # Count frequencies
        name_counts = {}
        for name in names:
            if name not in cls.COMMON_WORDS:
                name_counts[name] = name_counts.get(name, 0) + 1

        # Process each unique name
        for name, count in name_counts.items():
            # Determine if this is likely an example
            is_example = (
                is_example_context or
                name.lower() in cls.EXAMPLE_NAMES or
                context_source == 'prompt'  # Names in prompts are usually examples
            )

            # Calculate confidence based on various factors
            confidence = cls._calculate_confidence(name, count, text, is_example)

            # Only include if confidence is reasonable and not an example
            # OR if it's mentioned frequently enough to override example status
            if (confidence > 30 and not is_example) or (count > 2 and confidence > 60):
                entities.append(Entity(
                    name=name,
                    entity_type='person',
                    confidence=confidence,
                    context=cls._extract_context(name, text),
                    is_example=is_example and count <= 2,  # Override if mentioned often
                    frequency=count
                ))

        # Sort by confidence and frequency
        entities.sort(key=lambda x: (x.confidence * x.frequency), reverse=True)

        return entities[:5]  # Top 5 entities

    @classmethod
    def _calculate_confidence(cls, name: str, frequency: int, text: str, is_example: bool) -> float:
        """Calculate confidence score for an entity"""
        confidence = 50.0  # Base confidence

        # Adjust based on frequency
        confidence += min(frequency * 10, 30)  # Max +30 for frequency

        # Penalize if it looks like an example
        if is_example:
            confidence -= 40

        # Boost if mentioned with action verbs (indicates real person)
        action_patterns = [
            rf'{name}\s+(called|emailed|sent|needs|requested|approved|submitted)',
            rf'(contact|call|email|notify|tell|ask)\s+{name}',
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in action_patterns):
            confidence += 20

        # Boost if mentioned with roles/titles
        role_patterns = [
            rf'{name}.*?(manager|supervisor|employee|staff|team|lead|cook|server|host)',
            rf'(manager|supervisor|employee|staff|team|lead|cook|server|host).*?{name}',
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in role_patterns):
            confidence += 15

        return min(max(confidence, 0), 100)  # Clamp to 0-100

    @classmethod
    def _extract_context(cls, name: str, text: str, max_length: int = 100) -> str:
        """Extract surrounding context for an entity mention"""
        # Find first occurrence
        match = re.search(rf'\b{re.escape(name)}\b', text, re.IGNORECASE)
        if not match:
            return ""

        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end].strip()

        # Clean up and truncate
        context = ' '.join(context.split())  # Normalize whitespace
        if len(context) > max_length:
            context = context[:max_length] + "..."

        return context

    @classmethod
    def filter_real_entities(cls, entities: List[Entity]) -> List[str]:
        """
        Filter to only real (non-example) entity names

        Returns just the names for backward compatibility
        """
        real_entities = [
            e.name for e in entities
            if not e.is_example and e.confidence > 50
        ]
        return real_entities[:3]  # Top 3 for memory summaries

# Backward-compatible function for existing code
def extract_entity_names(text: str, source: str = 'email') -> List[str]:
    """
    Extract real entity names from text (backward compatible)

    Args:
        text: The text to extract from
        source: Where this came from ('email', 'prompt', 'memory')

    Returns:
        List of entity names (strings)
    """
    entities = EntityExtractor.extract_entities(text, source)
    return EntityExtractor.filter_real_entities(entities)