"""Export functionality for pain points and reports."""

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.database import get_database
from src.models import PainPoint, Review


class Exporter:
    """Export pain points to various formats."""
    
    def __init__(self):
        self.db = get_database()
    
    def to_csv(
        self,
        output_path: str,
        category: Optional[str] = None,
    ) -> int:
        """
        Export pain points to CSV.
        Returns count of exported pain points.
        """
        pain_points_with_reviews = self.db.get_all_pain_points_with_reviews()
        
        if category:
            pain_points_with_reviews = [
                (pp, r) for pp, r in pain_points_with_reviews
                if pp.category.lower() == category.lower()
            ]
        
        if not pain_points_with_reviews:
            return 0
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "category",
                "verbatim_quote",
                "emotional_intensity",
                "implied_need",
                "source",
                "product_title",
                "rating",
                "review_date",
            ])
            
            for pp, review in pain_points_with_reviews:
                writer.writerow([
                    pp.category,
                    pp.verbatim_quote,
                    pp.emotional_intensity.value if hasattr(pp.emotional_intensity, 'value') else pp.emotional_intensity,
                    pp.implied_need or "",
                    review.source,
                    review.product_title or "",
                    review.rating or "",
                    review.review_date or "",
                ])
        
        return len(pain_points_with_reviews)
    
    def to_json(
        self,
        output_path: str,
        category: Optional[str] = None,
    ) -> int:
        """
        Export pain points to JSON.
        Returns count of exported pain points.
        """
        pain_points_with_reviews = self.db.get_all_pain_points_with_reviews()
        
        if category:
            pain_points_with_reviews = [
                (pp, r) for pp, r in pain_points_with_reviews
                if pp.category.lower() == category.lower()
            ]
        
        if not pain_points_with_reviews:
            return 0
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        data = []
        for pp, review in pain_points_with_reviews:
            data.append({
                "category": pp.category,
                "verbatim_quote": pp.verbatim_quote,
                "emotional_intensity": pp.emotional_intensity.value if hasattr(pp.emotional_intensity, 'value') else pp.emotional_intensity,
                "implied_need": pp.implied_need,
                "source": {
                    "platform": review.source,
                    "product_title": review.product_title,
                    "rating": review.rating,
                    "review_date": review.review_date,
                    "author": review.author,
                },
            })
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return len(data)
    
    def to_markdown(
        self,
        output_path: str,
        category: Optional[str] = None,
        include_summary: bool = True,
    ) -> int:
        """
        Export pain points to Markdown report.
        Returns count of exported pain points.
        """
        pain_points_with_reviews = self.db.get_all_pain_points_with_reviews()
        
        if category:
            pain_points_with_reviews = [
                (pp, r) for pp, r in pain_points_with_reviews
                if pp.category.lower() == category.lower()
            ]
        
        if not pain_points_with_reviews:
            return 0
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Group by category
        by_category: dict[str, list[tuple[PainPoint, Review]]] = defaultdict(list)
        for pp, review in pain_points_with_reviews:
            by_category[pp.category].append((pp, review))
        
        # Sort categories by count
        sorted_categories = sorted(by_category.items(), key=lambda x: -len(x[1]))
        
        # Count by intensity
        intensity_counts: dict[str, int] = defaultdict(int)
        for pp, _ in pain_points_with_reviews:
            intensity = pp.emotional_intensity.value if hasattr(pp.emotional_intensity, 'value') else pp.emotional_intensity
            intensity_counts[intensity] += 1
        
        # Build report
        lines = []
        lines.append("# Pain Point Analysis Report")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")
        
        if include_summary:
            lines.append("## Executive Summary")
            lines.append("")
            lines.append(f"- **Total Pain Points:** {len(pain_points_with_reviews)}")
            lines.append(f"- **Categories Identified:** {len(by_category)}")
            lines.append(f"- **High Intensity:** {intensity_counts.get('high', 0)}")
            lines.append(f"- **Medium Intensity:** {intensity_counts.get('medium', 0)}")
            lines.append(f"- **Low Intensity:** {intensity_counts.get('low', 0)}")
            lines.append("")
            
            # Top 5 categories summary
            lines.append("### Top Pain Point Categories")
            lines.append("")
            for cat, items in sorted_categories[:5]:
                pct = (len(items) / len(pain_points_with_reviews)) * 100
                lines.append(f"1. **{cat}** - {len(items)} instances ({pct:.1f}%)")
            lines.append("")
        
        # Detailed breakdown by category
        lines.append("---")
        lines.append("")
        lines.append("## Detailed Findings")
        lines.append("")
        
        for cat, items in sorted_categories:
            lines.append(f"### {cat}")
            lines.append("")
            lines.append(f"*{len(items)} pain points identified*")
            lines.append("")
            
            for pp, review in items:
                intensity = pp.emotional_intensity.value if hasattr(pp.emotional_intensity, 'value') else pp.emotional_intensity
                intensity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(intensity, "⚪")
                
                lines.append(f"> \"{pp.verbatim_quote}\"")
                lines.append(">")
                lines.append(f"> — *{review.source}*{f', {review.product_title}' if review.product_title else ''}{f', {review.rating}★' if review.rating else ''}")
                lines.append("")
                
                if pp.implied_need:
                    lines.append(f"**Implied Need:** {pp.implied_need}")
                    lines.append("")
                
                lines.append(f"**Intensity:** {intensity_emoji} {intensity.capitalize()}")
                lines.append("")
                lines.append("---")
                lines.append("")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return len(pain_points_with_reviews)
