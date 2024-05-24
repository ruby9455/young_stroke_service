import streamlit as st
import pandas as pd
import string
from typing import (
    Literal,
    Callable
)

gender = {
    'M': 1,
    'F': 2
}

discipline = {
    'Nurse': 1,
    'OT': 2,
    'Rehab Physician': 3,
    'Neurologist': 4,
    # 'Other': 5
}

lhn_catchment = {
    'SALHN': 1,
    'CALHN': 2,
    'NALHN': 3,
    'Country': 4
}

triage_stream = {
    'Clinic': 1,
    'Intake': 2
}

yes_no = {
    'Yes': 1,
    'No': 0,
    'TBC': 2
}

working_rtw_goals = {
    'Yes, working': 1,
    'RTW goals': 2,
    'Neither': 0
}

phq_gad = {
    'Not at all': 0,
    'Several days': 1,
    'More than half the days': 2,
    'Nearly every day': 3
}

phq9_difficulty = {
    'Not difficult at all': 0,
    'Somewhat difficult': 1,
    'Very difficult': 2,
    'Extremely difficult': 3
}

gad7_severity = {
    0: 'Minimal',
    1: 'Mild',
    2: 'Moderate',
    3: 'Severe'
}

eq5d = {
    'I have no problems in walking about': 0,
    'I have no problems with self care': 0,
    'I have no problems with performing myusual activities': 0,
    'I have no pain or discomfort': 0,
    'I am not anxious or depressed': 0,
    'I have some problems in walking about': 1,
    'I have some problems with washing ordressing myself': 1,
    'I have some problems with performing myusual activities': 1,
    'I have moderate pain or discomfort': 1,
    'I am moderately anxious or depressed': 1,
    'I am confined to bed': 2,
    'I am unable to wash or dress myself': 2,
    'I am unable to perform my usual activities': 2,
    'I have extreme pain or discomfort': 2,
    'I am extremely anxious or depressed': 2
}

ocs_range = {
    1: [0, 4],
    2: [0, 3],
    3: [0, 4],
    4: [0, 4],
    5: [0, 15],
    6: [0, 3],
    7: [0, 4],
    8: [0, 50],
    9: [0, 50],
    10: [0, 50],
    11: [0, 12],
    12: [0, 4],
    13: [0, 4],
    14: [-13, 12]
}

unmet_needs = [
    'Body and Mind', 'Social', 'Daily Life', 
    'Relationships', 'Emotions', 'Information'
]

def mapping(input_df: pd.DataFrame, output_df: pd.DataFrame, apply_func: Callable, columns: list[str]):
    mapped_values = input_df.apply(apply_func, axis=1)
    mapped_df = pd.DataFrame(mapped_values.tolist(), columns=columns)
    
    return pd.concat([output_df, mapped_df], axis=1)

def general_map(row: pd.Series, col_name: Literal['Gender', 'LHN Catchment', 'Triage: Stream\nClinic or Intake', 'Consent data sharing', 'Aboriginal or Torres Strait Islander', 'Neuropsychology Ax', 'CBT Referral', 'Memory Referral', 'Working or RTW goals', 'Consent for contacting on future research', 'PHQ9', 'GAD7', 'PHQ9-diff', 'GAD7-sev', 'EQ5D', 'OCS']):
    if col_name == 'Gender':
        map = gender
    elif col_name == 'LHN Catchment':
        map = lhn_catchment
    elif col_name == 'Triage: Stream\nClinic or Intake':
        map = triage_stream
    elif col_name == 'Working or RTW goals':
        map = working_rtw_goals
    elif col_name == 'PHQ9' or col_name == 'GAD7':
        map = phq_gad
        return map.get(row.iloc[0], None)
    elif col_name == 'PHQ9-diff':
        map = phq9_difficulty
        return map.get(row.iloc[0], None)
    elif col_name == 'GAD7-sev':
        map = gad7_severity
        return map.get(row.iloc[0], None)
    elif col_name == 'EQ5D':
        map = eq5d
        return map.get(row.iloc[0], None)
    elif col_name == 'OCS':
        map = ocs_range
        return map.get(row.iloc[0], [None,None])
    # elif col_name in ['Consent data sharing', 'Aboriginal or Torres Strait Islander', 'Neuropsychology Ax', 'CBT Referral', 'Memory Referral', 'Consent for contacting on future research']:
    else:
        map = yes_no
        return map.get(row[col_name], None)
    
def map_discipline(row: pd.Series):
    col_name = 'Clinician Discipline'
    if pd.isna(row[col_name]) or row[col_name] == '':
        return None, None
    else:
        map_code = discipline.get(row[col_name], row[col_name])
        if isinstance(map_code, int):
            return map_code, None
        else:
            return 5, row[col_name]
        
def map_unmet_needs(df: pd.DataFrame):
    global unmet_needs

    df = df.copy()
    cat_num = 0
    item_num = 0
    df.rename(columns={df.columns[0]: 'Category', df.columns[1]: 'Item'}, inplace=True)
    
    # generate item_code by category and item
    if 'Item' in list(df.columns):
        idx = df.columns.get_loc('Item')
        if isinstance(idx, int):
            df.insert(idx+1, 'item_code', None)

    letter_lower = list(string.ascii_lowercase) # for category
    for idx, row in df.iterrows(): # skip header rows
        if idx <= 1:
            continue
        category = row['Category']
        item = row['Item']

        if pd.notna(category):
            cat_num += 1
            item_num = 0

        if pd.notna(item):
            item_num += 1
            # item_code = f'cat{cat_num}_item{item_num}'
            item_code = f'{letter_lower[cat_num-1]}{item_num}'
            df.at[idx, 'item_code'] = item_code
        else:
            break
    
    # nested_dict for output
    # outer_dict: key=study_id
    # inner_dict: key=unmet_needs or top_unmet_needs; value=[item_code_selected]
    output_dict: dict[str,dict[str,list[str]]] = {}

    for col in df.columns:
        if col.lower() not in ['category','item','item_code']:
            unmet_needs = []
            top_unmet_needs = []

            for idx, row in df[df['item_code'].notnull()].iterrows():
                if row[col] == 1:
                    unmet_needs.append(row['item_code'])
                elif row[col] == 2:
                    top_unmet_needs.append(row['item_code'])
            
            output_dict[col] = {}
            output_dict[col]['unmet_needs'] = unmet_needs
            output_dict[col]['top_unmet_needs'] = top_unmet_needs
    return output_dict, list(df['item_code'].dropna())
