import markdown
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import os
import json
from jinja2 import Environment, FileSystemLoader
import shutil

class StaticBlogGenerator:
    def __init__(self, site_url="https://justinshillingford.com"):
        self.site_url = site_url
        self.posts = []
        self.output_dir = "_site"
        self.posts_dir = "_posts"
        
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
<html>
<head>
    <meta charset="utf-8">
    <title>{% block title %}Justin Shillingford's Blog{% endblock %}</title>
    <link rel="alternate" type="application/rss+xml" title="RSS" href="/blog/feed.xml">
    <style>
        body { max-width: 800px; margin: 0 auto; padding: 1rem; font-family: system-ui; }
        article { margin-bottom: 2rem; }
        .post-date { color: #666; }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>''',
            
            'index.html': '''
{% extends "base.html" %}
{% block content %}
    <h1>Justin Shillingford's Blog</h1>
    <p><a href="/blog/feed.xml">Subscribe via RSS</a></p>
    
    {% for post in posts %}
    <article>
        <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
        <div class="post-date">{{ post.date.strftime('%B %d, %Y') }}</div>
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
        <div class="post-date">{{ post.date.strftime('%B %d, %Y') }}</div>
        <div>{{ post.content|safe }}</div>
    </article>
    <p><a href="/blog/">← Back to Blog</a></p>
{% endblock %}'''
        }
        
        for name, content in templates.items():
            path = os.path.join('_templates', name)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write(content)

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
                
                # Convert content to HTML
                html_content = markdown.markdown(content)
                
                # Create post object
                post = {
                    'title': front_matter.get('title', 'Untitled'),
                    'date': datetime.strptime(front_matter.get('date', '2025-01-01'), '%Y-%m-%d'),
                    'content': html_content,
                    'excerpt': ' '.join(content.split('\n\n')[0].split()[:50]) + '...',
                    'url': f'/blog/posts/{os.path.splitext(filename)[0].replace(" ", "_")}.html'
                }
                self.posts.append(post)
        
        # Sort posts by date
        self.posts.sort(key=lambda x: x['date'], reverse=True)

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
