"""SEO rule-based checks."""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def check_seo(html: str, text: str) -> dict:
    """Run all SEO rule checks on HTML content."""
    results = {"scores": {}, "issues": [], "metrics": {}}
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check title tag
        title_result = check_title_tag(soup)
        results["scores"]["title"] = title_result["score"]
        results["metrics"]["title_length"] = title_result["length"]
        results["issues"].extend(title_result["issues"])
        
        # Check meta description
        meta_result = check_meta_description(soup)
        results["scores"]["meta_description"] = meta_result["score"]
        results["metrics"]["meta_desc_length"] = meta_result["length"]
        results["issues"].extend(meta_result["issues"])
        
        # Check H1 tags
        h1_result = check_h1_tags(soup)
        results["scores"]["h1"] = h1_result["score"]
        results["metrics"]["h1_count"] = h1_result["count"]
        results["issues"].extend(h1_result["issues"])
        
        # Check canonical URL
        canonical_result = check_canonical(soup)
        results["scores"]["canonical"] = canonical_result["score"]
        results["issues"].extend(canonical_result["issues"])
        
        # Check word count
        word_count_result = check_word_count(text)
        results["scores"]["word_count"] = word_count_result["score"]
        results["metrics"]["word_count"] = word_count_result["count"]
        results["issues"].extend(word_count_result["issues"])
        
        # Calculate overall SEO score
        scores = list(results["scores"].values())
        results["overall_score"] = sum(scores) / len(scores) if scores else 0
        
    except Exception as e:
        logger.error(f"Error running SEO checks: {e}")
        results["error"] = str(e)
    
    return results


def check_title_tag(soup: BeautifulSoup) -> dict:
    """Check title tag length and presence."""
    result = {"score": 0, "length": 0, "issues": []}
    
    title_tag = soup.find('title')
    if not title_tag:
        result["issues"].append("Missing title tag")
        return result
    
    title_text = title_tag.get_text(strip=True)
    result["length"] = len(title_text)
    
    if result["length"] == 0:
        result["issues"].append("Empty title tag")
    elif result["length"] < 30:
        result["score"] = 50
        result["issues"].append(f"Title too short ({result['length']} chars, recommended 30-60)")
    elif result["length"] > 60:
        result["score"] = 75
        result["issues"].append(f"Title too long ({result['length']} chars, recommended 30-60)")
    else:
        result["score"] = 100
    
    return result


def check_meta_description(soup: BeautifulSoup) -> dict:
    """Check meta description length and presence."""
    result = {"score": 0, "length": 0, "issues": []}
    
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if not meta_desc or not meta_desc.get('content'):
        result["issues"].append("Missing meta description")
        return result
    
    desc_text = meta_desc['content']
    result["length"] = len(desc_text)
    
    if result["length"] == 0:
        result["issues"].append("Empty meta description")
    elif result["length"] < 120:
        result["score"] = 50
        result["issues"].append(f"Meta description too short ({result['length']} chars, recommended 120-160)")
    elif result["length"] > 160:
        result["score"] = 75
        result["issues"].append(f"Meta description too long ({result['length']} chars, recommended 120-160)")
    else:
        result["score"] = 100
    
    return result


def check_h1_tags(soup: BeautifulSoup) -> dict:
    """Check H1 tag presence and uniqueness."""
    result = {"score": 0, "count": 0, "issues": []}
    
    h1_tags = soup.find_all('h1')
    result["count"] = len(h1_tags)
    
    if result["count"] == 0:
        result["issues"].append("Missing H1 tag")
    elif result["count"] > 1:
        result["score"] = 75
        result["issues"].append(f"Multiple H1 tags found ({result['count']}, recommended 1)")
    else:
        result["score"] = 100
    
    return result


def check_canonical(soup: BeautifulSoup) -> dict:
    """Check for canonical URL presence."""
    result = {"score": 0, "issues": []}
    
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if not canonical or not canonical.get('href'):
        result["issues"].append("Missing canonical URL")
    else:
        result["score"] = 100
    
    return result


def check_word_count(text: str) -> dict:
    """Check content word count."""
    result = {"score": 0, "count": 0, "issues": []}
    
    words = text.split()
    result["count"] = len(words)
    
    if result["count"] < 300:
        result["score"] = 25
        result["issues"].append(f"Low word count ({result['count']}, recommended 300+)")
    elif result["count"] < 600:
        result["score"] = 75
    else:
        result["score"] = 100
    
    return result
