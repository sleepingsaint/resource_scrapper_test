import requests
from bs4 import BeautifulSoup
from utils.python.resource_client import ResourceClient

class AmazonMLBlogClient(ResourceClient):
    def __init__(self, title: str, dateFormat: str) -> None:
        super().__init__(title, dateFormat)

    def getTitle(self, tag):
        if tag is None:
            return None
        try:
            title_tag = tag.find("h2", class_="blog-post-title")
            return self.formatTitle(title_tag.text)
        except:
            return None
    
    def getURL(self, tag):
        if tag is None:
            return None
        
        try:
            title_tag = tag.find("h2", class_="blog-post-title")
            a = title_tag.find("a")
            return self.formatURL(a['href'])
        except:
            return None

    def getPublishedOn(self, tag):
        if tag is None:
            return None

        try:
            meta = tag.find("footer", class_="blog-post-meta")
            publishedOn = meta.find("time", {"property": "datePublished"})
            return self.formatPublishedOn(publishedOn.text)
        except:
            return None

    def getAuthors(self, tag):
        if tag is None:
            return None

        try:
            meta = tag.find("footer", class_="blog-post-meta")
            spans = meta.find_all("span", {"property": "author"})
            authors = []
            for span in spans:
                authors.append(span.text.strip())
            return self.formatAuthors(authors)
        except:
            return None

    def getTags(self, tag):
        if tag is None:
            return None

        try:
            meta = tag.find("footer", class_="blog-post-meta")
            categories_tag = meta.find("span", {"class": "blog-post-categories"})
            tag_elements = categories_tag.find_all("span", {"property": "articleSection"})
            
            tags = []
            for ele in tag_elements:
                tags.append(ele.text.stip())
            
            return self.formatTags(tags)
        except:
            return self.formatTags(None)

    def nextPageUrl(self, soup):
        try:
            pagination_container = soup.find("div", {"class": "blog-pagination"})
            older_posts = pagination_container.find("a", {"class": "blog-btn-a"})
            if older_posts.text.find("Older posts") != -1:
                return older_posts['href']
            return None
        except:
            return None

    def getResources(self, initial_url):
        page_url = initial_url
        while True:
            page = requests.get(page_url)
            soup = BeautifulSoup(page.content, 'html.parser')
            
            posts = soup.find_all("article", class_="blog-post")

            for post in posts:
                title = self.getTitle(post)
                url = self.getURL(post)
                
                if title is None or url is None:
                    continue
                
                authors = self.getAuthors(post)
                publishedOn = self.getPublishedOn(post)
                tags = self.getTags(post)

                resourceExists = self.db.resourceExists(url)

                if not resourceExists:
                    result = self.db.addResource(title=title, url=url, publishedOn=publishedOn, authors=authors, tags=tags, source=self.source)
                    if not result:
                        print(f"Resource cannot be created : {title}")
                        print(url, tags, authors, publishedOn, sep="\n")
                    elif not self.refetch:
                        self.sendResourceNotification(url)

                elif self.refetch:
                    result = self.db.updateResource(page_id=resourceExists, title=title, url=url, publishedOn=publishedOn, authors=authors, tags=tags, source=self.source)
                    if not result:
                        print(f"Resource cannot be updated : {title}")
                    continue
                elif self.delete:
                    result = self.db.deleteResource(page_id=resourceExists)
                    if not result:
                        print(f"Resource cannot be deleted : {title}")
                    continue
                else:
                    return

            nextPageURL = self.nextPageUrl(soup)
            if nextPageURL is None:
                break
            page_url = nextPageURL

if __name__ == "__main__":
    title = "Amazon ML Blog"
    url = "https://aws.amazon.com/blogs/machine-learning/"
    icon = "https://www.solodev.com/file/e17f3d9f-b23d-11ea-904e-0eb0590535cd/SageMaker%20Icon%202-d5a8af11.jpg"
    dateFormat = "%d %b %Y"

    amazonmlblog_client = AmazonMLBlogClient(title, dateFormat)
    amazonmlblog_client.getResources(url)

    if amazonmlblog_client.new_source:
        amazonmlblog_client.sendSourceNotification(title, url)