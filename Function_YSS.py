import warnings
import streamlit as st
import pandas as pd
from typing import (
    Literal
)

_date_format: str = '%d/%m/%Y'

def read_upload_excel(uploader_message: str, key: str):
    uploaded_file = st.file_uploader(uploader_message, key=key)
    if uploaded_file is not None:
        xlsx = pd.ExcelFile(uploaded_file)
        if xlsx:
             return xlsx
        return None
        
def get_excel_sheet(xlsx: pd.ExcelFile, sheet_name: str):
    if sheet_name not in xlsx.sheet_names:
        st.warning(f'Interested spreadsheet "{sheet_name}" is not in the uploaded file.')
        return pd.DataFrame()
    else:
        warnings.simplefilter(action='ignore', category=UserWarning)
        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        if not df.empty:
            _date_col  = []
            for col in df.columns:
                if 'date' in col.lower():
                    _date_col.append(col)
            for col in _date_col:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime(_date_format)
        return df
    
def merge_dfs(df_list: list[pd.DataFrame], 
              on: str, 
              how: list[Literal['left', 'right', 'outer', 'inner', 'cross']]):
    
    if not df_list:
        return pd.DataFrame()
    
    elif len(how) == 1:
        output_df = df_list[0]

        if len(df_list) == 1:
            return output_df
        
        elif len(df_list) == 2:
            return pd.merge(output_df, df_list[1], on=on, how=how[0])
        
        else:
            for df in df_list[1:]:
                output_df = pd.merge(output_df, df, on=on, how=how[0])   
            return output_df

    elif len(how) > 1:
        if len(df_list) == len(how) + 1:
            count = 0
            output_df = df_list[0]

            for df in df_list[1:]:
                output_df = pd.merge(output_df, df, on=on, how=how[count])
                count += 1
            
            return output_df
        
        else:
            st.error('Wrong input for merge_dfs(), check the df_list and how')
            return pd.DataFrame()
    
    else:
        st.error('Wong input for merge_dfs(), check how')
        return pd.DataFrame()
