#!/usr/bin/env python
# coding: utf-8
import configparser
from notion_client import Client
from datetime import datetime as dt
from jinja2 import Template, Environment, FileSystemLoader

config=configparser.ConfigParser()
config.read('config.cfg')

NOTION_TOKEN = config['NOTION']['TOKEN']
DATABASE_ID = config['NOTION']['DATABASE_ID']

def read_text(client, page_id):
    response = client.blocks.children.list(block_id=page_id)
    return response['results']

def read_database(client, database_id):
    response = client.databases.query(database_id=database_id)
    return response['results']

def get_info_from_database(client, notion_database_id, article_id=0):
    database_content = read_database(client, notion_database_id)
    article_page_id = database_content[article_id]['properties']['URL']['url'].split('-')[-1].split('?')[0]
    
    date = database_content[article_id]['properties']['Date']['date']['start']
    keywords = [i['name'] for i in database_content[article_id]['properties']['Étiquettes']['multi_select']]
    titre_article = database_content[article_id]['properties']['Nom']['title'][0]['text']['content']
    description = database_content[article_id]['properties']['Description']['rich_text'][0]['text']['content']
    
    page_content = read_text(client, article_page_id)
    
    html_content_list = []

    for block in page_content:
        block_type = block['type']
        if block_type == 'heading_1':
            content = block[block_type]['rich_text'][0]['text']['content']
            html = f"<h4>{content}</h4>"
            html_content_list.append(html)
        elif block_type == 'heading_2':
            content = block[block_type]['rich_text'][0]['text']['content']
            html = f"<h5>{content}</h5>"
            html_content_list.append(html)
        elif block_type == 'paragraph':
            content = block[block_type]['rich_text'][0]['text']['content']
            html = f"<p class='mt-3 text-muted'>{content}<p>"
            html_content_list.append(html)
        elif block_type == 'code':
            content = block[block_type]['rich_text'][0]['text']['content']
            html = f"<pre><code class='python'>{content}</code></pre>"
            html_content_list.append(html)
        elif block_type == 'image':
            content = block[block_type]['file']['url']
            html = f"<img src='{content}' alt='image'/>"
            html_content_list.append(html)
        else:
            print('Format non pris en charge', block_type)

    return date, keywords, titre_article, description, html_content_list

def main():
    client = Client(auth=NOTION_TOKEN)
    date, keywords, titre_article, description, html_content_list = get_info_from_database(client=client, notion_database_id=DATABASE_ID, article_id=0)
    results_filename = "blog.html"
    environment = Environment(loader=FileSystemLoader("."))
    results_template = environment.get_template("blog_template.html")
    context = {
        "description": description,
        "keywords": ' '.join(keywords),
        "titre_article": titre_article,
        "sous_titre_article": html_content_list[0],
        "content": html_content_list[1:],
        "date": date,
        "tag_1": keywords[0],
        "tag_2": keywords[1],
        "tag_3": keywords[2],
    }
    with open(results_filename, mode="w", encoding="utf-8") as results:
        results.write(results_template.render(context))
        print(f"... wrote {results_filename}")

if __name__ == '__main__':
    main()
