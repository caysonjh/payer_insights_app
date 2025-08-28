import pandas as pd 
import requests 
import numpy as np 
import streamlit as st 
from tqdm import tqdm 
from stqdm import stqdm

def run_data_fetch(url, headers, out): 
    resp = requests.get(url, headers=headers).json()
    values = resp['result']['charts']['pie1']['series']
    labels = resp['result']['charts']['pie1']['labels']
    for i in range(len(values)): 
        out[labels[i]] = values[i]

def get_claims_for_npis(npis, headers, cpt_codes=None, hcpcs_codes=None, icd_codes=None, drugs=None): 
    claims_data = []
    for npi in stqdm(npis, total=len(npis), desc='Getting claims data...'): 
        base_url = f'https://api.medscout.io/api/v1/center/{npi}/'
        out = {}
        
        if cpt_codes:
            for i, cpt_code in enumerate(cpt_codes):
                if i == 0: 
                    cpt_url = base_url + 'cpt?code=%5B'
                cpt_url = cpt_url + f'%22CPT-{cpt_code}%22'
                if i == len(cpt_codes)-1:
                    cpt_url = cpt_url + f'%5D'
                else: 
                    cpt_url = cpt_url + f'%2C'
        
            run_data_fetch(cpt_url, headers, out)
        
        if hcpcs_codes: 
            for i, hcpcs_code in enumerate(hcpcs_codes): 
                if i == 0: 
                    hcpcs_url = base_url + 'hcpcs?code=%5B'
                hcpcs_url = hcpcs_url + f'%22HCPCS-{hcpcs_code}%22'
                if i == len(hcpcs_codes)-1: 
                    hcpcs_url = hcpcs_url + f'%5D'
                else: 
                    hcpcs_url = hcpcs_url + f'%2C'
                    
            run_data_fetch(hcpcs_url, headers, out)
                    
        if icd_codes: 
            for i, icd_code in enumerate(icd_codes): 
                if i == 0: 
                    icd_url = base_url + 'icd?code=%5B'
                icd_url = icd_url + f'%22ICD10D-{icd_code}%22'
                if i == len(icd_codes)-1: 
                    icd_url = icd_url + f'%5D'
                else: 
                    icd_url = icd_url + f'%2C'
        
            run_data_fetch(icd_url, headers, out)
        
        if drugs: 
            for i, drug in enumerate(drugs): 
                if i == 0: 
                    drug_url = base_url + 'drug?&drug=%5B'
                drug_url = drug_url + f'%22DRUG-{drug}%22'
                if i == len(drugs)-1: 
                    drug_url = drug_url + f'%5D'
                else: 
                    drug_url = drug_url + f'%2C'
        
            run_data_fetch(drug_url, headers, out)
        
        out['NPI'] = npi
        claims_data.append(out)
        
    out_df = pd.DataFrame(claims_data)
    
    return out_df


def get_payer_insights(npis, headers, saved_search_code): 
    types = []
    names = []

    for i in stqdm(range(len(npis)), total=len(npis), desc='Getting payer insights...'): 
        npi = npis[i]

        #28679 is the saved search code for Keratoconus All

        type_url = f'https://api.medscout.io/api/v1/entities/entity/{npi}/payer-mix/?group_by=payer_type&saved_search={saved_search_code}'
        name_url = f'https://api.medscout.io/api/v1/entities/entity/{npi}/payer-mix/?group_by=payer_name&saved_search={saved_search_code}'

        type_resp = requests.get(type_url, headers=headers).json()
        name_resp = requests.get(name_url, headers=headers).json()
        
        if len(type_resp) == 0 or len(name_resp) == 0: 
            print(f'No response for {npi}')
            continue
        
        type_out = {}
        name_out = {}        

        type_out['NPI'] = npi
        name_out['NPI'] = npi
        
        if len(type_resp['results']) == 0: 
            type_out['No Payer Type Data Available'] = True
        else: 
            type_out['No Payer Type Data Available'] = False
            for result in type_resp['results']: 
                type_out[result['payer_type']] = result['percentage']
        
        #print(type_out)
        
        if len(name_resp['results']) == 0: 
            name_out['No Payer Name Data Available'] = True
        else: 
            name_out['No Payer Name Data Available'] = False
            for result in name_resp['results']: 
                name_out[result['payer_name']] = result['percentage']
        
        types.append(type_out)
        names.append(name_out)


    type_df = pd.DataFrame(types).sort_values('No Payer Type Data Available', ascending=True)
    name_df = pd.DataFrame(names).sort_values('No Payer Name Data Available', ascending=True)
    
    return type_df, name_df



st.set_page_config(layout='wide')
st.title('Fetch Payer Insights + Code Values')

auth = st.text_input('Authorization Token')

saved_search_name = st.text_input('Name of Saved Search')

upload_npi_file = st.file_uploader('Upload file with NPIs', type=['csv'])

if st.button('Fetch Data', width='stretch'): 
    if len(saved_search_name) == 0: 
        st.error('Enter search name')
        st.stop()
    try: 
        df = pd.read_csv(upload_npi_file, dtype={'NPI / CCN':str})
        npis = df['NPI / CCN'].to_list()
    except: 
        st.error('Invalid file')
        st.stop()
    
    if len(auth) == 0: 
        st.error('Enter authorization token')
        st.stop() 
    
    headers = {
        'Authorization':auth
    }
    
    search_url = 'https://api.medscout.io/api/v1/account/saved-searches/'

    search_resp = requests.get(search_url, headers=headers).json()
    #st.text(search_resp)
    if 'detail' in search_resp: 
        if search_resp['detail'] == 'Authentication credentials were not provided.': 
            st.error('Authorization token is incorrect')
            st.stop()

    #st.text('Finding selected search...')
    #sel_search = None
    i = 0
    for search in search_resp: 
        #st.text(search)
        if search['search_name'] == saved_search_name: 
            sel_search = search 
            break 
        i += 1
    
    if i == len(search_resp): 
        st.error('Invalid search name')
        st.stop()
        
    cpt_codes, hcpcs_codes, icd_codes, drugs = [], [], [], []
    if 'cpt' in sel_search['filters']: 
        for cpt in sel_search['filters']['cpt']: 
            cpt_codes.append(cpt['title'])

    if 'hcpcs' in sel_search['filters']: 
        for hcpcs in sel_search['filters']['hcpcs']: 
            hcpcs_codes.append(hcpcs['title'])
        
    if 'icd' in sel_search['filters']: 
        for icd in sel_search['filters']['icd']: 
            icd_codes.append(icd['title'])   
        
    if 'drug' in sel_search['filters']: 
        for drug in sel_search['filters']['drug']: 
            drugs.append(drug['title'])
      
    #st.text(hcpcs_codes)  
    search_code = sel_search['id']
    #st.text(search_code)
    #st.text('Getting payer insights')
    type_df, name_df = get_payer_insights(npis, headers, search_code)
    #st.text('Getting claims data...')
    claims_df = get_claims_for_npis(npis, headers, cpt_codes, hcpcs_codes, icd_codes, drugs)
    
    st.dataframe(type_df)
    type_name = 'type_df.csv'
    type_df.to_csv(type_name)
    with open(type_name, 'rb') as f: 
        st.download_button('Download Type Payer Insights', icon=':material/person_celebrate:', 
                            data=f.read(), file_name=type_name, width='stretch')
    
    st.dataframe(name_df)
    name_name = 'name_df.csv'
    name_df.to_csv(name_name)
    with open(name_name, 'rb') as f: 
        st.download_button('Download Name Payer Insights', icon=':material/person_celebrate:', 
                            data=f.read(), file_name=name_name, width='stretch')

    st.dataframe(claims_df)
    claims_name = 'claims_df.csv'
    claims_df.to_csv(claims_name)
    with open(claims_name, 'rb') as f: 
        st.download_button('Download Claims Data for Codes', icon=':material/person_celebrate:',
                            data=f.read(), file_name=claims_name, width='stretch')