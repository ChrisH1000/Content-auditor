"""Accessibility rule-based checks."""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def check_a11y(html: str, text: str) -> dict:
    """Run all accessibility rule checks on HTML content."""
    results = {"scores": {}, "issues": [], "metrics": {}}
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check image alt attributes
        img_result = check_image_alts(soup)
        results["scores"]["image_alts"] = img_result["score"]
        results["metrics"]["images_total"] = img_result["total"]
        results["metrics"]["images_with_alt"] = img_result["with_alt"]
        results["issues"].extend(img_result["issues"])
        
        # Check heading hierarchy
        heading_result = check_heading_hierarchy(soup)
        results["scores"]["heading_hierarchy"] = heading_result["score"]
        results["issues"].extend(heading_result["issues"])
        
        # Check link text
        link_result = check_link_text(soup)
        results["scores"]["link_text"] = link_result["score"]
        results["metrics"]["links_total"] = link_result["total"]
        results["metrics"]["links_with_text"] = link_result["with_text"]
        results["issues"].extend(link_result["issues"])
        
        # Calculate overall A11y score
        scores = list(results["scores"].values())
        results["overall_score"] = sum(scores) / len(scores) if scores else 0
        
    except Exception as e:
        logger.error(f"Error running A11y checks: {e}")
        results["error"] = str(e)
    
    return results


def check_image_alts(soup: BeautifulSoup) -> dict:
    """Check image alt attributes."""
    result = {"score": 0, "total": 0, "with_alt": 0, "issues": []}
    
    images = soup.find_all('img')
    result["total"] = len(images)
    
    if result["total"] == 0:
        result["score"] = 100
        return result
    
    for img in images:
        if img.get('alt') is not None:
            result["with_alt"] += 1
    
    alt_percentage = (result["with_alt"] / result["total"]) * 100 if result["total"] > 0 else 0
    
    if alt_percentage == 100:
        result["score"] = 100
    elif alt_percentage >= 80:
        result["score"] = 75
        result["issues"].append(
            f"{result['total'] - result['with_alt']} images missing alt text "
            f"({alt_percentage:.1f}% have alt)"
        )
    elif alt_percentage >= 50:
        result["score"] = 50
        result["issues"].append(
            f"{result['total'] - result['with_alt']} images missing alt text "
            f"({alt_percentage:.1f}% have alt)"
        )
    else:
        result["score"] = 25
        result["issues"].append(
            f"{result['total'] - result['with_alt']} images missing alt text "
            f"({alt_percentage:.1f}% have alt)"
        )
    
    return result


def check_heading_hierarchy(soup: BeautifulSoup) -> dict:
    """Check heading hierarchy order."""
    result = {"score": 100, "issues": []}
    
    headings = []
    for level in range(1, 7):
        for heading in soup.find_all(f'h{level}'):
            headings.append(level)
    
    if not headings:
        result["score"] = 50
        result["issues"].append("No headings found")
        return result
    
    # Check if headings skip levels
    for i in range(len(headings) - 1):
        if headings[i+1] - headings[i] > 1:
            result["score"] = 50
            result["issues"].append(
                f"Heading hierarchy skips from H{headings[i]} to H{headings[i+1]}"
            )
            break
    
    return result


def check_link_text(soup: BeautifulSoup) -> dict:
    """Check link text quality."""
    result = {"score": 0, "total": 0, "with_text": 0, "issues": []}
    
    links = soup.find_all('a')
    result["total"] = len(links)
    
    if result["total"] == 0:
        result["score"] = 100
        return result
    
    generic_phrases = ['click here', 'read more', 'here', 'more', 'link']
    generic_count = 0
    
    for link in links:
        text = link.get_text(strip=True).lower()
        if text:
            result["with_text"] += 1
            if text in generic_phrases:
                generic_count += 1
    
    text_percentage = (result["with_text"] / result["total"]) * 100 if result["total"] > 0 else 0
    
    if text_percentage < 80:
        result["score"] = 25
        result["issues"].append(
            f"{result['total'] - result['with_text']} links without text "
            f"({text_percentage:.1f}% have text)"
        )
    elif generic_count > result["total"] * 0.2:
        result["score"] = 50
        result["issues"].append(
            f"{generic_count} links use generic text (e.g., 'click here', 'read more')"
        )
    else:
        result["score"] = 100
    
    return result
