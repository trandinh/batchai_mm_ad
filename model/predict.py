import pyodbc
import numpy as np
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from azure.storage.blob import BlobServiceClient
import pickle
import sys
import json
import datetime
import pandas as pd

# query params
device = sys.argv[1]
tag = sys.argv[2]
ts_from = sys.argv[3]
ts_to = sys.argv[4]

# input/output params
config_file = sys.argv[5]
with open(config_file) as f:
    j = json.loads(f.read())

sql_con_string = j['sql_con_string']
sql_query = j['sql_query']
blob_account = j['blob_account']
blob_key = j['blob_key']
models_blob_container = j['models_blob_container']
predictions_blob_container = j['predictions_blob_container']

model_name = 'model_{0}_{1}'.format(device, tag)

# get data
cnxn = pyodbc.connect(sql_con_string)
query = sql_query.format(device, tag, ts_from, ts_to)


def get_vals(cursor, n=1000):
    while True:
        results = cursor.fetchmany(n)
        if not results:
            break
        for result in results:
            yield result


cursor = cnxn.cursor()
cursor.execute(query)
recs = [(x[0], str(x[1])) for x in get_vals(cursor, 1000)]
tss = [x[1] for x in recs]
vals = np.array([x[0] for x in recs])

# load model
account_url = "https://%s.blob.core.windows.net/"%(blob_account)
blob_service = BlobServiceClient(account_url=account_url, credential=blob_key)

blob = blob_service.get_blob_client(models_blob_container, model_name)
downloader = model_blob.download_blob(0)
with BytesIO() as f:
	 downloader.readinto(f)
     pipe = pickle.loads(f)
	    
# predict
preds = pipe.predict(vals.reshape(-1, 1))
preds = np.where(preds == 1, 0, 1) # 1 indicates an anomaly, 0 otherwise

# csv results
res = pd.DataFrame({'TS': tss,
                    'Device': np.repeat(device, len(preds)),
                    'Tag': np.repeat(tag, len(preds)),
                    'Val': vals,
                    'Prediction': preds})
res = res[['TS', 'Device', 'Tag', 'Val', 'Prediction']]

res_file_name = 'preds_{0}_{1}_{2}_{3}'.format(device,
                                               tag,
                                               ts_from.replace('-', ''),
                                               ts_to.replace('-', ''))
    
# save predictions
blob = blob_service.get_blob_client(predictions_blob_container, res_file_name)
output = df.to_csv (index=None, encoding = "utf-8")

blob.upload_blob(output, overwrite=True, blob_type="BlockBlob")
