import geopy.distance
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
import streamlit as st

#FUNCTIONS====================================================================================================
#FUNCTION: Calculate distance between 2 hotel | para: locationId
@st.cache(allow_output_mutation=True)
def getDistance(df, locationId_1, locationId_2):
  coords_1 = (df.latitude[locationId_1], df.longitude[locationId_1])
  coords_2 = (df.latitude[locationId_2], df.longitude[locationId_2])

  return geopy.distance.geodesic(coords_1, coords_2).km

# Filter out hotels in specified parentId
@st.cache(allow_output_mutation=True)
def getHotelByParent(df, parentGeoId):
  result = df[df['parentGeoId']==parentGeoId]
  return result.index.tolist()

# Get Hotels arround the specified one
@st.cache(allow_output_mutation=True)
def getHotelNearBy(df, locationId, limit):
  try:
    parentId = df.parentGeoId[locationId]
    list_result = []
    list_hotel = getHotelByParent(df, parentId)
    for hotel in list_hotel:
      try:
        distance = getDistance(df, locationId, hotel)
        if distance <= limit:
          list_result.append(hotel)
      except:
        continue
    if len(list_result) < 5:
      for hotel in list_hotel:
        try:
          distance = getDistance(df, locationId, hotel)
          if distance <= limit*2 and hotel not in list_result:
            list_result.append(hotel)
        except:
          continue
    return list_result
  except:
    return []

# Getting coordinates from location name
@st.cache(allow_output_mutation=True)
def getCoor(location):
  loc = Nominatim(user_agent="GetLoc")
  # entering the location name
  try: 
      getLoc = loc.geocode(location,addressdetails=True)
  except: 
      result = 'Not Found'
  return getLoc.latitude,getLoc.longitude

@st.cache(allow_output_mutation=True)
def getDistanceFrom(coor_1, coor_2):
  return geopy.distance.geodesic(coor_1, coor_2).km

# Search Hotel nearby a specified address
@st.cache(allow_output_mutation=True)
def searchHotel(df, address, distance):
  lat, lont = getCoor(address)
  coor = (lat,lont)
  print(coor)
  df_hotel = df[(abs(df['latitude']-lat)<1) & (abs(df['longitude']-lont)<1)]
  df_hotel['coordinate'] = df_hotel.apply(lambda x: (x.latitude,x.longitude), axis=1)
  df_hotel['distance'] = df_hotel['coordinate'].apply(lambda x: getDistanceFrom(coor,x))
  df_hotel = df_hotel[df_hotel['distance'] <= distance]
  # df_hotel = df_hotel.sort_values(by='distance', ascending=True)
  return df_hotel

@st.cache(allow_output_mutation=True)
def getUserPreference(df_user, user_id):
  try:
    user_pref = df_user[df_user['userId']==user_id]
    return user_pref['features'].values[0]
  except:
    return [0 for i in range(5)]
#====================================================================================================

# Load the data
df_user = pd.read_csv('Dataset/User_Preferences.csv')
df_hotel = pd.read_csv('Dataset/Hotel_Profile.csv')
df_coor = pd.read_csv('Dataset/hotel_coordinate.csv')

df_user['features'] = df_user.apply(lambda x: np.array(x[1:]), axis=1)
df_user = df_user[['userId', 'features']]

# df_hotel['features'] = df_hotel.apply(lambda x: np.array(x[1:]), axis=1)
# df_hotel = df_hotel[['locationId', 'features']]

st.set_page_config(page_title='🏨 Hotel Recommend System', page_icon='🏨', layout='wide', initial_sidebar_state='auto')

# Header
st.header('Hotel Recommend System - ECom20')
st.subheader('This is a hotel recommend system using scalar product of user and hotel')

# Get the user input
user_id = st.selectbox('Select a user', df_user.userId.unique())
address = st.text_input('Enter your address', 'Đại học Kinh tế Luật')
button = st.button('Get Recommendations')

# Get top 10 recommendations
@st.cache(allow_output_mutation=True)
def get_top_10(user_id):
    df_result = df[[user_id, 'locationId']].sort_values(by=user_id, ascending=False)[:10]    
    return df_result
    
if button:
    st.write('Top 10 recommendations for user', user_id, 'are:')
    user_pref = getUserPreference(df_user, user_id)
    st.write('User preferences', user_pref)
    df_result = searchHotel(df_coor, address, 5)
    df_result = df_result.reset_index(drop=True)
    df_result = df_result.merge(df_hotel, on='locationId', how='left')
    df_result.fillna(0, inplace=True)
    df_result['features'] = df_result.apply(lambda x: np.array(x[-5:]), axis=1)
    df_result['score'] = df_result['features'].apply(lambda x: np.dot(user_pref, x))
    df_result = df_result.sort_values(by=['score', 'distance'], ascending=[False, True])
    # st.write(df_result)
    for i in range(len(df_result)):
      st.write(f'<hr>', unsafe_allow_html=True)    
      st.write(i+1)
      st.write(f'<p style="font-size:20px"><a href="https://www.tripadvisor.com.vn/g{df_result.iloc[i]["parentGeoId"]}-d{df_result.iloc[i]["locationId"]}">{df_result.iloc[i]["name"]}</a> - {df_result.iloc[i]["distance"]}km</p>', unsafe_allow_html=True)
    # st.write(get_top_10(user_id))