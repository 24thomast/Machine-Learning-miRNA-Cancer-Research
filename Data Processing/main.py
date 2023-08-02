import pandas as pd
import multiprocessing as mp
import requests
import time

from bs4 import BeautifulSoup

ORIGINAL_DATASET_PATH = 'original_dataset.csv'
TRANSPOSED_DATASET_PATH = 'transposed_dataset.csv'
UNSORTED_DATASET_PATH = 'unsorted_dataset.csv'
DATASET_PATH = "dataset.csv"

ACCESSIONS_PATH = 'accessions.csv'
LABELS_PATH = 'labels.csv'
TEMP_ACCESSIONS_PATH = "temp_accessions/accession"
TEMP_LABELS_PATH = "temp_labels/label"

ACCESSIONS_HEADING = 'Accessions'
LABELS_HEADING = 'Labels'

ACCESSIONS_URL = 'https://www.ncbi.nlm.nih.gov/geo/browse/?view=samples&series=211692&suppl=TXT&zsort=date&display=500&page='
LABELS_URL = 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='

ACCESSIONS_PAGE_NUM = 33
PROCESS_NUM = mp.cpu_count()


def transpose_dataset():
    pd.read_csv(ORIGINAL_DATASET_PATH, header=None).T.to_csv(TRANSPOSED_DATASET_PATH, index=False, header=False)


def get_accessions(count):
    temp_accessions_list = [ACCESSIONS_HEADING]

    pages_num = ACCESSIONS_PAGE_NUM / PROCESS_NUM

    for page in range(round(pages_num * count) + 1, round(pages_num * (count + 1)) + 1):
        url = ACCESSIONS_URL + str(page)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        table_rows = soup.find(id="geo_data").find("tbody").findAll("tr")

        for table_row in table_rows:
            accession = table_row.find("td").find("a").text
            if "GSM" in accession:
                temp_accessions_list.append(accession)

    path = TEMP_ACCESSIONS_PATH + str(count) + ".csv"
    df = pd.DataFrame(temp_accessions_list)
    df.to_csv(path, index=False, header=False)


def combine_accessions():
    accessions_list = [ACCESSIONS_HEADING]

    for count in range(PROCESS_NUM):
        path = TEMP_ACCESSIONS_PATH + str(count) + ".csv"
        temp_accession_list = pd.read_csv(path)[ACCESSIONS_HEADING].tolist()
        accessions_list.extend(temp_accession_list)

    df = pd.DataFrame(accessions_list)
    df.to_csv(ACCESSIONS_PATH, index=False, header=False)


def get_labels(count):
    temp_labels_list = [LABELS_HEADING]

    accessions_list = pd.read_csv(ACCESSIONS_PATH)[ACCESSIONS_HEADING].tolist()
    accessions_num = len(accessions_list) / PROCESS_NUM

    for accession in accessions_list[round(accessions_num * count): round(accessions_num * (count + 1))]:
        url = LABELS_URL + accession
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        characteristics = soup.find("td", string="Characteristics").parent.findAll("td")[1].text
        label = characteristics[15: characteristics.index("Sex:")].title()
        temp_labels_list.append(label)

    path = TEMP_LABELS_PATH + str(count) + ".csv"
    df = pd.DataFrame(temp_labels_list)
    df.to_csv(path, index=False, header=False)


def combine_labels():
    labels_list = [LABELS_HEADING]

    for count in range(PROCESS_NUM):
        path = TEMP_LABELS_PATH + str(count) + ".csv"
        temp_labels_list = pd.read_csv(path)[LABELS_HEADING].tolist()
        labels_list.extend(temp_labels_list)

    df = pd.DataFrame(labels_list)
    df.to_csv(LABELS_PATH, index=False, header=False)


def replace_labels():
    labels_df = pd.read_csv(LABELS_PATH)
    transposed_df = pd.read_csv(TRANSPOSED_DATASET_PATH)
    transposed_df.assign(ID_REF=labels_df[LABELS_HEADING]).to_csv(UNSORTED_DATASET_PATH, index=False)


def sort_dataset():
    unsorted_df = pd.read_csv(UNSORTED_DATASET_PATH)
    unsorted_df.sort_values(by=["ID_REF"], ascending=True).to_csv(DATASET_PATH, index=False)


if __name__ == '__main__':
    save_time = time.time()
    with mp.Pool(PROCESS_NUM) as pool:
        pool.map(get_accessions, range(PROCESS_NUM))
    combine_accessions()
    print("Accessions Time: ", time.time() - save_time)
    print("Accessions Length: ", len(pd.read_csv(ACCESSIONS_PATH)[ACCESSIONS_HEADING].tolist()))

    save_time = time.time()
    with mp.Pool(PROCESS_NUM) as pool:
        pool.map(get_labels, range(PROCESS_NUM))
    combine_labels()
    print("Labels Time: ", time.time() - save_time)
    print("Labels Length: ", len(pd.read_csv(LABELS_PATH)[LABELS_HEADING].tolist()))

    replace_labels()
    sort_dataset()


