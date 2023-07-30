from scrapy import Spider
import pandas as pd
import html2text
import re

with open('busca.txt', 'r') as f:
    busca = f.read()

class LegislacaoSpider(Spider):
    name = "legislacao"
    start_urls = ["http://localhost:5500"]

    # there's an issue with not using the "start_requests" method
    # it will construct all the classes with Spider parameter
    # therefore use df pandas before it being ready etc
    # so I'm using the following __init__ as a workaround
    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = True

        self.df = pd.read_csv('id_link_file.csv', index_col='id').sort_index()

        with open('importador.csv', 'w') as f:
            f.write("")

    def parse(self, response):
        for i, page in enumerate(response.css('ul>li>a::attr(href)')):
            yield response.follow(page.get(), self.parse_page_link, meta={'i': i})

    def parse_page_link(self, response):
        for j, page in enumerate(response.css('ul>li>a::attr(href)')):
            df_series = self.df.iloc[response.meta.get('i') * 10 + j]
            if df_series.file_name == 'None':
                yield {
                    'id': df_series.name,
                    'epígrafe': "",
                    'ementa': "",
                    'Artigo 1º': "",
                    'Artigo 1 revogado': "?",
                    'URL': df_series.URL,
                    'file_name': df_series.file_name,
                }
            else:
                yield response.follow(page.get(), self.parse_law_link, meta={'df_series': df_series})

    def parse_law_link(self, response):
        df_series = response.meta.get('df_series')

        tag_epigrafe = " ".join(response.css('a')[1:6].getall())
        epigrafe = re.search(r'[A-Z].+DE \d\d\d\d\.?', re.sub(r'N o', "Nº", self.converter.handle(tag_epigrafe).replace("  ", " "))).group()

        if len(response.css('td')) == 0:
            if len(response.css('.ementa')) > 0:
                tag_ementa = response.css('.ementa').get()
            else:
                tag_ementa = "".join(response.css('*[style="color: #800000"], *[color="#800000"]').getall())
        elif re.search(r'\w', self.converter.handle(response.css('td')[1].get())).group() == 'P':
            tag_ementa = response.css('td')[3].get()
        else:
            tag_ementa = response.css('td')[1].get()

        ementa = re.search(r'\w.+\w\.?', re.sub(r'~~', "", re.sub(r'\n', " ", self.converter.handle(tag_ementa)))).group()
        ementa = re.sub(r'\s?_\s?os\s?_', "ºˢ", re.sub(r'(n _º_|n _o_|n o)", "nº', re.sub(r'(N _º_|N _o_|N o)', "Nº", re.sub(r'(?<=\d)( _º_| _o_| o)', "º", ementa.replace("  ", " ")))))

        with open(busca + "/txt_laws/" + df_series.file_name + ".txt", 'r') as f:
            f_read = f.read()

            if re.search(r'\nArt. 1\s*(º|°|\_\s*o\s*\_|~~º~~|~~°~~)\s+\**\s*\w', f_read):
                art1_r = ""
                artigo_1 = re.sub(r'\n', " ", re.search(r'(.|\n.)+(?=\n\n)', f_read[re.search(r'\nArt. 1\s*(º|°|\_\s*o\s*\_|~~º~~|~~°~~)\s+\**\s*\w', f_read).end() - 1:]).group())
            else:
                art1_r = "r"
                artigo_1 = re.sub(r'~~', "", re.sub(r'\n', " ", re.search(r'(.|\n.)+(?=\n\n)', f_read[re.search(r'\n~*\s*Art. 1\s*(º|°|\_\s*o\s*\_|~~º~~|~~°~~)[~ ]+\**\s*~*\s*\(?\w', f_read).end() - 1:]).group()))

        artigo_1 = re.sub(r'\s?_\s?os\s?_', "ºˢ", re.sub(r'n o', "nº", re.sub(r'N o', "Nº", re.sub(r'(?<=\w)(\s?º|\s?°|\s?\_º\_|\s?\_\s?o\s?\_|\s?~~º~~|\s?~~°~~)', "º", artigo_1.replace("  ", " ")))))

        yield {
            'id': df_series.name,
            'epígrafe': epigrafe,
            'ementa': ementa,
            'Artigo 1º': artigo_1,
            'Artigo 1 revogado': art1_r,
            'URL': df_series.URL,
            'file_name': df_series.file_name,
        }