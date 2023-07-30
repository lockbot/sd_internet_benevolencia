import pandas as pd
import re

df_imp = pd.read_csv('../../importador.csv', index_col='id').sort_index()
# do this when you're ready to replace other columns as well
# df_imp['Artigo 1 revogado'] = df_imp['Artigo 1 revogado'].fillna(False).replace('r', True)

with open('../../busca.txt', 'r') as f:
    busca = '../../' + f.read()


def extract_number(s):
    match = re.search(r'Nº (\d+\.?\d*)', s)
    return int(re.sub("\.", "", match.group(1))) if match else None

df_imp['nº lei'] = df_imp['epígrafe'].apply(extract_number)

regex = r'internet|on-line|online|tecnol|digital|computador|computaciona|eletron|eletrôn|não presencial|virtual|virtuais|banda.larga| redes?\s|veículo de comunicação social'


def lists_of_law_interaction(file_name):
    with open(busca + "/txt_laws/" + file_name + ".txt", 'r') as f:
        f_r = f.read()

        all_tera_tmp = re.findall(r'([Aa]ltera|[Rr]evoga|[Rr]etifica|[Mm]odifica|[, ]e [ao])\s.*?([Dd]ecreto\n?-\n?[Ll]ei|[Ll]ei|[Ll]ei\s[Cc]omplementar)\s[^0-9.]+(\d[\.\d]*)', f_r)
        vigora = re.findall(r'([Dd]ecreto\n?-\n?[Ll]ei|[Ll]ei|[Ll]ei\s[Cc]omplementar)\s[^0-9.]+(\d[\.\d]*).?.[dD][eE]\s\d\d?\s[dD][eE]\s\w+\s[dD][eE]\s\d\d\d\d.?\spassa\sa\s', f_r)
        list_all_tera = []
        all_terado_tmp = re.findall(r'([\wí]+|[\wí]+\sdada)(?=\spel[ao]\s\w*-?([Dd]ecreto\n?-\n?[Ll]ei|[Ll]ei|[Ll]ei\s[Cc]omplementar))[^0-9.]+(\d[\.\d]*)', f_r)
        list_all_terado = []

        law_type_translation = {
            'lei': 'l',
            'decreto-lei': 'dl',
            'leicomplementar': 'lc'
        }
        last_action = None
        for action, law_type, number in all_tera_tmp:
            action = action.lower()
            law_type = re.sub(r'\s', "", law_type.lower())

            law_type = law_type_translation[law_type]

            if action in [' e o', ',e o', ' e a', ',e a']:
                action = last_action
            else:
                last_action = action

            list_all_tera.append((action, law_type, number))
        for law_type, number in vigora:
            law_type = re.sub(r'\s', "", law_type.lower())

            law_type = law_type_translation[law_type]

            list_all_tera.append(('altera', law_type, number))

        set_tera_dict = set(list_all_tera)
        list_all_tera = []
        for action, law_type, number in set_tera_dict:
            no = int(re.sub(r'\.', "", number))
            found_assunto = no in df_imp['nº lei'].values
            tera_dict = {
                'ação': action,
                'tipo_lei': law_type,
                'no': no,
                'assunto': found_assunto
            }
            list_all_tera.append(tera_dict)

        for action, law_type, number in all_terado_tmp:
            action = action.lower()
            law_type = re.sub(r'\s', "", law_type.lower())

            law_type = law_type_translation[law_type]

            list_all_terado.append((action, law_type, number))

        set_terado_dict = set(list_all_terado)
        list_all_terado = []
        for action, law_type, number in set_terado_dict:
            no = int(re.sub(r'\.', "", number))
            found_assunto = no in df_imp['nº lei'].values
            terado_dict = {
                'ação': action,
                'tipo_lei': law_type,
                'no': no,
                'assunto': found_assunto
            }
            list_all_terado.append(terado_dict)

    return f_r, list_all_tera, list_all_terado


def f_or_fx(list_all_tera, list_all_terado):
    list_all_tera_true = [item for item in list_all_tera if item['assunto']]
    list_all_terado_true = [item for item in list_all_terado if item['assunto']]

    if list_all_tera_true and list_all_terado_true:
        none_either_or_both_f_fx = "f();f(x)"
    elif list_all_tera_true:
        none_either_or_both_f_fx = "f()"
    elif list_all_terado_true:
        none_either_or_both_f_fx = "f(x)"
    else:
        none_either_or_both_f_fx = ""

    # Filter the lists based on 'assunto'
    quais_f_temp = [(item['ação'], item['tipo_lei'], item['no']) for item in list_all_tera if item['assunto']]
    quais_fx_temp = [(item['ação'], item['tipo_lei'], item['no']) for item in list_all_terado if item['assunto']]
    quais_f_o_temp = [(item['ação'], item['tipo_lei'], item['no']) for item in list_all_tera if not item['assunto']]
    quais_fx_o_temp = [(item['ação'], item['tipo_lei'], item['no']) for item in list_all_terado if not item['assunto']]

    # Convert the lists of tuples into strings
    quais_f_str = ';'.join(map(str, quais_f_temp))
    quais_fx_str = ';'.join(map(str, quais_fx_temp))
    quais_f_o_str = ';'.join(map(str, quais_f_o_temp))
    quais_fx_o_str = ';'.join(map(str, quais_fx_o_temp))

    return none_either_or_both_f_fx, quais_f_str, quais_fx_str, quais_f_o_str, quais_fx_o_str


def calculate_frequency(text, regex):
    # Find all occurrences of the terms in the text
    matches = re.findall(regex, text, re.IGNORECASE)

    # Count the total number of words in the text
    total_words = len(re.findall(r'\b\w+\b', text))

    # Calculate the frequency
    frequency = len(matches) / total_words

    return len(matches), total_words, frequency


# for row in df_imp.itertuples():
# for i, row in df_imp.iterrows():
# -- inside -- df.loc[index, 'column_name'] = some_value
def create_assunto_and_f_columns(row):
    file_name = row.file_name
    f_read, all_tera, all_terado = lists_of_law_interaction(file_name)
    f_fx, quais_f, quais_fx, quais_f_o, quais_fx_o = f_or_fx(all_tera, all_terado)
    matches, total_words, frequency = calculate_frequency(f_read, regex)
    row['f_or_fx'] = f_fx
    row['quais_f'] = quais_f
    row['quais_fx'] = quais_fx
    row['quais_f_o'] = quais_f_o
    row['quais_fx_o'] = quais_fx_o
    row['assunto'] = matches
    row['n_palavras'] = total_words
    row['freq_assunto'] = frequency

    return row

df = df_imp.apply(create_assunto_and_f_columns, axis=1)

df['o'] = df_imp.apply(lambda row: "" if re.search(regex, row['ementa'], re.IGNORECASE) or re.search(regex, row['Artigo 1º'], re.IGNORECASE) else "o", axis=1)
df['o']

df.to_csv('../../importador_frequenciado.csv', index=True, encoding='utf-8-sig')
