import requests
from requests.models import Response
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
import re
import pandas as pd


exemplo = "https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?p=31251004641376005952650690003823761844896598%7C2%7C1%7C1%7CCD52B364F220486109328BAA47A98AB41ACB1506"


def get_bs_object_from_url(url: str) -> BeautifulSoup:
    response: Response = requests.get(url)
    html: str = response.text

    soup = BeautifulSoup(html, 'lxml')

    return soup


def get_table_with_items(soup: BeautifulSoup, class_name: str = 'table table-striped') -> Tag:
    table_itens_tag: Tag = soup.find('table', class_=class_name)

    if not table_itens_tag:
        print("[-] Table 'table table-striped' not found...")
        return None
    else:
        return table_itens_tag
        
def get_df_from_dict(map_values: dict) -> pd.DataFrame:
    try:
        df = pd.DataFrame.from_dict(map_values)
    except Exception as e:
        print(f'[-] Erro ao converter dicionário para df: {e}')
        return pd.DataFrame()
    else:
        return df

def get_df_from_table(table_itens_tag: Tag):
    rows: ResultSet = table_itens_tag.find_all("tr")

    headers_raw: list = [
        "produto_codigo",
        "qtd",
        "un",
        "valor_total"
    ]

    map_final_values: dict = {
        "produto": [],
        "cod": [],
        "qtd": [],
        "valor_total": [] 
    }

    for row in rows:
        for idx, cell in enumerate(row.find_all(['td', 'th'])):
            v: str = cell.get_text(strip=True) 
            column = headers_raw[idx]
            
            if column == 'produto_codigo':
                produto, codigo = v.split('(Código: ')
                map_final_values['produto'].append(produto)
                map_final_values['cod'].append(codigo.replace(')', ''))
            elif column == 'qtd':
                raw_amount = re.findall('\d+\.\d{3}$', v)[0]
                qtd = float(raw_amount)
                map_final_values['qtd'].append(qtd)
            elif column == 'valor_total':
                raw_value = re.findall(r'\d+,\d{2}', v)[0]
                value = raw_value.replace(',', '.')
                value = float(value)
                map_final_values['valor_total'].append(value)
            elif column == 'un':
                continue
    
    df = get_df_from_dict(map_final_values)
    return df

def standardize_values(map_raw_values: dict) -> pd.DataFrame:
    map_valores: dict = {
        "produto": [],
        "cod_produto": [],
        "qtd": [],
        "valor_total": [] 
    }
    pass


def main():
    bs: BeautifulSoup = get_bs_object_from_url(exemplo)
    table: Tag = get_table_with_items(bs)

    df: pd.DataFrame = get_df_from_table(table)
    
    # TODO: Conectar ao google sheets do apto
    # TODO: Criar uma nova aba contendo todas essas informações e preenchendo com as fórmulas necessárias

if __name__ == '__main__':
    main()