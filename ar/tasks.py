import requests
import bs4
import uuid
import boto
import io

from PIL import Image
from flask import current_app

from .application import celery, db
from .models import Post


@celery.task
def thumbnail_link(post_id):
    post = Post.query.filter_by(id=post_id).one()
    if post.thumbnail_path:
        raise AttributeError("Post already has a thumbnail!")
    if not post.url:
        raise AttributeError("Post is not a link type!")

    r = requests.get(post.url)
    if r.status_code != 200:
        raise AttributeError("URL was not properly reachable!")
    c = r.content
    soup = bs4.BeautifulSoup(c, "html5lib")
    img_urls = [t['content'] for t in soup.findAll(attrs={"property": "og:image"})]

    if not img_urls:
        print("No images to pull!")
        return

    img_url = img_urls[0]
    r = requests.get(img_url, stream=True)
    if r.status_code != 200:
        raise AttributeError("URL was not properly reachable!")
    im = Image.open(r.raw)
    im.thumbnail((70, 70))
    img_file = io.BytesIO()
    im.convert('RGB').save(img_file, "JPEG")
    img_file.seek(0)

    destination_filename = "{}.jpg".format(uuid.uuid4().hex)

    bucket_name = current_app.config["S3_BUCKET"]
    conn = boto.connect_s3(current_app.config["S3_KEY"], current_app.config["S3_SECRET"])
    b = conn.get_bucket(bucket_name)
    sml = b.new_key("/".join([current_app.config["S3_UPLOAD_DIRECTORY"], destination_filename]))
    sml.set_contents_from_file(img_file)
    sml.set_acl('public-read')

    post.thumbnail_path = ("https://{}.s3.amazonaws.com/{}"
                           .format(bucket_name, destination_filename))
    db.session.commit()
