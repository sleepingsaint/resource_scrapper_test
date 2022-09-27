import requests
from bs4 import BeautifulSoup
from utils.python.resource_client import ResourceClient

class AnalyticsVidhyaBlogClient(ResourceClient):
    def __init__(self, title: str, url: str, dateFormat: str) -> None:
        super().__init__(title, dateFormat)
        self.url = url

    def getTitle(self, tag):
        if tag is None:
            return None

        title = tag.find("h4")
        if title is not None:
            return self.formatTitle(title.text)
        return None
    
    def getURL(self, tag):
        if tag is None:
            return None

        try:
            title = tag.find("h4")
            a = title.parent
            return self.formatURL(a['href'])
        except:
            return None

    def getAuthors(self, tag):
        if tag is None:
            return None
        
        try:
            h6 = tag.find("h6")
            author_tag = h6.find_all("a")[-1]
            return self.formatAuthors(author_tag.text.split(','))
        except:
            return None
    
    def getPublishedOn(self, tag):
        if tag is None:
            return None
        
        try:
            h6 = tag.find("h6")
            date_str = h6.text.strip()
            a_tags = h6.find_all("a")
            if len(a_tags) > 0:
                author = a_tags[-1].text
                date_str = date_str.replace(author, "")
                date_str = date_str[2:]
            return self.formatPublishedOn(date_str)
        except:
            return None

    def getTags(self, tag=None):
        if tag is None:
            return self.formatTags(None)
        try:
            tags_span = tag.find("span")
            tags_elements = tags_span.find_all("a")
            tags = []
            for ele in tags_elements:
                tags.append(ele.text.strip())
            return self.formatTags(tags)
        except:
            return self.formatTags(None) 
    
    def getResources(self):
        page_num = 1

        while True:
            page = requests.get(self.url + f"page/{page_num}/")
            soup = BeautifulSoup(page.content, 'html.parser')
            container = soup.find("section", class_="listing-page")
            
            ul = container.find("ul")
            posts = ul.find_all("li")
            for post in posts:
                title = self.getTitle(post)
                url = self.getURL(post)

                if title is None or url is None:
                    continue
                
                authors = self.getAuthors(post)
                tags = self.getTags(post)
                publishedOn = self.getPublishedOn(post)

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

            if soup.find("a", class_="next") is not None:
                page_num += 1
            else:
                break


if __name__ == "__main__":
    title = "Analytics Vidhya Blog"
    url = "https://www.analyticsvidhya.com/blog-archive/"
    icon = "https://play-lh.googleusercontent.com/PAm4EoEKyjoDFuaF_uOENwVETTswBDQ5D-Q_erHEefNyDAd4uxwcGCYPj9b8FOaSTXM"
    dateFormat = "%B %d, %Y"

    analyticsvidhyablog_client = AnalyticsVidhyaBlogClient(title, url, dateFormat)
    analyticsvidhyablog_client.getResources()
    if analyticsvidhyablog_client.new_source:
        analyticsvidhyablog_client.sendSourceNotification(title, url)