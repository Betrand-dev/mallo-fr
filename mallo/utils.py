"""
Utility functions for Mallo framework
"""

import os
import re
import hashlib
import json
from typing import Any, Dict

def secure_filename(filename: str)-> str:
    """
    make a filename secure for filesystem storage
    Args:
        filename: Original filename

    Returns:
         Secure version of filename

    :param filename:
    :return:
    """
    # Remove path separators
    filename = filename.replace('/','_').replace('\\','_')

    #Remove any non-printable characters
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename.strip()

def generate_etag(content: Any) -> str:
    """
    Generate Etag for content

    Args:
       content: Content to generate Etag for

    Returns:
        ETag string

    :param content:
    :return:
    """
    if isinstance(content, str):
        content = content.encode()
    elif isinstance(content, (dict, list)):
        content = json.dumps(content, sort_keys=True)

    return hashlib.md5(content).hexdigest()

def parse_multipart_form(headers, body):
    """
    Parse multipart form data
    (To be implemented for file uploads)

    :param headers:
    :param body:
    :return:
    """
    content_type = headers.get('Content-Type', '')
    if 'boundary=' not in content_type:
        return {}, {}

    boundary = content_type.split('boundary=')[-1].strip()
    if boundary.startswith('"') and boundary.endswith('"'):
        boundary = boundary[1:-1]

    boundary_bytes = ('--' + boundary).encode()
    parts = body.split(boundary_bytes)

    form = {}
    files = {}

    for part in parts:
        part = part.strip(b'\r\n')
        if not part or part == b'--':
            continue

        if b'\r\n\r\n' not in part:
            continue

        raw_headers, content = part.split(b'\r\n\r\n', 1)
        raw_headers = raw_headers.decode('utf-8', errors='ignore').split('\r\n')
        header_map = {}
        for line in raw_headers:
            if ':' in line:
                key, value = line.split(':', 1)
                header_map[key.strip().lower()] = value.strip()

        disposition = header_map.get('content-disposition', '')
        if 'form-data' not in disposition:
            continue

        name = None
        filename = None
        for item in disposition.split(';'):
            item = item.strip()
            if item.startswith('name='):
                name = item.split('=', 1)[1].strip('"')
            elif item.startswith('filename='):
                filename = item.split('=', 1)[1].strip('"')

        if not name:
            continue

        if content.endswith(b'\r\n'):
            content = content[:-2]

        if filename is not None:
            content_type_value = header_map.get('content-type', 'application/octet-stream')
            files[name] = {
                'filename': filename,
                'content_type': content_type_value,
                'content': content
            }
        else:
            value = content.decode('utf-8', errors='ignore')
            if name in form:
                if isinstance(form[name], list):
                    form[name].append(value)
                else:
                    form[name] = [form[name], value]
            else:
                form[name] = value

    return form, files

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug

    Args:
        text: Text to convert

    Return:
        Slug version of text
    :param text:
    :return:
    """
    # Convert to lowercase
    text = text.lower()

    # Replace non-alphanumeric with hyphen
    text = re.sub(r'[^a-z0-9]+', '-', text)

    text = text.strip('-')

    return text

def camel_to_snake(name: str) -> str:
    """
    Convert camelcase to snake_case

    Args:
        name: camelCase string

    Returns:
          snake_case string

    :param name:
    :return:
    """
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', name).lower()


def snake_to_camel(name: str) -> str:
    """
    Convert snake_cas to camelCase

    Args:
        name: snake_case string

    Returns:
          camelCase string

    :param name:
    :return:
    """
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])
