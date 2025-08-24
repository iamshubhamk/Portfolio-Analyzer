import pandas as pd
from io import BytesIO
import pdfplumber

def parse_portfolio(filename: str, file_content: bytes):
    if filename.endswith('.csv'):
        df = pd.read_csv(BytesIO(file_content))
        return df.to_dict(orient='records')

    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        df = pd.read_excel(BytesIO(file_content))
        return df.to_dict(orient='records')

    elif filename.endswith('.pdf'):
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            all_data = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    headers = table[0]
                    for row in table[1:]:
                        all_data.append(dict(zip(headers, row)))
            if not all_data:
                raise ValueError("No table found in PDF.")
            return all_data

    else:
        raise ValueError("Unsupported file type. Only CSV, XLSX, and PDF supported.")
