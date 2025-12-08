from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from credentials_gcp import get_google_sheet_object
from datetime import datetime
from gspread import Spreadsheet, Worksheet
import re
import requests
from requests.models import Response
import pandas as pd


class AutomatizacaoRegistroCompras:
    def __init__(self, url: str):
        self.url = url
        self.soup: BeautifulSoup = None
        self.df: pd.DataFrame = pd.DataFrame()
        self.final_date_struct: str = "%Y-%m-%d %H:%M:%S"
        
    def get_bs_object_from_url(self) -> BeautifulSoup:
        response: Response = requests.get(self.url)
        html: str = response.text

        self.soup = BeautifulSoup(html, 'lxml')
        
        return self.soup

    def get_emission_date(self, class_name: str = 'table table-hover') -> str:
        # soup.find_all('table', class_='table table-hover')[5].find_all(['td', 'th'])[7].get_text(strip=True)
        list_table_itens_tag: ResultSet = self.soup.find_all('table', class_=class_name)


        if not list_table_itens_tag:
            print(f"[-] Table '{class_name}' not found...")
            return None
        else:
            tag_general_infos_date: Tag = list_table_itens_tag[5]
            date_str = tag_general_infos_date.find_all(['td', 'th'])[7].get_text(strip=True)
            
            date_str = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S").strftime(self.final_date_struct)
            return date_str


    def get_table_with_items(self, class_name: str = 'table table-striped') -> Tag:
        table_itens_tag: Tag = self.soup.find('table', class_=class_name)

        if not table_itens_tag:
            print(f"[-] Table '{class_name}' not found...")
            return None
        else:
            return table_itens_tag
            
    def get_df_from_dict(self, map_values: dict) -> pd.DataFrame:
        try:
            df = pd.DataFrame.from_dict(map_values)
        except Exception as e:
            print(f'[-] Erro ao converter dicionário para df: {e}')
            return pd.DataFrame()
        else:
            return df

    def get_df_from_table(self, table_itens_tag: Tag):
        rows: ResultSet = table_itens_tag.find_all("tr")

        headers_raw: list = [
            "produto_codigo",
            "qtd",
            "un",
            "valor"
        ]

        map_final_values: dict = {
            "produto": [],
            "cod": [],
            "qtd": [],
            "valor": [] 
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
                elif column == 'valor':
                    raw_value = re.findall(r'\d+,\d{2}', v)[0]
                    value = raw_value.replace(',', '.')
                    value = float(value)
                    map_final_values['valor'].append(value)
                elif column == 'un':
                    continue

        self.df = self.get_df_from_dict(map_final_values)
        self.df['andre_nao_quer'] = ""
        self.df['gilmar_nao_quer'] = ""
        self.df['kaleb_nao_quer'] = ""
        self.df['qtd_interessados'] = ""
        self.df['valor_por_interessado'] = ""
        self.df['valor_so_andre'] = ""
        self.df['valor_so_gilmar'] = ""
        self.df['valor_so_kaleb'] = ""
        return self.df

    @staticmethod
    def _fill_df_into_worksheet(df: pd.DataFrame, ws: Worksheet):
        values = [df.columns.tolist()] + df.values.tolist()
        ws.update("A5", values, value_input_option="USER_ENTERED")

    @staticmethod
    def _fill_formulas_in_worksheet(df: pd.DataFrame, ws: Worksheet):
        map_column_formula: dict[str, str] = {
            # qtd_interessados:
            "H": "=IF(ISBLANK(E2),1, 0)+IF(ISBLANK(F2),1, 0)+IF(ISBLANK(G2),1, 0)",
            # valor_por_interessado:
            "I": "=D2/H2",
            # valor_so_andre:
            "J": "=IF(ISBLANK(E2),1,0)*$I2",
            # valor_so_gilmar:
            "K": "=IF(ISBLANK(F2),1,0)*$I2",
            # valor_so_kaleb:
            "L": "=IF(ISBLANK(G2),1,0)*$I2"
        }
        qtd_linhas = df.shape[0]
        init_row_values = 6
        total_linhas = init_row_values + qtd_linhas 
        
        for col, formula in map_column_formula.items():
            for row in range(init_row_values, total_linhas):
                # print(f"{col}{row}", formula.replace("2", str(row)))
                try:
                    ws.update_acell(f"{col}{row}", formula.replace("2", str(row)))
                except Exception as e:
                    print(f"[-] Erro ao atualizar célula '{col}{row}': {e}")

    @staticmethod
    def _fill_total_in_worksheet(df: pd.DataFrame, ws: Worksheet):
        ws.update_acell("A1", "Total André:")
        ws.update_acell("A2", "Total Gilmar:")
        ws.update_acell("A3", "Total Kaleb:")

        ws.update_acell("B1", f"=SUM(J:J)")
        ws.update_acell("B2", f"=SUM(K:K)")
        ws.update_acell("B3", f"=SUM(L:L)")

    def create_sheet_with_values(self):
        sheet: Spreadsheet = get_google_sheet_object()
        
        data_emissao = self.get_emission_date()
        title = f'Compras {data_emissao}'
        ws: Worksheet = sheet.add_worksheet(title=title, rows=100, cols=20)
        
        self._fill_df_into_worksheet(self.df, ws)
        self._fill_formulas_in_worksheet(self.df, ws)
        self._fill_total_in_worksheet(self.df, ws)

    def run(self):
        self.get_bs_object_from_url()
        table: Tag = self.get_table_with_items()

        self.get_df_from_table(table)

        self.create_sheet_with_values()


if __name__ == '__main__':
    exemplo_url = "https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?p=31251004641376005952650690003823761844896598%7C2%7C1%7C1%7CCD52B364F220486109328BAA47A98AB41ACB1506"

    automatizacao_registro_compras = AutomatizacaoRegistroCompras(url=exemplo_url)
    automatizacao_registro_compras.run()