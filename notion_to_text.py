import configparser
import json
import os
import pprint

import requests
from notion_client import Client

config = configparser.ConfigParser()
config.read("config.cfg")

NOTION_TOKEN = config["NOTION"]["TOKEN"]
PAGE_ID = config["NOTION"]["PAGE_ID"]


def write_text(client, page_id, text):
    client.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                },
            }
        ],
    )


def write_dict_to_json(content, file_name):
    content_as_json_str = json.dumps(content)
    with open(file_name, "w") as f:
        f.write(content_as_json_str)


def read_text(client, page_id):
    response = client.blocks.children.list(block_id=page_id)
    # write_dict_to_json(response, "response.json")
    return response["results"]


def create_simple_blocks_from_content(client, content):
    page_simple_blocks = []
    for block in content:
        block_id = block["id"]
        block_type = block["type"]
        has_children = block["has_children"]

        if block_type not in ["code", "image"]:
            rich_text = block[block_type]["rich_text"]
            simple_block = {
                "id": block_id,
                "type": block_type,
                "text": rich_text[0]["plain_text"],
            }

            if has_children:
                nested_children = read_text(client, block_id)
                simple_block["children"] = create_simple_blocks_from_content(
                    client, nested_children
                )

            # if not rich_text:
            #    return

            page_simple_blocks.append(simple_block)

    return page_simple_blocks


def main():
    client = Client(auth=NOTION_TOKEN)
    content = read_text(client, PAGE_ID)
    write_dict_to_json(content, "content.json")
    simple_blocks = create_simple_blocks_from_content(client, content)
    write_dict_to_json(simple_blocks, "simple_blocks.json")


if __name__ == "__main__":
    main()
