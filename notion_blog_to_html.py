#!/usr/bin/env python
# coding: utf-8
import sys
import configparser
from notion_client import Client
from datetime import datetime as dt
from jinja2 import Environment, FileSystemLoader

config=configparser.ConfigParser()
config.read('config.cfg')

NOTION_TOKEN = config['NOTION']['TOKEN']
DATABASE_ID = config['NOTION']['DATABASE_ID']

def read_text(client, page_id):
    """
    Reads text from a client using the provided page ID.

    Args:
        client (object): The client object used to make requests.
        page_id (str): The ID of the page to retrieve text from.

    Returns:
        list: The list of text results from the client.

    Raises:
        Exception: If an error occurs while making a request to the client.
    """
    try:
        response = client.blocks.children.list(block_id=page_id)
        return response['results']
    except Exception as e:
        print(f"Error occurred while making a request to the client: {e}")
        return []

def read_database(client, database_id):
    """
    Queries a Notion database using the provided client and database ID.

    Args:
        client (object): The client object used to connect to the Notion API.
        database_id (str): The ID of the database to query.

    Returns:
        list: The list of database records returned by the query. Each record is a dictionary containing the properties of the record.
    """
    try:
        response = client.databases.query(database_id=database_id)
        # Extract the 'results' field from the API response
        results = response['results']
        return results
    except Exception as e:
        print(f"An error occurred while querying the database: {e}")
        return []

def get_info_from_database(client, notion_database_id, article_id:int=0):
    """
    Retrieves information from a Notion database and formats it into a list of HTML content.

    Args:
        client (Notion client object): The Notion client object used to access the database.
        notion_database_id (str): The ID of the Notion database.
        article_id (int, optional): The index of the article in the database. Default is 0.

    Returns:
        tuple: A tuple containing the following elements:
            - date (str): The date of the article.
            - keywords (list): The keywords associated with the article.
            - titre_article (str): The title of the article.
            - description (str): The description of the article.
            - html_content_list (list): A list of HTML-formatted content blocks from the article.
    """
    article_id=int(article_id)
    database_content = read_database(client, notion_database_id)
    url = database_content[article_id]['properties']['Illustration']['url']
    article_page_id = database_content[article_id]['properties']['URL']['url'].split('-')[-1]
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
            language = block[block_type]['language']
            html = f"<pre><code class='{language}'>{content}</code></pre>"
            html_content_list.append(html)
        elif block_type == 'image':
            content = block[block_type]['file']['url']
            html = f"<img src='{content}' alt='image'/>"
            html_content_list.append(html)
        else:
            print('Format non pris en charge', block_type)

    return date, url, keywords, titre_article, description, html_content_list

def main(article_id:int=sys.argv[1]):
    """
    Connects to a Notion database and retrieves information to render a blog template.

    Inputs:
    - NOTION_TOKEN: The authentication token required to connect to the Notion database.
    - DATABASE_ID: The ID of the Notion database from which the information will be retrieved.
    - blog_template.html: The blog template to fill with notion blog content
    
    Outputs:
    - blog.html: A file containing the rendered template with the retrieved information.

    Example Usage:
    main()

    Code Analysis:
    1. Connect to the Notion database using the provided authentication token.
    2. Call the get_info_from_database function to retrieve the necessary information from the database.
    3. Load the Jinja2 template file named "blog_template.html" using the FileSystemLoader.
    4. Create a context dictionary containing the retrieved information and other variables.
    5. Open the file "blog.html" in write mode and encode it with UTF-8.
    6. Write the rendered template to the file using the results_template.render(context) method.
    7. Print a message indicating that the file has been written.
    """

    client = Client(auth=NOTION_TOKEN)
    date, url, keywords, titre_article, description, html_content_list = get_info_from_database(client=client, notion_database_id=DATABASE_ID, article_id=article_id)
    results_filename = f"blog-{titre_article.replace(' ', '_')}.html"
    environment = Environment(loader=FileSystemLoader("."))
    results_template = environment.get_template("blog_template.html")
    context = {
        "description": description,
        "keywords": ' '.join(keywords),
        "url":url,
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
