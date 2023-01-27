from azure.servicebus import ServiceBusClient, ServiceBusMessage
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import json

CONNECTION_STR = "Endpoint=sb://forecast1.servicebus.windows.net/;SharedAccessKeyName=read_forcast;SharedAccessKey=XD75bC5ff+FQSO0iiR4HVKbIwyeGcKcAiX/gJbMFMqs=;EntityPath=forcast"
QUEUE_NAME = "forcast"

# create a Service Bus client using the connection string
servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)

all_msgs = {}

while True:
    with servicebus_client:
        # get the Queue Receiver object for the queue
        receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME, max_wait_time=5)
        with receiver:
            for msg in receiver:
                print(f"messg {type(msg)}")
                message=json.loads(str(msg))
                print(message)

                print(message['Forecast'][0].keys())
                print(message['Forecast'][0].values())
                city = message['Location']

                all_msgs[city] = message['Forecast']

                names = list(message['Forecast'][0].keys())
                values = list(message['Forecast'][0].values())

                colors = ['r','g','b']

                # selectbox = st.selectbox(
                #     "Select your city",
                #     ["Mumbai", "Pune", "Bangalore", "Hyderabad", "Chennai"]
                # )
                
                st.header(f"Today's Weather Forecast for {city} \n\n")

                

                chart_data = pd.DataFrame(
                np.random.randn(20, 3),
                columns=['a', 'b', 'c'])

                #st.write(chart_data)

                #st.line_chart(new_df)

                #st.bar_chart(new_df)



                # temprature=[]
                # date=[]
                # for i in message['Forecast']:
                #     print(i['temprature'],i['Date'])
                #     #print(time.strftime("%B %d %Y", str(i['Date'])))
                #     temprature.append(i['temprature'])
                #     date.append(i['Date'])

                # fig = plt.figure(figsize=(100,50))
                # sns.lineplot(x=date, y=temprature)

                #chart_data = pd.DataFrame(list(message['Forcast'][0].values()),columns=list(message['Forcast'][0].keys()))
                #plt.bar(range(len(message['Forcast'][0])), values, tick_label=names, color=colors)
                #st.bar_chart(chart_data)

                #st.pyplot(fig)
                
                #st.write(message['Forecast'])
                # complete the message so that the message is removed from the queue
                receiver.complete_message(msg)
            
    print(all_msgs)
    print("----------------------------------------------------------------------")
    print(list(all_msgs.keys()))

    date = []
    temp = []
    rain = []
    cloud = []
    condition = []
    humidity = []

    for i in all_msgs['Mumbai']:
        date.append(i['Date'])
        temp.append(i['temperature'])
        rain.append(i['chance_of_rain'])
        cloud.append(i['cloud'])
        condition.append(i['condition'])
        humidity.append(i['humidity'])

    mumbai_df = pd.DataFrame({"Temperature": temp, "Humidity": humidity, "Cloud": cloud, "Rain": rain, "Condition": condition})

    print("------------------------------------------------------------------------------------")

    print(mumbai_df)

    st.write(mumbai_df)
    st.line_chart(mumbai_df)
