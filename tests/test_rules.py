"""Basic tests for rule checking functionality."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules.seo_rules import check_seo, check_title_tag, check_meta_description, check_h1_tags
from rules.a11y_rules import check_a11y, check_image_alts, check_link_text


def test_seo_rules():
    """Test SEO rule checks."""
    html = """
    <html>
    <head>
        <title>This is a good title length for SEO testing</title>
        <meta name="description" content="This is a meta description that should be between 120 and 160 characters long to meet SEO best practices for search engines.">
        <link rel="canonical" href="https://example.com/page">
    </head>
    <body>
        <h1>Main Heading</h1>
        <p>""" + " ".join(["word"] * 400) + """</p>
    </body>
    </html>
    """
    
    text = " ".join(["word"] * 400)
    
    results = check_seo(html, text)
    
    assert "overall_score" in results
    assert results["overall_score"] > 0
    assert "scores" in results
    assert "title" in results["scores"]
    assert "meta_description" in results["scores"]
    assert "h1" in results["scores"]
    
    print(f"✓ SEO checks passed - Overall score: {results['overall_score']:.1f}")
    print(f"  Title score: {results['scores']['title']}")
    print(f"  Meta desc score: {results['scores']['meta_description']}")
    print(f"  H1 score: {results['scores']['h1']}")
    return results


def test_a11y_rules():
    """Test accessibility rule checks."""
    html = """
    <html>
    <body>
        <h1>Main Title</h1>
        <h2>Subtitle</h2>
        <h3>Section</h3>
        <img src="image1.jpg" alt="Description 1">
        <img src="image2.jpg" alt="Description 2">
        <a href="/page1">Link with good text</a>
        <a href="/page2">Another descriptive link</a>
    </body>
    </html>
    """
    
    text = "Main Title Subtitle Section"
    
    results = check_a11y(html, text)
    
    assert "overall_score" in results
    assert results["overall_score"] > 0
    assert "scores" in results
    assert "image_alts" in results["scores"]
    assert "heading_hierarchy" in results["scores"]
    
    print(f"✓ A11y checks passed - Overall score: {results['overall_score']:.1f}")
    print(f"  Image alts score: {results['scores']['image_alts']}")
    print(f"  Heading hierarchy score: {results['scores']['heading_hierarchy']}")
    print(f"  Link text score: {results['scores']['link_text']}")
    return results


def test_poor_seo():
    """Test SEO rules with poor content."""
    html = "<html><body><p>Short content</p></body></html>"
    text = "Short content"
    
    results = check_seo(html, text)
    
    assert len(results["issues"]) > 0
    print(f"✓ Poor SEO detection passed - Found {len(results['issues'])} issues")
    for issue in results["issues"]:
        print(f"  - {issue}")
    return results


def test_poor_a11y():
    """Test A11y rules with poor content."""
    html = """
    <html>
    <body>
        <img src="no-alt.jpg">
        <a href="/page">click here</a>
    </body>
    </html>
    """
    text = "click here"
    
    results = check_a11y(html, text)
    
    assert len(results["issues"]) > 0
    print(f"✓ Poor A11y detection passed - Found {len(results['issues'])} issues")
    for issue in results["issues"]:
        print(f"  - {issue}")
    return results


if __name__ == "__main__":
    print("Running rule-based tests...\n")
    
    try:
        test_seo_rules()
        print()
        test_a11y_rules()
        print()
        test_poor_seo()
        print()
        test_poor_a11y()
        print()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
