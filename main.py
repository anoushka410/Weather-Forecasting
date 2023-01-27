#import string
import numpy as np 
import pandas as pd 
import datetime as dt
from datetime import timedelta
from pydantic import BaseModel
import requests
import json
import argparse
import time
import joblib
import schedule
from fastapi import FastAPI
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from sklearn.preprocessing import LabelEncoder
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.api import VAR
import logging


#Command line arguments for main function
parser = argparse.ArgumentParser()
parser.add_argument('--city', help= "Please enter name of the city")
args = parser.parse_args()


current_time = dt.datetime.now().replace(microsecond=0)

def get_data(city):
    day = 7
    try:
        print("Entered try block")
        for i in range(0,day):
            apitime = current_time-timedelta(days=i)
            apitime = str(apitime.date())
            Endpoint = f"http://api.weatherapi.com/v1/history.json?key=ad9765d12f724fdc88b104256220806&q={str(city)}&dt={str(apitime)}"
            end  = requests.get(Endpoint)
            data = json.loads(end.text)
            data2 = data['forecast']['forecastday'][0]
            df2 = pd.json_normalize(data2['hour'])
            le = LabelEncoder()
            df2['condition.text'] = le.fit_transform(df2['condition.text'])
            df2 = df2.drop(['is_day','pressure_in'], axis=1)

            if i > 0:
                last_df = last_df.append(df2, ignore_index=True)
            else:
                last_df = df2 
                
        print(last_df.columns)
        
        logging.info(f"Ingested weather data for {city}")
        print(f"Ingested weather data for {city}")

    except Exception as e:
        logging.info(f"{time} : Data not found for {city}")

    #Pre-processing        
    try:
        last_df.rename(columns = {'time':'index', 'temp_c':'temperature', 'condition.text':'condition'}, inplace = True)
        last_df = last_df.set_index('index')
        last_df.index = pd.to_datetime(last_df.index)  

        result = arima_forcast(last_df, city)
        
    except Exception as e:
        print(e)
   
    return result
    

def arima_forcast(last_df, city):
    today = last_df[str(dt.datetime.now().date())]

    try:
        #Splitting data into train and test
        train_df = last_df.drop(today.index).resample('H').mean().fillna(method='pad')
        test_df = today.resample('H').mean().fillna(method='pad')
        test_df.to_csv('test-data.csv')

        #Training the ARIMA model
        model = VAR(train_df)
        mv_model_fit = model.fit()
        joblib.dump(mv_model_fit, 'ARIMA_model.joblib')
        print("Stored model as joblib file")
        pred = mv_model_fit.forecast(mv_model_fit.endog, test_df.shape[0])
        days = pd.date_range(current_time, current_time + timedelta(1), freq='H')

        #Creating a dataframe of predictions
        pred_df = pd.DataFrame(index=range(0,len(pred)),columns=last_df.columns)
        for j in range(0,5):
            for i in range(0, len(pred)):
                pred_df.iloc[i][j] = pred[i][j]
        pred_df['Date'] = days[:24]
        pred_df.columns = pred_df.columns.to_flat_index()
        print(pred_df)

        #Storing predictions in json object
        results = pred_df.to_json(orient='records', date_format = 'iso')
        print("results: \n", results)

        logging.info(f"{current_time} : Prediction successful for {city}")
        return json.loads(results)

    except Exception as e:
        print("Error: ", e)
        logging.info(f"{current_time} : Prediction failed. {e}")

    
def send_single_message(sender, forcast):

    try:
        # create a Service Bus message
        message = ServiceBusMessage(forcast)
        # send the message to the queue
        sender.send_messages(message)
        print("Sent a single message")
        logging.info(f"{current_time} : Sent message to Service Bus.")

    except Exception as e:
        logging.info(f"{current_time} : Failed to send message to Service Bus with error: {e}")


def get_forecast():
    try:
        CONNECTION_STR = "Endpoint=sb://forecast1.servicebus.windows.net/;SharedAccessKeyName=forcast;SharedAccessKey=e3Q5kl6BFZ/2mr6T5ZJfgbPUzKPIdDNnNdx962n+AO0=;EntityPath=forcast"
        QUEUE_NAME = "forcast"
        results_forcast = {"Location": str(args.city), "Forecast": (get_data(args.city))}
        # create a Service Bus client using the connection string
        servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)
        print("Connection with Service Bus established.")
        logging.info("Connection with Service Bus established.")
        with servicebus_client:
            # get a Queue Sender object to send messages to the queue
            sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
            with sender:
                # send one message        
                send_single_message(sender, json.dumps(results_forcast))

    except Exception as e:
        logging.info(f"{current_time} : Failed to establish connection with Service Bus. {e}")


app = FastAPI()

class city_arg(BaseModel):
    city: str

@app.post('/predict')
async def predict_temp(data: city_arg):
    try:
        CONNECTION_STR = "Endpoint=sb://forecast1.servicebus.windows.net/;SharedAccessKeyName=forcast;SharedAccessKey=e3Q5kl6BFZ/2mr6T5ZJfgbPUzKPIdDNnNdx962n+AO0=;EntityPath=forcast"
        QUEUE_NAME = "forcast"
        results_forcast = {"Location": str(data.city), "Forecast": (get_data(data.city))}
        # create a Service Bus client using the connection string
        servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)
        logging.info("Connection with Service Bus established.")
        with servicebus_client:
            # get a Queue Sender object to send messages to the queue
            sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
            with sender:
                # send one message        
                send_single_message(sender, json.dumps(results_forcast))

    except Exception as e:
        logging.info(f"{current_time} : Failed to establish connection with Service Bus. {e}")
    response = get_forecast(data.city)
    print(data.city)
    return results_forcast


# if __name__=="__main__":

#     schedule.every(10).seconds.do(get_forecast)
#     get_forecast()

    # while True:
 
    #     Checks whether a scheduled task is pending to run or not
    #     schedule.run_pending()
    #     time.sleep(1)