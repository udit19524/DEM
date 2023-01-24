import uvicorn
from fastapi import FastAPI
import os
import logging
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi_sqlalchemy import db
from models import User as ModelUser
from schema import User as SchemaUser
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
import psycopg2.extras as extras
import ipaddress
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.sql import text
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import fashion_mnist
from fastapi.responses import StreamingResponse

from io import BytesIO


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
logging.getLogger().setLevel(logging.INFO)


app = FastAPI()
#Pulling DATABASE URL env configs
app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])

#example:1 to show how connection can be created and used
engine = create_engine(os.environ["DATABASE_URL"])
connection = engine.connect()

#example:2 to show how connection can be created
conn = psycopg2.connect(
    host="db", user="postgres", password="postgres", database="postgres", port=5432
)


def insert_data(df, table: str):
    """Insert raw data into raw table for all uploads"""
    
    tuples = [tuple(x) for x in df.to_numpy()]

    cols = ",".join(list(df.columns))
    logging.info(f"columns {cols}")

    # SQL query to execute
    query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    cursor = conn.cursor()
    try:
        logging.info(f"About to insert, {query}, {tuples}")
        extras.execute_values(cursor, query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error("BOOOO Error: %s" % error)
        conn.rollback()
        cursor.close()
    logging.info("the dataframe is inserted")
    cursor.close()


def validate_ip_address(address:str):
    """validate ip address and return true or false"""
    try:
        ip = ipaddress.ip_address(address)
        return True
    except ValueError:
        logging.info(f"Invalid ipaddress {address}")
        return False


def validate_email_address(email: str):
    """validate email address and return true or false"""
    
    try:
        # validate and get info
        v = validate_email(email)
        email = v["email"]
        return True
    except EmailNotValidError as e:
        # email is not valid
        logging.info(f"Invalid email {email}")
        return False


def transform_data(df, result_df):
    """Perfrom transformation and insert into PG database"""
    
    for index, row in df.iterrows():
        insert_row = {
            "id": index,
            "full_name": row["first_name"] + " " + row["last_name"],
            "valid_ip": validate_ip_address(row["ip_address"]),
            "valid_email": validate_email_address(row["email"]),
        }
        result_df = result_df.append(insert_row, ignore_index=True)
    return result_df


@app.post(
    "/upload_user/", tags=["DEM USERS"], description="ETL for all valid user data"
)
async def create_upload_file(file: UploadFile = File(...)):
    logging.info(
        f"Uploaded file is {file.filename} and need to write to {os.environ['DATABASE_URL']}"
    )
    #read data into dataframe
    excel_data_df = pd.read_excel(file.file)
    excel_transform_data = pd.DataFrame(
        columns=["id", "full_name", "valid_email", "valid_ip"]
    )
    #save raw data into PG table
    insert_data(excel_data_df, "users")
    #transform and save new data into PG table
    excel_transform_data = transform_data(excel_data_df, excel_transform_data)
    insert_data(excel_transform_data, "user_transform")

    return {"Processed number of rows": excel_data_df.shape[0]}


@app.get(
    "/get_valid_users",
    tags=["DEM USERS"],
    description="Returns all user with valid IP and email",
)
async def valid_user():
    """Returns how many users have valid email and ip address"""
    
    #demonstrating sqlalchemy.sql
    valid_user_sql = text(
        f"SELECT DISTINCT full_name  FROM user_transform WHERE LOWER(valid_email) = LOWER('TRUE') and LOWER(valid_ip) = LOWER('True')"
    )
    valid_user_df = pd.read_sql(valid_user_sql, connection)
    valid_user_list = []
    for _, user_id in valid_user_df.iterrows():
        valid_user_list.append(user_id["full_name"])
    return valid_user_list


@app.get(
    "/get_invalid_users",
    tags=["DEM USERS"],
    description="Returns all user with invalid IP and email",
)
async def invalid_user():
    """Returns how many users have do not have valid email or ip address"""
    
    #demonstrating sqlalchemy.sql
    invalid_user_sql = text(
        f"SELECT DISTINCT full_name  FROM user_transform WHERE LOWER(valid_email) <> LOWER('TRUE') or LOWER(valid_ip) <> LOWER('True')"
    )
    invalid_user_df = pd.read_sql(invalid_user_sql, connection)
    invalid_user_list = []
    for _, user_id in invalid_user_df.iterrows():
        invalid_user_list.append(user_id["full_name"])
    return invalid_user_list


@app.get(
    "/get_fashion_plot",
    tags=["DEM ML PLOT"],
    description="Returns training set and display the grayscale",
)
async def plot_fashion():
    """Prepping images using fashion_minst dataset"""
    
    (X_train, Y_train), (X_test, Y_test) = fashion_mnist.load_data()
    logging.info("Fashion MNIST Dataset Shape:")
    logging.info("X_train: " + str(X_train.shape))
    logging.info("Y_train: " + str(Y_train.shape))
    logging.info("X_test:  " + str(X_test.shape))
    logging.info("Y_test:  " + str(Y_test.shape))

    num_row = 3
    num_col = 5

    # get a segment of the dataset
    num = num_row * num_col
    images = X_train[:num]
    labels = Y_train[:num]

    # plot images
    fig, axes = plt.subplots(num_row, num_col, figsize=(1.5 * num_col, 2 * num_row))
    for i in range(num_row * num_col):
        ax = axes[i // num_col, i % num_col]
        ax.imshow(images[i], cmap="gray")
        ax.set_title("Fashion: {}".format(labels[i]))
    plt.tight_layout()

    #save and return the plotted images
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    
    return StreamingResponse(buf, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
