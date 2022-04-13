#!env/bin/python

import json 
import os 
import random
import psycopg2 as pg
import awswrangler.secretsmanager as awssm 


# read rules from db and write to s3

database_name = "main"
table_name = "cities"
username = sm.get_secret_json( "postgres-database" ).get( "username" )
password = sm.get_secret_json( "postgres-database" ).get( "password" )
port = "5432"
host_name = "somehost"


def lambda_handler(event, context): 

    cxn = pg.connect( user=username, 
                password=password, 
                host=host_name, 
                port=port, 
                database=database_name)

    query_create_table = f"create table cities ( ix serial primary key, names varchar(50) unique not null );"
    query_insert_data = f"insert into {table_name} (city) values ('Washington'), ('Philadelphia'), ('New York'), ('Chicago'), ('Los Angeles'), ('Seattle'), ('Portland'), ('Dallas'), ('Miami'), ('Charlotte');"

    csr = cxn.cursor()
    csr.execute( query_create_table ) 
    csr.execute( query_insert_data )
    cxn.commit()
    len_table = csr.rowcount 
    random_record = random.randint(1, len_table)
    query_random_data = f"select names from cities where ix = {random_record};"
    cxn.execute( query_random_data )

    random_record = cxn.fetchall()

    print( f"{len_table} rows inserted sucessfully" ) 

    return {"statusCode" : 200, 
            "body" : f"a random city is {random_record}" } 
