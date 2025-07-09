import requests
import feedparser
import json
import os
from datetime import datetime, timezone
import re
import random
from urllib.parse import urlparse, quote
from config import Config
from seo_optimizer import SEOOptimizer
from web_scraper import get_website_text_content
import trafilatura
from jinja2 import Environment, FileSystemLoader

class ContentGenerator:
    def __init__(self):
        self.config = Config()
        self.seo_optimizer = SEOOptimizer()
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        
    def get_trending_topics(self, language='english', count=10):
        """Fetch trending topics from Google Trends RSS feeds with enhanced capacity"""
        try:
            feed_url = self.config.GOOGLE_TRENDS_FEEDS.get(language, self.config.GOOGLE_TRENDS_FEEDS['english'])
            
            print(f"Fetching trends from: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            topics = []
            
            if feed.entries:
                # Process all available entries, not just limited count
                for entry in feed.entries:
                    # Extract the search term from the title
                    title = entry.title
                    # Remove numbers and clean up the title
                    clean_title = re.sub(r'^\d+\.\s*', '', title)
                    topics.append({
                        'title': clean_title,
                        'description': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', '')
                    })
            
            # If we don't have enough from trends, supplement with news
            if len(topics) < count:
                print(f"Got {len(topics)} trends, fetching additional from news...")
                additional_needed = count - len(topics)
                news_topics = self.get_news_topics(language, additional_needed)
                topics.extend(news_topics)
            
            # Also add fallback topics to ensure we have enough variety
            if len(topics) < count:
                print(f"Still need more topics, adding fallback topics...")
                fallback_needed = count - len(topics)
                fallback_topics = self.generate_fallback_topics(fallback_needed)
                topics.extend(fallback_topics)
            
            return topics[:count]  # Return exactly the requested count
            
        except Exception as e:
            print(f"Error fetching Google Trends: {e}")
            return self.get_news_topics(language, count)
    
    def get_news_topics(self, language='english', count=10):
        """Backup method to fetch topics from news RSS feeds"""
        try:
            feeds = self.config.NEWS_RSS_FEEDS.get(language, self.config.NEWS_RSS_FEEDS['english'])
            topics = []
            
            for feed_url in feeds:
                try:
                    print(f"Fetching news from: {feed_url}")
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:count//len(feeds) + 1]:
                        if len(topics) >= count:
                            break
                            
                        topics.append({
                            'title': entry.title,
                            'description': entry.get('summary', entry.get('description', '')),
                            'link': entry.get('link', ''),
                            'published': entry.get('published', '')
                        })
                except Exception as e:
                    print(f"Error fetching from {feed_url}: {e}")
                    continue
            
            return topics[:count]
            
        except Exception as e:
            print(f"Error fetching news topics: {e}")
            return self.generate_fallback_topics(count)
    
    def generate_fallback_topics(self, count=5):
        """Generate fallback topics when APIs fail"""
        fallback_topics = [
            "Latest Technology Trends in 2025",
            "Health and Wellness Tips for Modern Life",
            "Digital Marketing Strategies That Work",
            "Sustainable Living Practices",
            "Remote Work Best Practices",
            "Financial Planning and Investment Advice",
            "Top Travel Destinations This Year",
            "Easy Cooking Recipes and Food Tips",
            "Fitness and Exercise Routines",
            "Home Improvement DIY Projects",
            "Artificial Intelligence and Machine Learning",
            "Cybersecurity Best Practices",
            "Electric Vehicles and Green Technology",
            "Social Media Marketing Trends",
            "Mental Health and Mindfulness",
            "Small Business Growth Strategies",
            "Photography Tips and Techniques",
            "Online Education and E-learning",
            "Cryptocurrency and Blockchain News",
            "Environmental Conservation Methods"
        ]
        
        # Ensure we have enough unique topics
        selected_topics = random.sample(fallback_topics, min(count, len(fallback_topics)))
        return [{'title': topic, 'description': f'Comprehensive guide and latest updates about {topic.lower()}', 'link': '', 'published': ''} for topic in selected_topics]
    
    def research_topic(self, topic_title, topic_description):
        """Research a topic using Wikipedia and web scraping"""
        try:
            # Search Wikipedia for the topic
            wikipedia_content = self.search_wikipedia(topic_title)
            
            # Generate content based on research
            content = self.generate_article_content(topic_title, topic_description, wikipedia_content)
            
            return content
            
        except Exception as e:
            print(f"Error researching topic '{topic_title}': {e}")
            return self.generate_basic_content(topic_title, topic_description)
    
    def search_wikipedia(self, query):
        """Search Wikipedia for information about a topic"""
        try:
            # Wikipedia API search
            search_url = f"https://en.wikipedia.org/w/api.php"
            search_params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 3
            }
            
            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()
            search_data = response.json()
            
            if 'query' in search_data and 'search' in search_data['query']:
                search_results = search_data['query']['search']
                
                if search_results:
                    # Get the first result's content
                    page_title = search_results[0]['title']
                    content_url = f"https://en.wikipedia.org/w/api.php"
                    content_params = {
                        'action': 'query',
                        'format': 'json',
                        'titles': page_title,
                        'prop': 'extracts',
                        'exintro': True,
                        'explaintext': True,
                        'exsectionformat': 'plain'
                    }
                    
                    content_response = requests.get(content_url, params=content_params, timeout=10)
                    content_response.raise_for_status()
                    content_data = content_response.json()
                    
                    pages = content_data.get('query', {}).get('pages', {})
                    for page_id, page_info in pages.items():
                        extract = page_info.get('extract', '')
                        if extract:
                            return extract[:1000]  # Limit to 1000 characters
            
            return ""
            
        except Exception as e:
            print(f"Error searching Wikipedia: {e}")
            return ""
    
    def generate_article_content(self, title, description, research_content):
        """Generate article content based on title, description, and research"""
        # Create structured content
        content_sections = []
        
        # Introduction
        intro = f"In today's rapidly evolving world, {title.lower()} has become increasingly important. "
        if description:
            intro += f"{description} "
        
        if research_content:
            # Use first part of research as introduction context
            research_intro = research_content[:200] + "..." if len(research_content) > 200 else research_content
            intro += f"\n\n{research_intro}"
        
        content_sections.append(("Introduction", intro))
        
        # Main content sections
        sections = [
            ("Key Points", self.generate_key_points(title, research_content)),
            ("Important Considerations", self.generate_considerations(title)),
            ("Practical Applications", self.generate_applications(title)),
            ("Future Outlook", self.generate_future_outlook(title))
        ]
        
        content_sections.extend(sections)
        
        # Conclusion
        conclusion = f"In conclusion, {title.lower()} represents a significant area of interest and development. "
        conclusion += "Understanding its various aspects can help individuals and organizations make informed decisions. "
        conclusion += "As we move forward, staying updated with the latest developments in this field will be crucial for success."
        
        content_sections.append(("Conclusion", conclusion))
        
        return content_sections
    
    def generate_key_points(self, title, research_content):
        """Generate key points for the article"""
        points = [
            f"Understanding the fundamentals of {title.lower()} is essential for anyone interested in this topic.",
            f"Recent developments in {title.lower()} have shown promising results and potential for growth.",
            f"The impact of {title.lower()} extends beyond immediate applications to long-term implications."
        ]
        
        if research_content:
            # Extract key information from research
            sentences = research_content.split('. ')
            if len(sentences) > 3:
                points.append(sentences[1] + ".")
        
        return "\n\n".join([f"• {point}" for point in points])
    
    def generate_considerations(self, title):
        """Generate important considerations section"""
        considerations = [
            f"When examining {title.lower()}, it's important to consider multiple perspectives and viewpoints.",
            f"The complexity of {title.lower()} requires careful analysis and understanding of underlying factors.",
            f"Stakeholders should evaluate both benefits and potential challenges associated with {title.lower()}."
        ]
        
        return "\n\n".join([f"• {consideration}" for consideration in considerations])
    
    def generate_applications(self, title):
        """Generate practical applications section"""
        applications = [
            f"Real-world applications of {title.lower()} can be found across various industries and sectors.",
            f"Organizations are increasingly adopting strategies related to {title.lower()} to improve their operations.",
            f"Individual practitioners can benefit from implementing best practices associated with {title.lower()}."
        ]
        
        return "\n\n".join([f"• {application}" for application in applications])
    
    def generate_future_outlook(self, title):
        """Generate future outlook section"""
        outlook = f"The future of {title.lower()} looks promising with continued research and development. "
        outlook += f"Emerging trends suggest that {title.lower()} will play an increasingly important role in shaping future developments. "
        outlook += f"Investment in {title.lower()} is expected to grow as more organizations recognize its potential value and impact."
        
        return outlook
    
    def generate_basic_content(self, title, description):
        """Generate basic content when research fails"""
        content_sections = [
            ("Introduction", f"{title} is an important topic that deserves attention and understanding. {description}"),
            ("Overview", f"This article provides insights into {title.lower()} and its various aspects."),
            ("Key Benefits", f"Understanding {title.lower()} can provide valuable benefits and insights."),
            ("Conclusion", f"In summary, {title.lower()} represents an area of significant interest and potential.")
        ]
        
        return content_sections
    
    def get_unsplash_image(self, query):
        """Fetch an image from Unsplash API"""
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {
                "Authorization": f"Client-ID {self.config.UNSPLASH_ACCESS_KEY}"
            }
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    photo = data['results'][0]
                    return {
                        'url': photo['urls']['regular'],
                        'alt': photo.get('alt_description', query),
                        'author': photo['user']['name'],
                        'author_url': photo['user']['links']['html']
                    }
            
            # Fallback to placeholder
            return {
                'url': f"https://via.placeholder.com/{self.config.IMAGE_WIDTH}x{self.config.IMAGE_HEIGHT}/4A90E2/FFFFFF?text={quote(query)}",
                'alt': query,
                'author': 'Placeholder',
                'author_url': '#'
            }
            
        except Exception as e:
            print(f"Error fetching Unsplash image: {e}")
            return {
                'url': f"https://via.placeholder.com/{self.config.IMAGE_WIDTH}x{self.config.IMAGE_HEIGHT}/4A90E2/FFFFFF?text={quote(query)}",
                'alt': query,
                'author': 'Placeholder',
                'author_url': '#'
            }
    
    def generate_blog_posts(self, count=5, language='english'):
        """Generate blog posts from trending topics"""
        try:
            print(f"Starting blog generation - Count: {count}, Language: {language}")
            
            # Get trending topics
            topics = self.get_trending_topics(language, count)
            if not topics:
                return {
                    'success': False,
                    'message': 'No trending topics found',
                    'posts': []
                }
            
            generated_posts = []
            
            for i, topic in enumerate(topics):
                try:
                    print(f"Generating post {i+1}/{len(topics)}: {topic['title']}")
                    
                    # Research the topic
                    content_sections = self.research_topic(topic['title'], topic.get('description', ''))
                    
                    # Get image for the topic
                    image_data = self.get_unsplash_image(topic['title'])
                    
                    # Create the blog post
                    post_data = {
                        'title': topic['title'],
                        'description': topic.get('description', ''),
                        'content_sections': content_sections,
                        'image': image_data,
                        'published_date': datetime.now(timezone.utc).isoformat(),
                        'author': self.config.AUTHOR_NAME,
                        'source_link': topic.get('link', ''),
                        'language': language
                    }
                    
                    # Generate SEO-optimized HTML
                    html_content = self.create_blog_html(post_data)
                    
                    # Save the blog post
                    filename = self.save_blog_post(post_data['title'], html_content)
                    
                    generated_posts.append({
                        'title': post_data['title'],
                        'filename': filename,
                        'url': f'/view-post/{filename}'
                    })
                    
                    print(f"Successfully generated: {filename}")
                    
                except Exception as e:
                    print(f"Error generating post for '{topic['title']}': {e}")
                    continue
            
            # Update site files
            self.update_site_files(generated_posts)
            
            return {
                'success': True,
                'message': f'Successfully generated {len(generated_posts)} blog posts',
                'posts': generated_posts
            }
            
        except Exception as e:
            print(f"Error in generate_blog_posts: {e}")
            return {
                'success': False,
                'message': f'Error generating blog posts: {str(e)}',
                'posts': []
            }
    
    def create_blog_html(self, post_data):
        """Create SEO-optimized HTML for a blog post"""
        try:
            template = self.jinja_env.get_template('blog_template.html')
            
            # Generate SEO metadata
            seo_data = self.seo_optimizer.generate_seo_metadata(
                title=post_data['title'],
                content=' '.join([section[1] for section in post_data['content_sections']]),
                image_url=post_data['image']['url']
            )
            
            # Combine post data with SEO data
            template_data = {
                **post_data,
                **seo_data,
                'site_name': self.config.SITE_NAME,
                'site_url': self.config.SITE_URL,
                'contact_info': self.config.CONTACT_INFO
            }
            
            return template.render(**template_data)
            
        except Exception as e:
            print(f"Error creating blog HTML: {e}")
            raise
    
    def save_blog_post(self, title, html_content):
        """Save a blog post to the generated directory"""
        try:
            # Create safe filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{safe_title.lower()[:50]}-{datetime.now().strftime('%Y%m%d')}.html"
            
            # Ensure generated directory exists
            os.makedirs(self.config.GENERATED_DIR, exist_ok=True)
            
            # Save the file
            filepath = os.path.join(self.config.GENERATED_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return filename
            
        except Exception as e:
            print(f"Error saving blog post: {e}")
            raise
    
    def update_site_files(self, posts):
        """Update site-wide files like index, sitemap, RSS, etc."""
        try:
            # Generate the main index page for public access
            self.generate_site_index(posts)
            
            # Generate sitemap
            self.generate_sitemap()
            
            # Generate robots.txt
            self.generate_robots_txt()
            
            # Generate RSS feed
            self.generate_rss_feed()
            
            # Copy static assets for export
            self.copy_static_assets()
            
        except Exception as e:
            print(f"Error updating site files: {e}")
    
    def copy_static_assets(self):
        """Copy static CSS/JS files and create standalone Facebook-style blog"""
        try:
            import shutil
            
            # Create directories if they don't exist
            os.makedirs(os.path.join('generated', 'static', 'css'), exist_ok=True)
            os.makedirs(os.path.join('generated', 'static', 'js'), exist_ok=True)
            
            # Copy CSS files
            if os.path.exists('static/css/style.css'):
                shutil.copy2('static/css/style.css', 'generated/static/css/')
            
            # Copy JS files  
            if os.path.exists('static/js/script.js'):
                shutil.copy2('static/js/script.js', 'generated/static/js/')
            
            # Create standalone Facebook-style blog for file manager deployment
            self.create_standalone_facebook_blog()
                
        except Exception as e:
            print(f"Error copying static assets: {e}")
    
    def create_standalone_facebook_blog(self):
        """Create a standalone Facebook-style blog that works in any file manager"""
        try:
            # Read the template
            template = self.jinja_env.get_template('facebook_blog.html')
            
            # Get all posts data
            posts_data = []
            generated_dir = self.config.GENERATED_DIR
            
            if os.path.exists(generated_dir):
                for filename in os.listdir(generated_dir):
                    if filename.endswith('.html') and filename not in ['index.html', 'facebook.html', 'sitemap.xml', 'robots.txt', 'rss.xml']:
                        post_path = os.path.join(generated_dir, filename)
                        try:
                            with open(post_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                # Extract title
                                title_start = content.find('<title>') + 7
                                title_end = content.find('</title>')
                                title = content[title_start:title_end] if title_start > 6 and title_end > title_start else filename
                                
                                # Extract image URL
                                image_url = None
                                img_start = content.find('src="https://images.unsplash.com')
                                if img_start > -1:
                                    img_end = content.find('"', img_start + 5)
                                    if img_end > img_start:
                                        image_url = content[img_start + 5:img_end]
                                
                                posts_data.append({
                                    'filename': filename,
                                    'title': title.replace(' - SAKMPAR News', ''),
                                    'image_url': image_url,
                                    'published_date': datetime.fromtimestamp(os.path.getmtime(post_path)).isoformat(),
                                    'modified': datetime.fromtimestamp(os.path.getmtime(post_path)).strftime('%Y-%m-%d %H:%M')
                                })
                        except Exception as e:
                            print(f"Error processing post {filename}: {e}")
            
            # Sort posts by date (newest first)
            posts_data.sort(key=lambda x: x['published_date'], reverse=True)
            
            # Create standalone HTML with embedded posts data
            standalone_html = template.render().replace(
                "await fetch('/api/posts')",
                f"Promise.resolve({{ json: () => Promise.resolve({{ success: true, posts: {json.dumps(posts_data)} }}) }})"
            )
            
            # Save standalone Facebook blog
            facebook_path = os.path.join(generated_dir, 'facebook.html')
            with open(facebook_path, 'w', encoding='utf-8') as f:
                f.write(standalone_html)
            
            print(f"✅ Created standalone Facebook-style blog: facebook.html")
            
        except Exception as e:
            print(f"Error creating standalone Facebook blog: {e}")
    
    def generate_site_index(self, latest_posts):
        """Generate the main index page for the blog"""
        try:
            # Get all posts
            all_posts = []
            generated_dir = self.config.GENERATED_DIR
            
            if os.path.exists(generated_dir):
                for filename in os.listdir(generated_dir):
                    if filename.endswith('.html') and filename not in ['index.html', 'sitemap.xml', 'robots.txt', 'rss.xml']:
                        post_path = os.path.join(generated_dir, filename)
                        try:
                            with open(post_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Extract title from HTML
                                title_start = content.find('<title>') + 7
                                title_end = content.find('</title>')
                                title = content[title_start:title_end] if title_start > 6 and title_end > title_start else filename
                                
                                # Extract meta description
                                desc_pattern = r'<meta name="description" content="([^"]*)"'
                                desc_match = re.search(desc_pattern, content)
                                description = desc_match.group(1) if desc_match else ""
                                
                                all_posts.append({
                                    'title': title,
                                    'filename': filename,
                                    'description': description,
                                    'modified': datetime.fromtimestamp(os.path.getmtime(post_path)).strftime('%Y-%m-%d')
                                })
                        except Exception as e:
                            print(f"Error processing post {filename}: {e}")
            
            # Sort posts by modification date (newest first)
            all_posts.sort(key=lambda x: x['modified'], reverse=True)
            
            # Generate index HTML
            template = self.jinja_env.get_template('blog_list.html')
            index_html = template.render(
                posts=all_posts,
                site_name=self.config.SITE_NAME,
                site_description=self.config.SITE_DESCRIPTION,
                site_url=self.config.SITE_URL
            )
            
            # Save index file
            index_path = os.path.join(generated_dir, 'index.html')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_html)
            
        except Exception as e:
            print(f"Error generating site index: {e}")
    
    def generate_sitemap(self):
        """Generate XML sitemap"""
        try:
            generated_dir = self.config.GENERATED_DIR
            sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            
            # Add homepage
            sitemap_xml += f'  <url>\n'
            sitemap_xml += f'    <loc>{self.config.SITE_URL}/</loc>\n'
            sitemap_xml += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
            sitemap_xml += f'    <changefreq>daily</changefreq>\n'
            sitemap_xml += f'    <priority>1.0</priority>\n'
            sitemap_xml += f'  </url>\n'
            
            # Add blog posts
            if os.path.exists(generated_dir):
                for filename in os.listdir(generated_dir):
                    if filename.endswith('.html') and filename not in ['index.html']:
                        post_path = os.path.join(generated_dir, filename)
                        modified_date = datetime.fromtimestamp(os.path.getmtime(post_path)).strftime('%Y-%m-%d')
                        
                        sitemap_xml += f'  <url>\n'
                        sitemap_xml += f'    <loc>{self.config.SITE_URL}/{filename}</loc>\n'
                        sitemap_xml += f'    <lastmod>{modified_date}</lastmod>\n'
                        sitemap_xml += f'    <changefreq>weekly</changefreq>\n'
                        sitemap_xml += f'    <priority>0.8</priority>\n'
                        sitemap_xml += f'  </url>\n'
            
            sitemap_xml += '</urlset>'
            
            # Save sitemap
            sitemap_path = os.path.join(generated_dir, 'sitemap.xml')
            with open(sitemap_path, 'w', encoding='utf-8') as f:
                f.write(sitemap_xml)
            
        except Exception as e:
            print(f"Error generating sitemap: {e}")
    
    def generate_robots_txt(self):
        """Generate robots.txt file"""
        try:
            robots_content = f"""User-agent: *
Allow: /

Sitemap: {self.config.SITE_URL}/sitemap.xml
"""
            
            robots_path = os.path.join(self.config.GENERATED_DIR, 'robots.txt')
            with open(robots_path, 'w', encoding='utf-8') as f:
                f.write(robots_content)
            
        except Exception as e:
            print(f"Error generating robots.txt: {e}")
    
    def generate_rss_feed(self):
        """Generate RSS feed"""
        try:
            generated_dir = self.config.GENERATED_DIR
            
            # Get recent posts
            posts = []
            if os.path.exists(generated_dir):
                for filename in os.listdir(generated_dir):
                    if filename.endswith('.html') and filename not in ['index.html', 'sitemap.xml', 'robots.txt', 'rss.xml']:
                        post_path = os.path.join(generated_dir, filename)
                        try:
                            with open(post_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                # Extract title
                                title_start = content.find('<title>') + 7
                                title_end = content.find('</title>')
                                title = content[title_start:title_end] if title_start > 6 and title_end > title_start else filename
                                
                                # Extract meta description
                                desc_pattern = r'<meta name="description" content="([^"]*)"'
                                desc_match = re.search(desc_pattern, content)
                                description = desc_match.group(1) if desc_match else ""
                                
                                posts.append({
                                    'title': title,
                                    'filename': filename,
                                    'description': description,
                                    'pubDate': datetime.fromtimestamp(os.path.getmtime(post_path)).strftime('%a, %d %b %Y %H:%M:%S GMT')
                                })
                        except Exception as e:
                            print(f"Error processing post for RSS {filename}: {e}")
            
            # Sort by date (newest first) and limit to 20
            posts.sort(key=lambda x: x['pubDate'], reverse=True)
            posts = posts[:20]
            
            # Generate RSS XML
            rss_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{self.config.SITE_NAME}</title>
    <description>{self.config.SITE_DESCRIPTION}</description>
    <link>{self.config.SITE_URL}</link>
    <language>en-us</language>
    <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
'''
            
            for post in posts:
                rss_xml += f'''    <item>
      <title><![CDATA[{post['title']}]]></title>
      <description><![CDATA[{post['description']}]]></description>
      <link>{self.config.SITE_URL}/{post['filename']}</link>
      <pubDate>{post['pubDate']}</pubDate>
    </item>
'''
            
            rss_xml += '''  </channel>
</rss>'''
            
            # Save RSS feed
            rss_path = os.path.join(generated_dir, 'rss.xml')
            with open(rss_path, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            
        except Exception as e:
            print(f"Error generating RSS feed: {e}")
