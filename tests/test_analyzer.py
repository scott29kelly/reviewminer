"""Tests for the analyzer module."""

import pytest
from unittest.mock import MagicMock, patch

from src.analyzer import PainPointAnalyzer
from src.models import Review


class TestPainPointAnalyzer:
    """Tests for PainPointAnalyzer."""
    
    def test_format_reviews(self):
        """Test review formatting for prompt."""
        analyzer = PainPointAnalyzer.__new__(PainPointAnalyzer)
        analyzer.client = None
        analyzer.model = "test"
        
        reviews = [
            Review(
                source="test",
                product_title="Test Book",
                rating=2,
                review_text="This is a test review.",
            ),
            Review(
                source="amazon",
                product_title="Another Book",
                rating=1,
                review_text="Another test review.",
            ),
        ]
        
        formatted = analyzer._format_reviews(reviews)
        
        assert "[Review 1]" in formatted
        assert "[Review 2]" in formatted
        assert "test" in formatted
        assert "2 stars" in formatted
    
    def test_extract_json_from_code_block(self):
        """Test JSON extraction from markdown code block."""
        analyzer = PainPointAnalyzer.__new__(PainPointAnalyzer)
        
        text = '''Here is the analysis:

```json
[
  {
    "review_number": 1,
    "pain_point_category": "Too theoretical",
    "verbatim_quote": "Test quote",
    "emotional_intensity": "high",
    "implied_need": "Test need"
  }
]
```
'''
        
        json_text = analyzer._extract_json(text)
        assert json_text is not None
        assert "review_number" in json_text
    
    def test_extract_json_raw(self):
        """Test JSON extraction without code block."""
        analyzer = PainPointAnalyzer.__new__(PainPointAnalyzer)
        
        text = '''[{"review_number": 1, "pain_point_category": "Test", "verbatim_quote": "Quote", "emotional_intensity": "low", "implied_need": "Need"}]'''
        
        json_text = analyzer._extract_json(text)
        assert json_text is not None
        assert json_text.startswith("[")
    
    def test_parse_response(self):
        """Test parsing Claude response into pain points."""
        analyzer = PainPointAnalyzer.__new__(PainPointAnalyzer)
        
        response_text = '''[
  {
    "review_number": 1,
    "pain_point_category": "Too theoretical",
    "verbatim_quote": "I kept waiting for concrete examples",
    "emotional_intensity": "high",
    "implied_need": "Wants actionable guidance"
  },
  {
    "review_number": 2,
    "pain_point_category": "Repetitive",
    "verbatim_quote": "Same ideas recycled over and over",
    "emotional_intensity": "medium",
    "implied_need": "Wants more depth"
  }
]'''
        
        pain_points = analyzer._parse_response(response_text)
        
        assert len(pain_points) == 2
        assert pain_points[0].pain_point_category == "Too theoretical"
        assert pain_points[0].emotional_intensity == "high"
        assert pain_points[1].review_number == 2
    
    def test_parse_response_empty(self):
        """Test parsing empty or invalid response."""
        analyzer = PainPointAnalyzer.__new__(PainPointAnalyzer)
        
        # No JSON found
        pain_points = analyzer._parse_response("No JSON here")
        assert len(pain_points) == 0
        
        # Invalid JSON
        pain_points = analyzer._parse_response("[invalid json")
        assert len(pain_points) == 0
    
    def test_init_requires_api_key(self):
        """Test that initializing without API key raises error."""
        with pytest.raises(ValueError, match="API key"):
            PainPointAnalyzer("")
