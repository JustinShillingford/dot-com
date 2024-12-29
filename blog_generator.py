import markdown
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import os
import json
from jinja2 import Environment, FileSystemLoader
import shutil
import re
from markdown.extensions import fenced_code, codehilite
import math

class StaticBlogGenerator:
    def __init__(self, site_url="https://justinshillingford.com"):
        self.site_url = site_url
        self.posts = []
        self.output_dir = "_site"
        self.posts_dir = "_posts"
        self.categories = {}
        self.tags = {}
        
        # Create necessary directories
        for dir_name in [self.output_dir, self.posts_dir]:
            os.makedirs(dir_name, exist_ok=True)
            
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader('_templates'))
        
    def create_templates(self):
        """Create default templates if they don't exist"""
        os.makedirs('_templates', exist_ok=True)
        
        templates = {
            'base.html': '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Justin Shillingford's Blog{% endblock %}</title>
    <link rel="alternate" type="application/rss+xml" title="RSS" href="/blog/feed.xml">
    <!-- Prism.js for syntax highlighting -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-dark.min.css" rel="stylesheet" class="prism-dark">
    <style>
        /* Light mode styles */
        :root {
            --bg-color: #a47764;
            --text-color: #333333;
            --link-color: #0066cc;
            --border-color: #dddddd;
            --code-bg: #f5f5f5;
        }
        
        /* Dark mode styles */
        .dark-mode {
            --bg-color: #1a1a1a;
            --text-color: #ffffff;
            --link-color: #66b3ff;
            --border-color: #404040;
            --code-bg: #2d2d2d;
        }
        
        body {
            max-width: 800px;
            margin: 0 auto;
            padding: 1rem;
            font-family: system-ui;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s;
        }
        
        a { color: var(--link-color); }
        
        article {
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .post-date { color: #666; }
        
        .post-meta {
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
            font-size: 0.9rem;
        }
        
        .categories, .tags {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .category, .tag {
            padding: 0.2rem 0.5rem;
            border-radius: 3px;
            background: var(--code-bg);
            font-size: 0.8rem;
        }
        
        .toc {
            background: var(--code-bg);
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 4px;
        }
        
        .toc a {
            display: block;
            padding: 0.2rem 0;
            text-decoration: none;
        }
        
        .search-container {
            margin: 1rem 0;
        }
        
        #search {
            width: 100%;
            padding: 0.5rem;
            font-size: 1rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-color);
            color: var(--text-color);
        }
        
        .share-buttons {
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .share-buttons a {
            padding: 0.5rem 1rem;
            background: var(--code-bg);
            border-radius: 4px;
            text-decoration: none;
        }
        
        .post-navigation {
            display: flex;
            justify-content: space-between;
            margin: 2rem 0;
        }
        
        .reading-time {
            font-style: italic;
            color: #666;
        }
        
        .theme-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px;
            border-radius: 50%;
            background: var(--code-bg);
            border: none;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleDarkMode()" aria-label="Toggle dark mode">🌓</button>
    {% block content %}{% endblock %}
    
    <!-- Prism.js for syntax highlighting -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-javascript.min.js"></script>
    
    <script>
        // Dark mode toggle
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        }
        
        // Initialize dark mode from localStorage
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
        
        // Search functionality
        function searchPosts() {
            const query = document.getElementById('search').value.toLowerCase();
            const posts = document.querySelectorAll('article');
            posts.forEach(post => {
                const content = post.textContent.toLowerCase();
                post.style.display = content.includes(query) ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>''',
            
            'index.html': '''
{% extends "base.html" %}
{% block content %}
    <h1>Justin Shillingford's Blog</h1>
    <p><a href="/blog/feed.xml">Subscribe via RSS</a></p>
    
    <div class="search-container">
        <input type="text" id="search" placeholder="Search posts..." onkeyup="searchPosts()">
    </div>
    
    {% for post in posts %}
    <article>
        <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
        <div class="post-meta">
            <span class="post-date">{{ post.date.strftime('%B %d, %Y') }}</span>
            <span class="reading-time">{{ post.reading_time }} min read</span>
        </div>
        
        {% if post.categories %}
        <div class="categories">
            {% for category in post.categories %}
            <span class="category">{{ category }}</span>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if post.tags %}
        <div class="tags">
            {% for tag in post.tags %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}
        
        <div>{{ post.excerpt }}</div>
    </article>
    {% endfor %}
{% endblock %}''',
            
            'post.html': '''
{% extends "base.html" %}
{% block title %}{{ post.title }} - Justin Shillingford's Blog{% endblock %}
{% block content %}
    <article>
        <h1>{{ post.title }}</h1>
        <div class="post-meta">
            <span class="post-date">{{ post.date.strftime('%B %d, %Y') }}</span>
            <span class="reading-time">{{ post.reading_time }} min read</span>
        </div>
        
        {% if post.categories %}
        <div class="categories">
            {% for category in post.categories %}
            <span class="category">{{ category }}</span>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if post.tags %}
        <div class="tags">
            {% for tag in post.tags %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if post.toc %}
        <div class="toc">
            <h3>Table of Contents</h3>
            {{ post.toc|safe }}
        </div>
        {% endif %}
        
        <div>{{ post.content|safe }}</div>
        
        <div class="share-buttons">
            <a href="https://twitter.com/intent/tweet?url={{ site_url }}{{ post.url }}&text={{ post.title }}" target="_blank" rel="noopener">Share on Twitter</a>
            <a href="https://www.linkedin.com/shareArticle?url={{ site_url }}{{ post.url }}&title={{ post.title }}" target="_blank" rel="noopener">Share on LinkedIn</a>
        </div>
        
        <div class="post-navigation">
            {% if post.previous %}
            <a href="{{ post.previous.url }}">← {{ post.previous.title }}</a>
            {% else %}
            <span></span>
            {% endif %}
            
            {% if post.next %}
            <a href="{{ post.next.url }}">{{ post.next.title }} →</a>
            {% endif %}
        </div>
    </article>
    <p><a href="/blog/">← Back to Blog</a></p>
{% endblock %}'''
        }
        
        for name, content in templates.items():
            path = os.path.join('_templates', name)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write(content)

    def estimate_reading_time(self, content):
        """Estimate reading time in minutes"""
        words = len(content.split())
        return max(1, math.ceil(words / 200))

    def generate_toc(self, content):
        """Generate table of contents from HTML content"""
        headings = re.findall(r'<h[2-3].*?>(.*?)</h[2-3]>', content)
        if not headings:
            return None
            
        toc = ['<div class="toc-content">']
        for heading in headings:
            slug = re.sub(r'[^\w\s-]', '', heading.lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            toc.append(f'<a href="#{slug}">{heading}</a>')
        toc.append('</div>')
        return '\n'.join(toc)

    def load_posts(self):
        """Load all markdown posts from _posts directory"""
        self.posts = []
        for filename in os.listdir(self.posts_dir):
            if filename.endswith('.md'):
                with open(os.path.join(self.posts_dir, filename), 'r') as f:
                    content = f.read()
                
                # Parse front matter
                lines = content.split('\n')
                front_matter = {}
                if lines[0] == '---':
                    end_front_matter = lines[1:].index('---') + 1
                    front_matter_lines = lines[1:end_front_matter]
                    content = '\n'.join(lines[end_front_matter + 1:])
                    
                    for line in front_matter_lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            front_matter[key.strip()] = value.strip()
                
                # Parse categories and tags
                categories = [c.strip() for c in front_matter.get('categories', '').split(',') if c.strip()]
                tags = [t.strip() for t in front_matter.get('tags', '').split(',') if t.strip()]

                # Convert content to HTML
                html_content = markdown.markdown(content)

                # Generate table of contents
                toc = self.generate_toc(html_content)
                
                # Create post object
                post = {
                    'title': front_matter.get('title', 'Untitled'),
                    'date': datetime.strptime(front_matter.get('date', '2025-01-01'), '%Y-%m-%d'),
                    'content': html_content,
                    'excerpt': ' '.join(content.split('\n\n')[0].split()[:50]) + '...',
                    'url': f'/blog/posts/{os.path.splitext(filename)[0].replace(" ", "_")}.html',
                    'categories': categories,
                    'tags': tags,
                    'toc': toc,
                    'reading_time': self.estimate_reading_time(content)
                }
                self.posts.append(post)

                # Update categories and tags indexes
                for category in categories:
                    self.categories.setdefault(category, []).append(post)
                for tag in tags:
                    self.tags.setdefault(tag, []).append(post)
        
        # Sort posts by date
        self.posts.sort(key=lambda x: x['date'], reverse=True)

        # Add next/previous links
        for i, post in enumerate(self.posts):
            post['next'] = self.posts[i-1] if i > 0 else None
            post['previous'] = self.posts[i+1] if i < len(self.posts)-1 else None

    def generate_feed(self):
        """Generate RSS feed"""
        fg = FeedGenerator()
        fg.title('Justin Shillingford\'s Blog')
        fg.link(href=f'{self.site_url}/blog')
        fg.description('Latest posts from Justin Shillingford\'s Blog')
        fg.logo(f'{self.site_url}/img/favicon/favicon-32x32.png')
        fg.image(url=f'{self.site_url}/img/favicon/favicon-rss.png', title='Justin Shillingford\'s Blog', link=f'{self.site_url}/blog')
        
        for post in self.posts:
            fe = fg.add_entry()
            fe.title(post['title'])
            fe.link(href=f'{self.site_url}{post["url"]}')
            fe.description(post['content'])
            time_zone = pytz.timezone('America/New_York')
            fe.pubDate(post['date'].astimezone(time_zone).strftime("%a, %d %b %Y %H:%M:%S %z"))
        
        os.makedirs(os.path.join(self.output_dir, 'blog'), exist_ok=True)
        fg.rss_file(os.path.join(self.output_dir, 'blog', 'feed.xml'))

    def generate_site(self):
        """Generate the complete static site"""
        # Ensure output directories exist
        os.makedirs(os.path.join(self.output_dir, 'blog', 'posts'), exist_ok=True)
        
        # Generate index page
        template = self.env.get_template('index.html')
        index_html = template.render(posts=self.posts)
        with open(os.path.join(self.output_dir, 'blog', 'index.html'), 'w') as f:
            f.write(index_html)
        
        # Generate individual post pages
        template = self.env.get_template('post.html')
        for post in self.posts:
            post_html = template.render(post=post)
            post_path = os.path.join(self.output_dir, 'blog', 'posts', 
                                   os.path.basename(post['url']))
            with open(post_path, 'w') as f:
                f.write(post_html)
        
        # Generate RSS feed
        self.generate_feed()

if __name__ == '__main__':
    generator = StaticBlogGenerator()
    generator.create_templates()
    generator.load_posts()
    generator.generate_site()
    print("Blog generated successfully!")
