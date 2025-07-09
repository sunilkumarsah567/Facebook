import re
from datetime import datetime
from urllib.parse import urlparse
import json

class SEOOptimizer:
    """SEO optimization utilities for blog content"""
    
    def __init__(self):
        self.max_title_length = 60
        self.max_description_length = 160
        self.min_content_length = 300
    
    def generate_seo_metadata(self, title, content, image_url=None):
        """Generate comprehensive SEO metadata for a blog post"""
        try:
            # Optimize title
            seo_title = self.optimize_title(title)
            
            # Generate meta description
            meta_description = self.generate_meta_description(content)
            
            # Extract keywords
            keywords = self.extract_keywords(title, content)
            
            # Generate schema markup
            schema_markup = self.generate_schema_markup(seo_title, meta_description, image_url)
            
            # Generate Open Graph tags
            og_tags = self.generate_open_graph_tags(seo_title, meta_description, image_url)
            
            # Generate Twitter Card tags
            twitter_tags = self.generate_twitter_tags(seo_title, meta_description, image_url)
            
            return {
                'seo_title': seo_title,
                'meta_description': meta_description,
                'keywords': keywords,
                'schema_markup': schema_markup,
                'og_tags': og_tags,
                'twitter_tags': twitter_tags,
                'canonical_url': '',
                'robots': 'index, follow',
                'reading_time': self.calculate_reading_time(content)
            }
            
        except Exception as e:
            print(f"Error generating SEO metadata: {e}")
            return self.get_default_seo_metadata(title)
    
    def optimize_title(self, title):
        """Optimize title for SEO"""
        try:
            # Remove extra whitespace and clean up
            clean_title = re.sub(r'\s+', ' ', title.strip())
            
            # Truncate if too long
            if len(clean_title) > self.max_title_length:
                # Try to truncate at word boundary
                truncated = clean_title[:self.max_title_length]
                last_space = truncated.rfind(' ')
                if last_space > self.max_title_length * 0.8:  # If we can save significant characters
                    clean_title = truncated[:last_space]
                else:
                    clean_title = truncated
            
            return clean_title
            
        except Exception as e:
            print(f"Error optimizing title: {e}")
            return title[:self.max_title_length]
    
    def generate_meta_description(self, content):
        """Generate meta description from content"""
        try:
            if isinstance(content, list):
                # If content is a list of sections, combine them
                text_content = ' '.join([section[1] if isinstance(section, tuple) else str(section) for section in content])
            else:
                text_content = str(content)
            
            # Clean up the text
            clean_text = re.sub(r'<[^>]+>', '', text_content)  # Remove HTML tags
            clean_text = re.sub(r'\s+', ' ', clean_text)  # Normalize whitespace
            clean_text = clean_text.strip()
            
            # Extract first meaningful sentence(s)
            sentences = clean_text.split('. ')
            description = ''
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Add sentence if it doesn't make description too long
                test_desc = description + sentence + '. ' if description else sentence + '. '
                if len(test_desc) <= self.max_description_length:
                    description = test_desc
                else:
                    break
            
            # If description is still too long, truncate
            if len(description) > self.max_description_length:
                description = description[:self.max_description_length - 3] + '...'
            
            # Ensure description ends properly
            description = description.strip()
            if not description.endswith('.') and not description.endswith('...'):
                description += '.'
            
            return description
            
        except Exception as e:
            print(f"Error generating meta description: {e}")
            return "Discover insights and information on this important topic."
    
    def extract_keywords(self, title, content, max_keywords=10):
        """Extract relevant keywords from title and content"""
        try:
            # Combine title and content
            if isinstance(content, list):
                text_content = ' '.join([section[1] if isinstance(section, tuple) else str(section) for section in content])
            else:
                text_content = str(content)
            
            full_text = f"{title} {text_content}".lower()
            
            # Clean text
            clean_text = re.sub(r'[^\w\s]', ' ', full_text)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            
            # Common stop words to exclude
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
                'his', 'her', 'its', 'our', 'their', 'into', 'from', 'up', 'down', 'out', 'off', 'over',
                'under', 'again', 'further', 'then', 'once', 'more', 'also', 'very', 'just', 'here', 'there',
                'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
                'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'can', 'will'
            }
            
            # Extract words and count frequency
            words = clean_text.split()
            word_freq = {}
            
            for word in words:
                word = word.strip()
                if len(word) > 2 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and take top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return ', '.join(keywords)
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return title.lower()
    
    def generate_schema_markup(self, title, description, image_url=None):
        """Generate JSON-LD schema markup for the article"""
        try:
            schema = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": title,
                "description": description,
                "datePublished": datetime.now().isoformat(),
                "dateModified": datetime.now().isoformat(),
                "author": {
                    "@type": "Organization",
                    "name": "AutoBlog Generator"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "AutoBlog Generator",
                    "logo": {
                        "@type": "ImageObject",
                        "url": "https://example.com/logo.png"
                    }
                }
            }
            
            if image_url:
                schema["image"] = {
                    "@type": "ImageObject",
                    "url": image_url,
                    "width": 800,
                    "height": 600
                }
            
            return json.dumps(schema, indent=2)
            
        except Exception as e:
            print(f"Error generating schema markup: {e}")
            return "{}"
    
    def generate_open_graph_tags(self, title, description, image_url=None):
        """Generate Open Graph meta tags"""
        try:
            og_tags = [
                f'<meta property="og:type" content="article">',
                f'<meta property="og:title" content="{self.escape_html(title)}">',
                f'<meta property="og:description" content="{self.escape_html(description)}">',
                f'<meta property="og:site_name" content="AutoBlog Generator">',
                f'<meta property="article:published_time" content="{datetime.now().isoformat()}">',
                f'<meta property="article:author" content="AutoBlog Generator">'
            ]
            
            if image_url:
                og_tags.extend([
                    f'<meta property="og:image" content="{image_url}">',
                    f'<meta property="og:image:width" content="800">',
                    f'<meta property="og:image:height" content="600">',
                    f'<meta property="og:image:alt" content="{self.escape_html(title)}">'
                ])
            
            return '\n    '.join(og_tags)
            
        except Exception as e:
            print(f"Error generating Open Graph tags: {e}")
            return ""
    
    def generate_twitter_tags(self, title, description, image_url=None):
        """Generate Twitter Card meta tags"""
        try:
            twitter_tags = [
                f'<meta name="twitter:card" content="summary_large_image">',
                f'<meta name="twitter:title" content="{self.escape_html(title)}">',
                f'<meta name="twitter:description" content="{self.escape_html(description)}">',
                f'<meta name="twitter:creator" content="@autoblog">'
            ]
            
            if image_url:
                twitter_tags.append(f'<meta name="twitter:image" content="{image_url}">')
            
            return '\n    '.join(twitter_tags)
            
        except Exception as e:
            print(f"Error generating Twitter tags: {e}")
            return ""
    
    def calculate_reading_time(self, content, words_per_minute=200):
        """Calculate estimated reading time"""
        try:
            if isinstance(content, list):
                text_content = ' '.join([section[1] if isinstance(section, tuple) else str(section) for section in content])
            else:
                text_content = str(content)
            
            # Clean text and count words
            clean_text = re.sub(r'<[^>]+>', '', text_content)  # Remove HTML
            words = len(clean_text.split())
            
            # Calculate reading time
            reading_time = max(1, round(words / words_per_minute))
            
            return reading_time
            
        except Exception as e:
            print(f"Error calculating reading time: {e}")
            return 1
    
    def escape_html(self, text):
        """Escape HTML special characters"""
        try:
            return (text.replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;')
                       .replace('"', '&quot;')
                       .replace("'", '&#x27;'))
        except Exception as e:
            print(f"Error escaping HTML: {e}")
            return str(text)
    
    def get_default_seo_metadata(self, title):
        """Get default SEO metadata when generation fails"""
        return {
            'seo_title': title[:self.max_title_length],
            'meta_description': "Discover insights and information on this important topic.",
            'keywords': title.lower(),
            'schema_markup': "{}",
            'og_tags': "",
            'twitter_tags': "",
            'canonical_url': "",
            'robots': 'index, follow',
            'reading_time': 1
        }
    
    def optimize_content_structure(self, content_sections):
        """Optimize content structure for SEO"""
        try:
            optimized_sections = []
            
            for i, (heading, content) in enumerate(content_sections):
                # Determine heading level
                if i == 0:
                    heading_tag = 'h2'  # H1 is reserved for main title
                elif heading.lower() in ['introduction', 'overview']:
                    heading_tag = 'h2'
                elif heading.lower() == 'conclusion':
                    heading_tag = 'h2'
                else:
                    heading_tag = 'h3'
                
                # Optimize content for readability
                optimized_content = self.optimize_content_readability(content)
                
                optimized_sections.append((heading, optimized_content, heading_tag))
            
            return optimized_sections
            
        except Exception as e:
            print(f"Error optimizing content structure: {e}")
            return [(heading, content, 'h3') for heading, content in content_sections]
    
    def optimize_content_readability(self, content):
        """Optimize content for better readability"""
        try:
            # Split long paragraphs
            paragraphs = content.split('\n\n')
            optimized_paragraphs = []
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # If paragraph is too long, try to split it
                if len(paragraph) > 300:
                    sentences = paragraph.split('. ')
                    current_para = ""
                    
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        
                        test_para = current_para + sentence + '. ' if current_para else sentence + '. '
                        
                        if len(test_para) > 250 and current_para:
                            optimized_paragraphs.append(current_para.strip())
                            current_para = sentence + '. '
                        else:
                            current_para = test_para
                    
                    if current_para:
                        optimized_paragraphs.append(current_para.strip())
                else:
                    optimized_paragraphs.append(paragraph)
            
            return '\n\n'.join(optimized_paragraphs)
            
        except Exception as e:
            print(f"Error optimizing content readability: {e}")
            return content
