"""Tests for scrapers."""

import pytest
from pathlib import Path

from src.scrapers.csv_import import CSVImporter, import_reviews


class TestCSVImporter:
    """Tests for CSV import functionality."""
    
    def test_import_csv(self, tmp_path):
        """Test importing reviews from CSV file."""
        csv_content = """source,product_title,rating,review_text,review_date
test,Test Book,2,This is a test review with enough content to pass the minimum length requirement for reviews.,2024-01-15
test,Another Book,3,Another test review that also needs to be long enough to be considered valid content.,2024-01-16
"""
        csv_file = tmp_path / "test_reviews.csv"
        csv_file.write_text(csv_content)
        
        importer = CSVImporter()
        reviews = importer.import_csv(str(csv_file))
        
        assert len(reviews) == 2
        assert reviews[0].source == "test"
        assert reviews[0].product_title == "Test Book"
        assert reviews[0].rating == 2
        assert "test review" in reviews[0].review_text
    
    def test_import_json(self, tmp_path):
        """Test importing reviews from JSON file."""
        json_content = """[
    {
        "source": "test",
        "product_title": "Test Book",
        "rating": 2,
        "review_text": "This is a test review with enough content to pass the minimum length requirement.",
        "review_date": "2024-01-15"
    }
]"""
        json_file = tmp_path / "test_reviews.json"
        json_file.write_text(json_content)
        
        importer = CSVImporter()
        reviews = importer.import_json(str(json_file))
        
        assert len(reviews) == 1
        assert reviews[0].source == "test"
        assert reviews[0].rating == 2
    
    def test_import_sample_json(self):
        """Test importing the sample reviews JSON file."""
        sample_file = Path("tests/sample_reviews.json")
        if sample_file.exists():
            reviews = import_reviews(str(sample_file))
            assert len(reviews) == 3
            assert all(r.rating in [1, 2] for r in reviews)
    
    def test_import_missing_file(self):
        """Test handling of missing file."""
        importer = CSVImporter()
        with pytest.raises(FileNotFoundError):
            importer.import_csv("nonexistent.csv")
    
    def test_import_empty_reviews_skipped(self, tmp_path):
        """Test that empty reviews are skipped."""
        csv_content = """source,product_title,rating,review_text,review_date
test,Test Book,2,,2024-01-15
test,Another Book,3,Valid review content that is long enough.,2024-01-16
"""
        csv_file = tmp_path / "test_reviews.csv"
        csv_file.write_text(csv_content)
        
        importer = CSVImporter()
        reviews = importer.import_csv(str(csv_file))
        
        assert len(reviews) == 1
        assert reviews[0].product_title == "Another Book"
