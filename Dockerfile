FROM apache/airflow:2.10.3
ADD requirements.txt .
RUN pip install -r requirements.txt
RUN pip install redis
RUN pip install python-dotenv
RUN pip install awscli
RUN pip install apache-airflow-providers-snowflake
RUN pip install apache-airflow-providers-amazon
RUN pip install snowflake-connector-python