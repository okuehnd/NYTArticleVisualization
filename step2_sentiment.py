import pandas as pd
from transformers import pipeline
import os

#Find the cleaned file we created in the cleaning step

for root, dirs, files in os.walk("."): 
    if "nyt-metadata.csv" in files:
        data_set_path = os.path.join(root, "nyt-metadata.csv")
        folder_path = root
        break  

#Open pandas dataframe
articles = pd.read_csv(data_set_path)

#Identify file paths for output, tracking, and errors

#Output file will copy the original df and add its sentiment value
output_file = os.path.join(folder_path,'sentiment_nyt.csv')
#Tracking File will hold the place of where the batch processor stop in case it 
#crashes it doesn't need to start from the beginning
tracking_file = os.path.join(folder_path, 'tracking.txt')
#This will catch the articles that create errors so that they can be 
#dealt with later and not stop the program
error_csv = os.path.join(folder_path,'error_nyt.csv')

#NOTE: This method may produce duplicates if a batch terminates early. Duplicates will
#need to be removed later

#Open Hugging Face Sentiment Pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

#Negative : -1 , POSITIVE: 1
#create new column in df with pos/neg and another with score
articles['sentiment'] = 0
articles['sentiment_score'] = 0.0
error_indices = []
# error_log = []
chunk_size = 5000 #modify batch size if you want

try:
  with open(tracking_file, 'r') as f:
    last_row = int(f.read().strip())
except FileNotFoundError:
  last_row = 0

successful_rows = []
error_rows = []

for i,(index,row) in enumerate(articles.iloc[last_row:].iterrows(),start = last_row):
  try:
    sentiment = sentiment_pipeline(row['abstract'])[0]
    articles.at[index,'sentiment'] = 'Positive' if sentiment['label'] == 'POSITIVE' else 'Negative'
    articles.at[index,'sentiment_score'] = sentiment['score']
    successful_rows.append(articles.loc[index])
  except Exception as e:
    error_rows.append({'index': index, 'error': str(e)})
  if (i + 1) % chunk_size == 0 or i + 1 == len(articles):  # Save when chunk is complete or at the end
            # Save successful rows to the output CS
    if successful_rows:
      chunk_df = pd.DataFrame(successful_rows)
      chunk_df.to_csv(output_file, mode='a', header=(i == 0), index=False)
      successful_rows = []  # Clear the successful rows list

            # Save error rows to the error CSV
    if error_rows:
      error_df = pd.DataFrame(error_rows)
      error_df.to_csv(error_csv, mode='a', header=(i == 0), index=False)
      error_rows = []  # Clear the error rows list

            # Update the tracking file with the last processed row index (successful and error rows included)
    with open(tracking_file, 'w') as f:
      f.write(str(i + 1))

#Read output to df so we can remove duplicates
df = pd.read_csv(output_file)
df.drop_duplicates(inplace = True)

#send 
df.to_csv(output_file,mode = 'w',header = articles.columns,index = False)

