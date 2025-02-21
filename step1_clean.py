import kagglehub
import pandas as pd
import zipfile
import os
import subprocess
import ast

#Get current path
current_path = os.getcwd()
folder_path = os.path.join(current_path,"NYT_DATA")

if not os.path.exists(folder_path):
    #Download NYT Articles Dataset from kaggle
    subprocess.run(["kaggle", "datasets", "download", "-d", "aryansingh0909/nyt-articles-21m-2000-present"])

    #Extract data from zip file
    with zipfile.ZipFile('nyt-articles-21m-2000-present.zip', 'r') as zip_ref:
        zip_ref.extractall(folder_path)

#Put data into a pandas dataframe
path = os.path.join(folder_path,"nyt-metadata.csv")
df = pd.read_csv(path)

#Remove Sections of NYT that either contain repeat topics (i.e., 'Corrections' would have the same sentiment and topic as its original published version)
#And the sentiment of things like 'Admin' is not of interest to us
removeList = ['Obituaries', 'membercenter','Archives','Corrections','Crosswords & Games','none','xword','Reader Center','Homepage','readersopinions','Admin','Week in Review','Critic\'s Choice','Topics']
df = df[~df['section_name'].isin(removeList)]

#Drop all document types besides 'articles'
df = df[df['document_type'] == 'article']

#Columns necessary for visualization--we will delete any rows with NaN in any of these
keep_columns = ['abstract','web_url','headline','keywords','pub_date','section_name']
#Remove all other columns
df = df.loc[:,keep_columns]
#Drop NaN
df = df.dropna(subset = keep_columns)

#Some rows of keywords do not contain 'NaN' but have '[]'. Remove these
df = df[df['keywords'].apply(lambda x: x != '[]')]

#Some rows in 'The Learning Network' Category have data that contains '.menu' that 
#is not meaningful for the purpose of this visualization. Remove.
df = df[~((df['section_name'] == 'The Learning Network') & (df['abstract'].str.contains('.menu', na=False)))]

#Some 'headline' rows have a hashmap with details. We only want the actual headline
#Optional
df['headline'] = df['headline'].apply(lambda x: (ast.literal_eval(x))['main'] if isinstance(x, str) else x)

#Similarly, with keywords-- we just want the keywords from the hash in a list
df['keywords'] = df['keywords'].apply(lambda x: [d['value'] for d in ast.literal_eval(x) if 'value' in d]  if isinstance(x, str) else x)

#We want to store the keywords in all lowercase for comparisons and searching later
df['keywords'] = df['keywords'].apply(lambda x: [item.lower() for item in x])

#The Visualization only intakes a year, not the entire datetime
df['pub_date'] = pd.to_datetime(df['pub_date'])
df['pub_date'] = df['pub_date'].dt.year

#Delete Old Large (uncleaned) dataset for space optimization (Optional)
if os.path.exists(path):
    os.remove(path)

rows = df.shape[0]

print("The dataset for this visualization is very large (",rows," rows)... the sentiment analyzer make take a while to run. You have the option to continue with a small test batch and the full file will be saved under a different name. If you choose to use a small batch and want to use the whole dataset later, you will have to rename the large file to 'nyt-metadata.csv' to be recognized by the other scripts")

ans = input("Do you want to continue with the full dataset? (Y/N)")

#Replace with cleaned file
#If you would like to keep both clean and unclean, rename filepath here
if ans == 'Y':
    df.to_csv(path,index = False, header = True)
else:
    df.head(5000).to_csv(path, index = False, header = True)
    path = os.path.join(folder_path,"nyt-metadata-full.csv")
    df.to_csv(path,index = False, header = True)

print(path)










