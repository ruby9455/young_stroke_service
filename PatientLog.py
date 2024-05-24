import streamlit as st
import pandas as pd

import Function_YSS as func
import MappingFunction_YSS as mapFunc

def translate_patient_log():
    # _redcap_import_form = pd.DataFrame()

    patient_log = func.read_upload_excel(uploader_message='Patient Log File', key='patient_log_file')

    if patient_log is not None:
        # return the mrn if 'yes' in col'Checked for SALHN MRN' for creating col'SALHN MRN'
        def create_salhn_mrn(row):
            # if row['Checked for SALHN MRN'] == 'Yes':
            #     return row['Medical Record Number']
            # else:
            #     return None
            return row['Medical Record Number']
            
        recruitment = func.get_excel_sheet(xlsx=patient_log,
                                           sheet_name='Recruitment')
        recruitment['SALHN MRN'] = recruitment.apply(create_salhn_mrn, axis=1)
        # remove unfilled row
        recruitment = recruitment[
            (recruitment['Patient Given Name'].notnull()) |
            (recruitment['Patient Family Name'].notnull())
        ]
        
        registered = func.get_excel_sheet(xlsx=patient_log,
                                        sheet_name='Registered')
        # remove unfilled row
        registered = registered[
            registered['SALHN MRN'].notnull()
        ]
        duplicated_col = ['Year-Month of Intake Ax', 'Patient Given Name', 'Patient Family Name', 'Date of birth']
        for col in duplicated_col:
            if col in registered.columns:
                registered.pop(col)

        demographics = func.get_excel_sheet(xlsx=patient_log,
                                            sheet_name='Demographics')
        # remove unfilled row
        demographics = demographics[
            demographics['SALHN MRN'].notnull()
        ]
        demographics = demographics[['StudyID', 'SALHN MRN', 'Consent for contacting on future research']]
        
        # store those three spreadsheet in the session state
        if recruitment is not None and registered is not None and demographics is not None:
            st.session_state['recruitment'] = recruitment
            st.session_state['registered'] = registered
            st.session_state['demographics'] = demographics

        # merge three dataframe by 'SALHN MRN' (inner: need study_id to store data on redcap) 
        # to-do: check the implementation of the function
        # patient_log_merge = func.merge_dfs(df_list=[recruitment, registered],
        #                         on='SALHN MRN',
        #                         how='outer')
        # patient_log_merge = func.merge_dfs(df_list=[patient_log_merge, demographics],
        #                                    on='SALHN MRN',
        #                                    how='inner')
        patient_log_merge = func.merge_dfs(df_list=[recruitment, registered, demographics],
                                           on='SALHN MRN',
                                           how=['outer','inner'])
        patient_log_merge = patient_log_merge[patient_log_merge['StudyID'].notnull()].reset_index(drop=True)
        
        # create a dict for mrn lookup and store in session_state
        mrn_list = patient_log_merge['SALHN MRN'].tolist()
        study_id_list = patient_log_merge['StudyID'].tolist()

        id_dict = {}
        for mrn, study_id in zip(mrn_list, study_id_list):
            if pd.notna(mrn) and pd.notna(study_id):
                id_dict[mrn] = study_id

        if 'id_dict' not in st.session_state:
            st.session_state['id_dict'] = id_dict
        
        if patient_log_merge is not None:
            st.session_state['patient_log_merge'] = patient_log_merge
            with st.expander('Patient Log Merge'):
                st.write(patient_log_merge)
        else:
            st.error('There is no patient with data in all interested spreadsheets ("Recruitment", "Registered" and "Demographics")')

        # extract data from patient_log into import form
        try:
            _redcap_import_form = pd.DataFrame(patient_log_merge['StudyID']).reset_index(drop=True).rename(columns={'StudyID':'record_id'})
            _redcap_import_form = mapFunc.mapping(input_df=patient_log_merge,
                                                output_df=_redcap_import_form,
                                                apply_func=lambda row: mapFunc.general_map(row=row, col_name='Gender'),
                                                columns=['gender'])
            _redcap_import_form['date_referral'] = patient_log_merge['Date of referral']
            _redcap_import_form['refer_clinician'] = patient_log_merge['Referring Clinician']
            _redcap_import_form['refer_service'] = patient_log_merge['Referring Service']
            _redcap_import_form = mapFunc.mapping(input_df=patient_log_merge,
                                                output_df=_redcap_import_form,
                                                apply_func=mapFunc.map_discipline,
                                                columns=['refer_clinician_discipline', 'refer_clinician_dis_des'])
            _redcap_import_form['date_stroke'] = patient_log_merge['Date of Stroke']
            mappings = [
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='LHN Catchment'),
                    'columns': ['lhn_catchment']
                },
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='Triage: Stream\nClinic or Intake'),
                    'columns': ['triage_stream']
                }
            ]
            for mapping_info in mappings:
                _redcap_import_form = mapFunc.mapping(input_df=patient_log_merge,
                                                        output_df=_redcap_import_form,
                                                        apply_func=mapping_info['apply_func'],
                                                        columns=mapping_info['columns'])
            _redcap_import_form['date_first_appt'] = patient_log_merge['First Appt (date)']
            mappings = [
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='Consent data sharing'),
                    'columns': ['consent_data_sharing']
                },
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='Aboriginal or Torres Strait Islander'),
                    'columns': ['aboriginal_ts_islander']
                },
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='Neuropsychology Ax'),
                    'columns': ['neuropsychology_ax']
                },
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='CBT Referral'),
                    'columns': ['cbt_referral']
                },
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='Memory Referral'),
                    'columns': ['memory_referral']
                },
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='Working or RTW goals'),
                    'columns': ['working_rtw_goals']
                },
                {
                    'apply_func': lambda row: mapFunc.general_map(row=row, col_name='Consent for contacting on future research'),
                    'columns': ['consent_future_research']
                }
            ]
            for mapping_info in mappings:
                _redcap_import_form = mapFunc.mapping(input_df=patient_log_merge,
                                                        output_df=_redcap_import_form,
                                                        apply_func=mapping_info['apply_func'],
                                                        columns=mapping_info['columns'])
            if not _redcap_import_form.empty:
                _redcap_import_form.sort_values(by='record_id',inplace=True)
                st.session_state['redcap_import_form_1'] = _redcap_import_form
                with st.expander('REDCap Import Form'):
                    st.write(_redcap_import_form)
            
            # unmet needs
            unmet_needs_input = func.get_excel_sheet(xlsx=patient_log,
                                                sheet_name='UnmetNeeds')
            unmet_needs_map_data, unmet_needs_list = None, None
            if not unmet_needs_input.empty:
                st.session_state['unmet_needs'] = unmet_needs_input
                mapping_result = mapFunc.map_unmet_needs(unmet_needs_input)
                if mapping_result is not None:
                    unmet_needs_map_data, unmet_needs_list = mapping_result
            if unmet_needs_map_data and unmet_needs_list:
                unmet_needs_df = pd.DataFrame(list(unmet_needs_map_data.keys()),columns=['record_id'])
                # append unmet_needs_list col to the import form with default value = 0
                    # create list of col_names
                unmet_needs_col_names = []
                top_unmet_needs_col_names = []
                for unmet_need in unmet_needs_list:
                    unmet_needs_col_names.append(f'unmet_{unmet_need}___1')
                    top_unmet_needs_col_names.append(f'top_unmet_{unmet_need}___1')
                    
                    # add those cols to import form
                new_df = pd.DataFrame(columns=unmet_needs_col_names+top_unmet_needs_col_names, dtype=int)
                concat_df = pd.concat([unmet_needs_df, new_df], axis=1)
                    # set default value
                fill_values = {col: 0 for col in new_df.columns}
                concat_df.fillna(fill_values, inplace=True)
                unmet_needs_df = concat_df
                # fill in the form according to the data
                for study_id, inner_dict in unmet_needs_map_data.items():
                    unmet_needs_list = inner_dict['unmet_needs']
                    top_unmet_needs_list = inner_dict['top_unmet_needs']
                    for item in top_unmet_needs_list:
                        col_name = f'unmet_{item}___1'
                        unmet_needs_df.loc[unmet_needs_df['record_id']==study_id, f'{col_name}'] = int(1)
                        unmet_needs_df.loc[unmet_needs_df['record_id']==study_id, f'top_{col_name}'] = int(1)

                    for item in unmet_needs_list:
                        col_name = f'unmet_{item}___1'
                        unmet_needs_df.loc[unmet_needs_df['record_id']==study_id, f'{col_name}'] = int(1)

                with st.expander('Unmet data to be added into the import form'):
                    st.write(unmet_needs_df)

                merged_df = pd.merge(_redcap_import_form, unmet_needs_df, how='outer', on='record_id')
                if not merged_df.empty:
                    st.session_state['redcap_import_form_2'] = merged_df
                    _redcap_import_form = merged_df
                    with st.expander('Latest version of REDCap Import Form'):
                        st.write(_redcap_import_form)
                    return _redcap_import_form
                else:
                    return None

            else:
                st.error('No result is returned from mapping the unmet need function.')
                if not _redcap_import_form.empty:
                    return _redcap_import_form
                else:
                    return None
            
        except Exception as e:
            st.error("An error occurred: {}".format(e))
