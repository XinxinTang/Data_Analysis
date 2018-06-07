# @author: Xinxin Tang
# email: xinxin.tang92@gmail.com

from mysql import connector as con
import datetime
import requests
import pandas as pd
from sqlalchemy import engine


def get_live():  # 16s
    db = con.connect(user='cogo_read_only', password='N&f#vSq9',database='liveworks',
                      host='data-engineer-rds.czmkgxqloose.us-east-1.rds.amazonaws.com')
    cursor = db.cursor()
    cursor.execute('select COUNT(emd5) from `cogo_list_v1`')
    count = cursor.fetchone()[0]
    cursor.execute('select emd5, job, company from `cogo_list_v1`')
    arr_all = list(cursor.fetchone() for i in range(count))
    db.close()

    return arr_all


def get_cogo():
    host = "EC2Co-EcsEl-MT18UEPNPS93-1308701016.us-east-1.elb.amazonaws.com"
    re = requests.get('http://{}:8000/records?page={}'.format(host, 1))
    page = re.json()["num_pages"]

    arr_all = []
    for i in range(1, page+1):
        re = requests.get('http://{}:8000/records?page={}'.format(host, i))
        rows = re.json()["rows"]
        for j in range(len(rows)):
            emd, job, company = rows[j]["emd5"], rows[j]["job"], rows[j]["company"]
            arr_all.append((emd, job, company))

    return arr_all


def compare_users(all_cogo, all_live):
    cogo_col = ['emd5', 'job_cogo', 'company_cogo']
    live_col = ['emd5', 'job_live', 'company_live']
    df_cogo = pd.DataFrame(all_cogo, columns=cogo_col)
    df_live = pd.DataFrame(all_live, columns=live_col)

    # answer for question 1
    cogo_user = set(df_cogo.emd5)
    live_user = set(df_live.emd5)
    print("The number of users within both datasets: ", len(list(cogo_user & live_user)))
    print("The number of users unique to Cogo's dataset:", len(list(cogo_user - live_user)))
    print("The number of users unique to Livework's dataset:", len(list(live_user - cogo_user)))

    # answer for question 2
    intersection_user = list(cogo_user & live_user)
    joined_df = pd.merge(df_cogo[df_cogo.emd5.isin(intersection_user)], df_live[df_live.emd5.isin(intersection_user)],
                         how='left', on='emd5')
    joined_df['is_job_diff'] = joined_df.apply(lambda x: 1 if x.job_cogo != x.job_live else 0, axis=1)
    intersection_rate = len(joined_df[joined_df.is_job_diff == 1]) * 1.0 / len(intersection_user)
    print("The percent of users with different job titles in intersection part:", intersection_rate)
    joined_df['cogo_job/company'] = joined_df.apply(lambda x: {x.job_cogo: x.company_cogo}, axis=1)
    joined_df['live_job/company'] = joined_df.apply(lambda x: {x.job_live: x.company_live}, axis=1)
    joined_df = joined_df[['emd5', 'cogo_job/company', 'live_job/company']]
    print(joined_df.head(10))
    # joined_df.to_csv("output.csv")

    # connection = con.connect(host='10.33.69.53', user='root', passwd='123456', db='test', charset='utf8')
    # joined_df.to_sql("joined_df", connection, flavor='mysql', if_exists='append')


if __name__ == "__main__":
    time_start = datetime.datetime.now()
    data_live = get_live()
    data_cogo = get_cogo()
    compare_users(data_cogo, data_live)
    time_end = datetime.datetime.now()
    print("Total runtime: {} seconds".format((time_end-time_start).seconds))