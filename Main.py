# to-do: (discuss with Brendan) unmet needs table: 1 -> unmet needs; 2-> top unmet needs
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime

import PatientLog as log
import PatientData as data

_project_name: str = 'Young Stroke Service'
_date_format: str = '%d/%m/%Y'

st.set_page_config(
    page_title=f'{_project_name} Dashboard',
    layout='wide',
    initial_sidebar_state='expanded'
)

with st.sidebar:
    side_menu = option_menu(None, 
                            ['Home'],
                            icons=['house'],
                            menu_icon='cast',
                            default_index=0,
                            orientation='vertical')
    # st.button('Refresh', on_click=func.refresh)

if side_menu=='Home':
    try:
          df1 = log.translate_patient_log()
          patient_data = data.translate_patient_data()
          if patient_data:
               df2, df3 = patient_data
          else:
               df2, df3 = None, None
          # with st.expander('df1'):
          #      st.write(df1)
          # with st.expander('df2'):
          #      st.write(df2)   
          
          if df1 is not None and df2 is not None:
               output_df = pd.merge(left=df1, 
                                   right=df2, 
                                   how='outer',
                                   on='record_id')
               with st.expander('merge of df1 and df2'):
                    st.write(output_df)
          elif df1 is not None:
               output_df = df1
          elif df2 is not None:
               output_df = df2
          else:
               output_df = pd.DataFrame()

          cols = st.columns(2)
          if not output_df.empty:
               output_df.insert(1, 'redcap_event_name', 'baseline_arm_1')
               output_df_numeric_cols = output_df.select_dtypes(include=['number']).columns
               output_df[output_df_numeric_cols] = output_df[output_df_numeric_cols].astype('Int64')
               cols[0].download_button(
                    label='Download the import form',
                    data=output_df.to_csv(index=False),
                    file_name=f'redcap_import_template_{datetime.datetime.now().strftime(_date_format)}.csv',
                    mime='txt/csv'
               )
          if df3 is not None:
               cols[1].download_button(
                    label='Download data without StudyID in Data.xlsx',
                    data=df3.to_csv(index=False),
                    file_name=f'no_studyid_data_form_{datetime.datetime.now().strftime(_date_format)}.csv',
                    mime='txt/csv'
               )

    except Exception as e:
            st.error("An error occurred: {}".format(e))
