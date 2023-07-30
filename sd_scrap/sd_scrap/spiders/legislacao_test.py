from scrapy import Spider
import pandas as pd
import html2text
import re

with open('busca.txt', 'r') as f:
    busca = f.read()

# TUDO ERRADO

class LegislacaoTestSpider(Spider):
    name = "legislacao_test"
    start_urls = ["http://localhost:5500/l13846.html"]

    # there's an issue with not using the "start_requests" method
    # it will construct all the classes with Spider parameter
    # therefore use df pandas before it being ready etc
    # so I'm using the following __init__ as a workaround
    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.df = None
        self.converter = None

        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = True

        self.df = pd.read_csv('id_link_file3.csv', index_col='id').sort_index()

        with open('importador_test3.csv', 'w') as f:
            f.write("")

    def parse(self, response):
        for i, page in enumerate(response.css('ul>li>a::attr(href)')):
            yield response.follow(page.get(), self.parse_page_link, meta={'i': i})

    def parse_page_link(self, response):
        for j, page in enumerate(response.css('ul>li>a::attr(href)')):
            yield response.follow(page.get(), self.parse_law_link, meta={'id': response.meta.get('i') * 10 + j})

    def parse_law_link(self, response):
        df_series = self.df.iloc[response.meta.get('id')]

        tag_epigrafe = " ".join(response.css('a')[1:6].getall())
        epigrafe = re.search("[A-Z].+DE \d\d\d\d\.?", re.sub("N o", "Nº", self.converter.handle(tag_epigrafe).replace("  ", " "))).group()

        if len(response.css('td')) == 0:
            if len(response.css('.ementa')) > 0:
                tag_ementa = response.css('.ementa').get()
            else:
                tag_ementa = "".join(response.css('*[style="color: #800000"], *[color="#800000"]').getall())
        elif re.search("\w", self.converter.handle(response.css('td')[1].get())).group() == 'P':
            tag_ementa = response.css('td')[3].get()
        else:
            tag_ementa = response.css('td')[1].get()

        ementa = re.search("\w.+\w\.?", re.sub("~~", "", re.sub("\n", " ", self.converter.handle(tag_ementa)))).group()
        ementa = re.sub("\s?_\s?os\s?_", "ºˢ", re.sub("(n _º_|n _o_|n o)", "nº", re.sub("(N _º_|N _o_|N o)", "Nº", re.sub("(?<=\d)( _º_| _o_| o)", "º", ementa.replace("  ", " ")))))

        with open(busca + "/txt_laws/" + df_series.file_name + ".txt", 'r') as f:
            f_read = f.read()

            if re.search("\nArt. 1\s*(º|°|\_\s*o\s*\_|~~º~~|~~°~~)\s+\**\s*\w", f_read):
                art1_r = ""
                artigo_1 = re.sub("\n", " ", re.search("(.|\n.)+(?=\n\n)", f_read[re.search("\nArt. 1\s*(º|°|\_\s*o\s*\_|~~º~~|~~°~~)\s+\**\s*\w", f_read).end() - 1:]).group())
            else:
                art1_r = "r"
                artigo_1 = re.sub("~~", "", re.sub("\n", " ", re.search("(.|\n.)+(?=\n\n)", f_read[re.search("\n~*\s*Art. 1\s*(º|°|\_\s*o\s*\_|~~º~~|~~°~~)[~ ]+\**\s*~*\s*\(?\w", f_read).end() - 1:]).group()))

        artigo_1 = re.sub("\s?_\s?os\s?_", "ºˢ", re.sub("n o", "nº", re.sub("N o", "Nº", re.sub("(?<=\w)(\s?º|\s?°|\s?\_º\_|\s?\_\s?o\s?\_|\s?~~º~~|\s?~~°~~)", "º", artigo_1.replace("  ", " ")))))

        yield {
            'id': df_series.name,
            'epígrafe': epigrafe,
            'ementa': ementa,
            'Artigo 1º': artigo_1,
            'Artigo 1 revogado': art1_r,
            'URL': df_series.URL,
            'file_name': df_series.file_name,
        }
