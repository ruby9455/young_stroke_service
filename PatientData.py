import streamlit as st
import pandas as pd
import warnings
from pandas.errors import SettingWithCopyWarning

import Function_YSS as func
import MappingFunction_YSS as mapFunc

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

_redcap_import_form = pd.DataFrame()

def print_df(df: pd.DataFrame, line: int):
    st.write(f'current concat_df (line {line})')
    st.write(df)

def get_patient_data():
    output_df = pd.DataFrame()
    output_dict = {}

    patient_data = func.read_upload_excel(uploader_message='Patient Data File', key='patient_data_file')

    if patient_data is not None:
        output_df = func.get_excel_sheet(xlsx=patient_data,
                                    sheet_name='data')
        output_df.columns = output_df.iloc[0]
        output_df = output_df[1:].reset_index(drop=True)
        
        if 'id_dict' in st.session_state:
            output_dict = st.session_state['id_dict']

        else:
            st.error('No Study ID dict for mapping. Need patient log file. Click refresh button below to check.')
            patient_log = func.read_upload_excel(uploader_message='Patient Log File', key='patient_log_file_id')
            if patient_log is not None:
                demographics =func.get_excel_sheet(xlsx=patient_log,
                                                   sheet_name='Demographics')
                
                mrn_list = demographics['SALHN MRN'].tolist()
                study_id_list = demographics['StudyID'].tolist()

                for mrn, study_id in zip(mrn_list, study_id_list):
                    if pd.notna(mrn) and pd.notna(study_id):
                        output_dict[mrn] = study_id
                
                if output_dict:
                    st.session_state['id_dict'] = output_dict

        st.button('Refresh', key='refresh')

    return output_df, output_dict

def translate_patient_data():
    data_cols = []
    df, id_dict = get_patient_data()
    if not df.empty:
        df = df[df['SALHN MRN'].notnull()].reset_index(drop=True)

        # compute the studyid
        for idx, item in enumerate(df['SALHN MRN']):
            df.loc[idx, 'StudyID'] = id_dict.get(item, item)
        data_cols.append('StudyID')

        # phq9
            # add new cols for mapping
        phq9_col_names = []
        num_cols = 10
        for count in range(1, num_cols + 1):
            phq9_col_names.append(f'phq9_{count}')
    
        new_df = pd.DataFrame(columns=phq9_col_names, dtype=int)
        df = pd.concat([df, new_df], axis=1)

            # map the data and put the result in the newly created cols in the form
        count = 0
        for col in df.columns:
            if col.startswith('phq'):
                count += 1

                if count < num_cols:
                    col_name = f'phq9_{count}'
                    map_name = 'PHQ9'
                elif count == num_cols:
                    col_name = f'phq9_{count}'
                    map_name = 'PHQ9-diff'
                else:
                    col_name = None
                    map_name = None
                    
                if col_name and map_name:
                    # st.write(f'col_name: {col_name} map_name: {map_name}')
                    for idx, item in enumerate(df[col]):
                        if not pd.isna(item):
                            # st.write(item)
                            df.loc[idx, col_name] = mapFunc.general_map(pd.Series(item), map_name)
                else:
                    break
        df.rename(columns={'phq_ttl_score':'phq9_ttl_score'}, inplace=True) # rename the col to fit the redcap structure
        df['phq9_ttl_score'] = pd.to_numeric(df['phq9_ttl_score'], errors='coerce')
        phq9_col_names.append('phq9_ttl_score')
        data_cols += phq9_col_names

        # smrs
        data_cols.append('smrs_cat_excel')
        df.rename(columns={'smRS_cat':'smrs_cat_excel'}, inplace=True) # rename the col to fit the redcap structure
        
        # eq5d
            # add new cols for mapping
        eq5d_col_names = []
        num_cols = 6
        for count in range(2, num_cols+1):
            eq5d_col_names.append(f'eq5d_3l_{count}')
        new_df = pd.DataFrame(columns=eq5d_col_names, dtype=int)
        df = pd.concat([df, new_df], axis=1)

            # rename the health_score col and add it into data cols
        new_name = 'eq5d_3l_1'
        df.rename(columns={'eq5d_health score':new_name}, inplace=True)
        data_cols.append(new_name)

            # map the data and put the result in the newly created cols in the form
        count = 1
        for col in df.columns:
            if col.startswith('eq5d') and '_3l_' not in col:
                count += 1

                if count <= num_cols:
                    col_name = f'eq5d_3l_{count}'
                    map_name = 'EQ5D'
                else:
                    col_name = None
                    map_name = None

                if col_name and map_name:
                    for idx, item in enumerate(df[col]):
                        if not pd.isna(item):
                            df.loc[idx, col_name] = mapFunc.general_map(pd.Series(item), map_name)
                else:
                    break
        data_cols += eq5d_col_names

        # gad7
            # add new cols for mapping
        gad7_col_names = []
        num_cols = 7
        for count in range(1, num_cols + 1):
            gad7_col_names.append(f'gad7_{count}')
        new_df = pd.DataFrame(columns=gad7_col_names, dtype=int)
        df = pd.concat([df, new_df], axis=1)

            # map the data and put the result in the newly created cols in the form            
        count = 0
        for col in df.columns:
            if col.startswith('gad'):
                count += 1

                if count <= num_cols:
                    col_name = f'gad7_{count}'
                    map_name = 'GAD7'
                else:
                    col_name = None
                    map_name = None

                if col_name and map_name:
                    for idx, item in enumerate(df[col]):
                        if not pd.isna(item):
                            df.loc[idx, col_name] = mapFunc.general_map(pd.Series(item), map_name)
                else:
                    break

        df['gad7_score'] = None
        df['gad7_severity_excel'] = None
        for idx, row in df.iterrows():
            if row[gad7_col_names].isna().any():
                continue
            score = row[gad7_col_names].sum()
            df.at[idx, 'gad7_score'] = score
            # st.write(f'score: {score}')
            if score <= 4:
                level = 'Minimal'
            elif score <= 9:
                level = 'Mile'
            elif score <=14:
                level = 'Moderate'
            else:
                level = 'Severe'
            # st.write(f'level: {level}')
            # st.write(mapFunc.general_map(pd.Series(level), 'GAD7-sev'))
            df.at[idx, 'gad7_severity_excel'] = mapFunc.general_map(pd.Series(level), 'GAD7-sev')
        df.rename(columns={'gad7_score':'gad7_ttl_score'}, inplace=True) # rename the col to fit the redcap structure
        df['gad7_ttl_score'] = pd.to_numeric(df['gad7_ttl_score'], errors='coerce')
        gad7_col_names += ['gad7_ttl_score','gad7_severity_excel']
        # gad7_col_names += ['gad_score','gad_severity']
        data_cols += gad7_col_names

        # ocs
        # data validation
        ocs_col_names_dict = {}
        ocs_col_names_redcap = ['ocs_1','ocs_2','ocs_3','ocs_4','ocs_5',
                                'ocs_6a','ocs_6b','ocs_7a','ocs_7b','ocs_7c',
                                'ocs_8','ocs_9a','ocs_9b','ocs_10'] # rename the col to fit the redcap structure
        incorrect_id = []
        num_cols = 14
        count = 0
        for col in df.columns:
            if col.startswith('ocs'):
                count += 1
                ocs_col_names_dict[col] = f'{ocs_col_names_redcap[count-1]}'
                # ocs_col_names_dict[col] = f'ocs_{count}'

                if count <= num_cols:
                    score_range = mapFunc.general_map(pd.Series(count), 'OCS')
                    if isinstance(score_range, list) and score_range != [None, None] and len(score_range) == 2:
                        min_score, max_score = score_range

                        for idx, row in df.iterrows():
                            if row[col] < min_score or row[col] > max_score:
                                incorrect_id.append(row['SALHN MRN'])
                else:
                    break

        with st.expander(f'Num of id with incorrect value(s) in ocs cols: {len(incorrect_id)}'):
            st.write(incorrect_id)
        
        df.rename(columns=ocs_col_names_dict, inplace=True)
        data_cols += list(ocs_col_names_dict.values())        

        ############################## Extract the data by filtering the df with col name in data_cols ##############################
        # st.write('data_cols: ')
        # st.write(data_cols)
        data_df = df[data_cols]
        with st.expander('data_df from extracting data from Data.xlsx'):
            st.write(data_df)

        # split the form according to the StudyID pattern
        regex_pattern = r'SA\d{3}'
        _import_form_ready = data_df[data_df['StudyID'].str.contains(regex_pattern, regex=True)]\
            .rename(columns={'StudyID':'record_id'})\
                .sort_values(by='record_id').reset_index(drop=True)
        with st.expander('Form ready for import: '):
            st.write(_import_form_ready)

        _import_form_check = data_df[~data_df['StudyID'].str.contains(regex_pattern, regex=True)].reset_index(drop=True)
        _import_form_check.rename(columns={'StudyID':'SALHN MRN'}, inplace=True)
        with st.expander('Form needing to be checked: '):
            st.write(_import_form_check)

        return _import_form_ready, _import_form_check
