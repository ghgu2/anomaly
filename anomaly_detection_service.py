import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# Функция для обнаружения аномалий
def detect_anomalies(data, threshold=3):
    data['rolling_mean'] = data['value'].rolling(window=7).mean()
    data['rolling_std'] = data['value'].rolling(window=7).std()
    data['anomaly'] = np.abs(data['value'] - data['rolling_mean']) > threshold * data['rolling_std']
    return data

# Загрузка данных
st.title('Сервис обнаружения аномалий во временном ряду')
uploaded_file = st.file_uploader("Загрузите TSV файл", type="tsv")

if uploaded_file is not None:
    # Предоставить пользователю выбор кодировки
    encoding = st.sidebar.selectbox('Выберите кодировку файла', options=['utf-8', 'windows-1252', 'latin1', 'ascii'], index=0)
    
    # Попробуйте загрузить файл с выбранной кодировкой
    try:
        data = pd.read_csv(uploaded_file, sep='\t', encoding=encoding, parse_dates=['time'])
    except Exception as e:
        st.error(f"Ошибка загрузки файла с кодировкой {encoding}: {e}")
        st.stop()
    
    # Выбор порога пользователем
    threshold = st.sidebar.slider('Выберите порог для обнаружения аномалий (в стандартных отклонениях)', 1.0, 5.0, 3.0)

    # Обнаружение аномалий
    data = detect_anomalies(data, threshold)

    # Отображение таблицы с аномалиями
    st.subheader('Таблица аномалий')
    anomaly_table = data[data['anomaly']]
    st.write(anomaly_table[['time', 'value']])
    
    # Фильтрация данных по заданному временному интервалу
    st.subheader('Результирующий график')
    start_date = st.date_input("Начальная дата", data['time'].min().date())
    end_date = st.date_input("Конечная дата", data['time'].max().date())

    if start_date <= end_date:
        filtered_data = data[(data['time'] >= pd.Timestamp(start_date)) & (data['time'] <= pd.Timestamp(end_date))]
    else:
        st.error("Некорректный временной интервал: начальная дата больше конечной даты.")
        st.stop()

    # Построение графика
    fig = px.line(filtered_data, x='time', y='value', title='Временной ряд с аномалиями')
    anomaly_points = filtered_data[filtered_data['anomaly']]
    fig.add_scatter(x=anomaly_points['time'], y=anomaly_points['value'], mode='markers', name='Аномалии',
                    marker=dict(color='red', size=10))
    st.plotly_chart(fig)

    # Функция для выгрузки данных в формате XLS
    def convert_to_excel(df):
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        return output.getvalue()

    # Выгрузка результатов
    if st.button('Выгрузить результаты в XLS'):
        result_data = filtered_data[['time', 'value', 'anomaly']]
        excel_data = convert_to_excel(result_data)
        st.download_button(label='Скачать XLS', data=excel_data, file_name='anomaly_detection_results.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
else:
    st.info("Пожалуйста, загрузите TSV файл.")