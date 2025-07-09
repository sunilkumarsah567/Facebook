import os

class Config:
    """Configuration settings for the blog generator"""
    
    # API Keys from environment variables
    UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY', 'demo_key')
    
    # Google Trends RSS feeds for different languages
    GOOGLE_TRENDS_FEEDS = {
        'english': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=US',
        'hindi': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN',
        'global': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo='
    }
    
    # Alternative news RSS feeds as backup
    NEWS_RSS_FEEDS = {
        'english': [
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://rss.reuters.com/reuters/topNews'
        ],
        'hindi': [
            'https://feeds.abplive.com/abplive/hindi-news/home',
            'https://www.amarujala.com/rss/breaking-news.xml'
        ]
    }
    
    # Content generation settings
    MIN_CONTENT_LENGTH = 500
    MAX_CONTENT_LENGTH = 2000
    DEFAULT_POSTS_PER_GENERATION = 5
    
    # SEO settings
    DEFAULT_META_DESCRIPTION_LENGTH = 160
    DEFAULT_TITLE_LENGTH = 60
    
    # Image settings
    UNSPLASH_IMAGES_PER_POST = 1
    IMAGE_WIDTH = 800
    IMAGE_HEIGHT = 600
    
    # Site settings
    SITE_NAME = "SAKMPAR News"
    SITE_DESCRIPTION = "Latest trending topics and news updates"
    SITE_URL = "https://www.sakmpar.co.in"
    AUTHOR_NAME = "SAKMPAR Team"
    
    # Contact Information (automatically added to all pages)
    CONTACT_INFO = {
        'website': 'https://www.sakmpar.co.in',
        'email': 'info@sakmpar.co.in',
        'phone': '+91-XXXXXXXXXX',  # Add your phone number
        'address': 'India',  # Add your address
        'social_media': {
            'facebook': 'https://facebook.com/sakmpar',
            'twitter': 'https://twitter.com/sakmpar',
            'linkedin': 'https://linkedin.com/company/sakmpar',
            'instagram': 'https://instagram.com/sakmpar'
        }
    }
    
    # Directory settings
    GENERATED_DIR = 'generated'
    TEMPLATES_DIR = 'templates'
    STATIC_DIR = 'static'
