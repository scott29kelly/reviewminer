"""CSV import functionality for manual review data entry."""

import csv
import json
from pathlib import Path
from typing import List, Optional

from src.models import Review


class CSVImporter:
    """Import reviews from CSV or JSON files."""
    
    source_name: str = "csv_import"
    
    # Expected CSV columns
    REQUIRED_COLUMNS = {"review_text"}
    OPTIONAL_COLUMNS = {
        "source",
        "product_title",
        "product_url",
        "source_url",
        "author",
        "rating",
        "review_date",
    }
    
    def import_csv(self, file_path: str, default_source: str = "manual") -> List[Review]:
        """
        Import reviews from a CSV file.
        
        Expected CSV format:
        source,product_title,rating,review_text,review_date
        
        Only review_text is required. Other columns are optional.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        reviews = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Validate columns
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or has no headers")
            
            columns = set(reader.fieldnames)
            if "review_text" not in columns:
                raise ValueError("CSV must contain 'review_text' column")
            
            for row in reader:
                review_text = row.get("review_text", "").strip()
                if not review_text:
                    continue  # Skip empty reviews
                
                # Parse rating if present
                rating = None
                if row.get("rating"):
                    try:
                        rating = int(row["rating"])
                        if not 1 <= rating <= 5:
                            rating = None
                    except ValueError:
                        pass
                
                review = Review(
                    source=row.get("source", default_source) or default_source,
                    source_url=row.get("source_url"),
                    product_title=row.get("product_title"),
                    product_url=row.get("product_url"),
                    author=row.get("author"),
                    rating=rating,
                    review_text=review_text,
                    review_date=row.get("review_date"),
                )
                reviews.append(review)
        
        return reviews
    
    def import_json(self, file_path: str, default_source: str = "manual") -> List[Review]:
        """
        Import reviews from a JSON file.
        
        Expected JSON format (array of objects):
        [
            {
                "source": "test",
                "product_title": "Book Title",
                "rating": 2,
                "review_text": "The review content...",
                "review_date": "2024-01-15"
            }
        ]
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON file must contain an array of review objects")
        
        reviews = []
        for item in data:
            review_text = item.get("review_text", "").strip()
            if not review_text:
                continue
            
            # Parse rating if present
            rating = item.get("rating")
            if rating is not None:
                try:
                    rating = int(rating)
                    if not 1 <= rating <= 5:
                        rating = None
                except (ValueError, TypeError):
                    rating = None
            
            review = Review(
                source=item.get("source", default_source) or default_source,
                source_url=item.get("source_url"),
                product_title=item.get("product_title"),
                product_url=item.get("product_url"),
                author=item.get("author"),
                rating=rating,
                review_text=review_text,
                review_date=item.get("review_date"),
            )
            reviews.append(review)
        
        return reviews
    
    def import_file(self, file_path: str, default_source: str = "manual") -> List[Review]:
        """Import reviews from a file, auto-detecting format by extension."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == ".csv":
            return self.import_csv(file_path, default_source)
        elif suffix == ".json":
            return self.import_json(file_path, default_source)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .json")


def import_reviews(file_path: str, default_source: str = "manual") -> List[Review]:
    """Convenience function to import reviews from a file."""
    importer = CSVImporter()
    return importer.import_file(file_path, default_source)
