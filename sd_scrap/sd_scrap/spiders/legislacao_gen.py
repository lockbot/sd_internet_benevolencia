from scrapy import Spider
from scrapy_splash import SplashRequest
import re
import os
import html2text

with open('busca.txt', 'r') as f:
    busca = f.read()
ordenacao = "relevancia"
doctype = """<!DOCTYPE html>
<a href="$#link#$" hidden>hidden link</a>
"""


def get_filename(html):
    # Create a regex pattern to match the last / and before .htm
    pattern = r'.*/(.*).htm'

    # Use re.findall to find all matches
    matches = re.findall(pattern, html)

    if matches:
        return matches[0]  # Return the first match, which should be the only match
    else:
        return None  # Return None if there are no matches


class LegislacaoGenSpider(Spider):
    name = "legislacao_gen"

    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = True
        self.none_file_name_count = 0

        # request for headers and cookies
        with open('lua_cookies_req.lua', 'r') as f:
            self.lua_cookies_req = f.read()

        # navigate to search page
        with open('lua_search_req.lua', 'r') as f:
            self.lua_search_req = re.sub(r'\$#busca#\$', busca, f.read())

    def start_requests(self):
        if not os.path.exists(busca):
            os.mkdir(busca)
        if not os.path.exists(f"{busca}/html_laws"):
            os.mkdir(f"{busca}/html_laws")
        if not os.path.exists(f"{busca}/txt_laws"):
            os.mkdir(f"{busca}/txt_laws")

        with open('id_link_file', 'w') as f:
            f.write("")

        url = 'https://legislacao.presidencia.gov.br/'
        yield SplashRequest(url, self.parse_cookies_first_then_parse,
                            endpoint='execute', args={'lua_source': self.lua_cookies_req})

    def parse_cookies_first_then_parse(self, response):
        cookies = [{'domain': 'legislacao.presidencia.gov.br', 'secure': False, 'path': '/', 'httpOnly': False,
                    'name': 'f5_cspm', 'value': '1234'}]
        for cookie in response.data['cookies']:
            cookies.append(cookie)
        yield response.follow(response.url, self.parse_search,
                              cookies=cookies, meta={
                'splash': {
                    'endpoint': 'execute', 'args': {
                        'lua_source': self.lua_search_req,
                        'cookies': cookies
                    }
                },
                'cookies': cookies
            })

    def parse_search(self, response):
        url = response.url + "pesquisa/ajax/resultado_pesquisa_legislacao.php"
        num = int(re.search("\d+", response.data['num']).group())
        index_elements = ""
        for i in range(1, num // 10 + 2):
            index_elements += f'\t\t<li><a href="page{i}.html">{i}</a></li>\n'
            body = f"pagina={i}&posicao={(i - 1) * 10}&termo={busca}&num_ato=&ano_ato=&dat_inicio=&dat_termino=&tipo_macro_ato=lei&tipo_ato=&situacao_ato=&presidente_exercicio=&chefe_governo=&dsc_referenda_ministerial=&referenda_ministerial=&origem=&diario_extra=&data_resenha=&num_mes_resenha=&num_ano_resenha=&ordenacao={ordenacao}&conteudo_tipo_macro_ato=Leis%7Clei&conteudo_tipo_ato=&conteudo_situacao_ato=&conteudo_presidente_exercicio=&conteudo_chefe_governo=&conteudo_referenda_ministerial=&conteudo_origem=&conteudo_diario_extra="
            yield response.follow(url, self.parse_page_link, "POST",
                                  body=body,
                                  cookies=response.meta.get('cookies'),
                                  meta={
                                      'i': i - 1,
                                      'body': body,
                                      'splash': {
                                          'endpoint': 'render.html', 'args': {
                                              'wait': 1.5,
                                              'html': 1,
                                              'cookies': response.meta.get('cookies'),
                                          }
                                      }
                                  })
        with open('index_model.html', 'r') as fr:
            index = re.sub(r'\$#liahrefpageihtmliali#\$', index_elements, fr.read())
            with open(busca + "/html_laws/index.html", 'w') as fw:
                fw.write(index)

    def parse_page_link(self, response):
        i = response.meta.get('i')
        page_elements = ""
        for j, page in enumerate(response.css('h4.card-title a::attr(href)')):
            # wrong attempt: file_name = re.search(r'(?<=\/)[\w\-]+(\.\d+\w*)?(?=\.htm)', page.get()).group()
            # try reversing the page.get() string into variable, regex search it starting with mth\. until finds a \/ and then reverse it back to file_name
            # file_name = re.search(r'(?<=mth\.)[^\/.]+(?=\/)', page.get()[::-1]).group()[::-1]
            file_name = get_filename(page.get())
            if file_name is None:
                none_file_name = "None" + str(self.none_file_name_count)
                self.none_file_name_count += 1
                page_elements += f'\t\t<li><a href="{none_file_name}.html">{j + 1}</a></li>\n'
                with open(busca + "/html_laws/" + none_file_name + ".html", 'w') as f:
                    f.write(re.sub(r'\$#link#\$', page.get(), doctype) + response.css('html').get())
                yield {
                    'id': i * 10 + j + 1,
                    'URL': page.get(),
                    'file_name': "None",
                }
            else:
                page_elements += f'\t\t<li><a href="{file_name}.html">{j + 1}</a></li>\n'
                yield response.follow(page.get(), self.parse_law_link,
                                      meta={
                                          'id': i * 10 + j + 1,
                                          'file_name': file_name
                                      },
                                      dont_filter=True)
        with open('page_model.html', 'r') as fr:
            page = re.sub(r'\$#liahrefl00000htmliali#\$', page_elements, fr.read())
            page = re.sub(r'\$\{i\}', str(i + 1), page)
            page = re.sub(r'\$#body#\$', response.meta.get('body'), page)
            with open(busca + "/html_laws/page" + str(i + 1) + ".html", 'w') as fw:
                fw.write(page)

    def parse_law_link(self, response):
        file_name = response.meta.get('file_name')

        # start txt generator
        # '''
        with open(busca + "/txt_laws/" + file_name + ".txt", 'w') as f:
            f.write(self.converter.handle(response.css('body').get()))
        # '''
        # end txt generator
        # start html generator
        # '''
        with open(busca + "/html_laws/" + file_name + ".html", 'w') as f:
            f.write(re.sub(r'\$#link#\$', response.url, doctype) + response.css('html').get())
        # '''
        # end html generator
        yield {
            'id': response.meta.get('id'),
            'URL': response.url,
            'file_name': file_name
        }
