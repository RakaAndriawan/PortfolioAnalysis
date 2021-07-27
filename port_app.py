## Package for Web App
import streamlit as st
import joblib, os
import datetime
import string

## Import Custom Functions
from port_script import *

## Set Page Config
st.set_page_config(page_title="Portfolio Anda", page_icon="🧊", layout="wide", initial_sidebar_state="expanded")

## Get Options for Tickers
tickers = get_ticker()
ticker_list = tickers['Kode'] + ' - ' + tickers['Nama Perusahaan']

def main():
    
    ## Base Input: Tickers, Start_Date, Sections
    ## Organize Sidebar
    st.title('Analisa dan Simulasi Portfolio Investasi Saham')
    sh1, sh2 = st.beta_columns(2)
    with sh1:
        st.info('**Susun Portfolio Anda di Sidebar**')
    st.sidebar.header('Susun Portfolio Anda')
    section = st.sidebar.radio('Pilih Halaman:', ('Performa Portfolio', 'Backtesting Portfolio'), index = 0)
    myPicks = st.sidebar.multiselect(label = 'Pilih Saham (Maks. 5)', options = ticker_list)
    start_date = st.sidebar.date_input(label = 'Tanggal Mulai', value = datetime.date.today() - datetime.timedelta(365))
    st.sidebar.header('Kontribusi')
    st.sidebar.info('''Ini adalah project **open source** yang dapat anda **bantu kembangkan** dengan memberikan **feedback** melalui email **raka.andria1@gmail.com** atau github **RakaAndriawan**''')
    st.sidebar.header('Tentang Saya')
    st.sidebar.info('''Aplikasi ini dibuat oleh Raka Andriawan, **penggemar Data Science**. Anda dapat mengetahui lebih banyak tentang saya pada **akun Linkedn saya**''')
    
    ## Check Base Input
    num_stocks = len(myPicks)
    if num_stocks > 5 or num_stocks < 2:
        with sh2:
            st.warning('**Portfolio diisi 2 hingga 5 saham**')
            return None
        
    ## Collect Datasets
    with sh2:
        with st.spinner('Tunggu Proses Download Data Ya!'):
            myPicks = [x.split(' - ')[0] for x in myPicks]
            recent_data = get_data(myPicks, start_date)
    
    ## Rendering First Page
    if section == 'Performa Portfolio':

        st.markdown('''<p style="text-align:center;">
        <em><b>Halaman ini bertujuan</b> untuk melihat <b>performa portfolio</b> yang anda susun
        <b>berdasarkan performa di masa lalu</b><br>
        Ingat bahwa performa masa lalu <b>tidak mencerminkan hasil yang menjanjikan di masa depan</b><br>
        Selalu <b>berinvestasi</b> dengan <b>penuh pertimbangan</b></em></p>
        ''', unsafe_allow_html = True)
        
        ## Organize Layout
        L0 = st.beta_container()
        inp_weight = st.beta_columns(num_stocks)
        L1A, L1B = st.beta_columns(2)
        L2A, L2B = st.beta_columns([1,5])
        st.header('**Resiko Portfolio Anda**')
        L3A, L3B = st.beta_columns(2)
        
        ## Ask for Custom Weights
        L0.subheader('**Tentukan Komposisi Portfolio Anda (%)**')
        weights = np.zeros(num_stocks)
        for i in range(0,num_stocks):
            weights[i] = inp_weight[i].number_input(myPicks[i], min_value = 0.0, max_value = 100.0, value = 100/num_stocks, step = 0.1)        
            
        if sum(weights) != 100:
            warn = 'Pastikan Total Komposisi 100%! Komposisi Saat Ini : {}%'.format(sum(weights))
            st.text(warn)
            return None

        ## Calculation Process for First Page
        with sh2:
            with st.spinner('Tunggu Proses Kalkulasi Ya!'):
                weights = [x/100 for x in weights]
                result = core_plot_data(recent_data, weights)
                
        ## Visualize DataFrame
        with L1A:
            st.subheader('**Data Returns Portfolio**')
            display_data = result[2]
            display_data.index = pd.to_datetime(display_data.index, format = '%m/%d/%Y').strftime('%Y-%m-%d')
            L1A.dataframe(display_data.style.applymap(negative_red))
            display_data.index = pd.DatetimeIndex(display_data.index)
            
            ## Create Download Link
            if st.button('Download Data Return', key = 'first_df'):
                tmp_download_link = download_link(display_data, 'portfolio_returns.csv', 'DOWNLOAD!')
                st.markdown(tmp_download_link, unsafe_allow_html=True)
        
        ## Highlights Key Values
        with L1B:
            st.subheader('**Summary Performa Portfolio**')
            kpi = result[0]
            keys = list(kpi.keys())
            
            ## Returns
            if kpi[keys[0]] < 0 and kpi[keys[1]] < 0:
                st.error('**{}** : {}% || **{}** : {}%'.format(keys[0], kpi[keys[0]], keys[1], kpi[keys[1]]))
            elif kpi[keys[0]] < 0 or kpi[keys[1]] < 0:
                st.warning('**{}** : {}% || **{}** : {}%'.format(keys[0], kpi[keys[0]], keys[1], kpi[keys[1]]))
            elif kpi[keys[0]] >= 0 and kpi[keys[1]] >= 0:
                st.success('**{}** : {}% || **{}** : {}%'.format(keys[0], kpi[keys[0]], keys[1], kpi[keys[1]]))                

            ## Volatility and Sharpe Ratio
            if kpi[keys[3]] < 0:
                st.error('**{}** : {}% || **{}** : {}'.format(keys[2], kpi[keys[2]], keys[3], kpi[keys[3]]))
            elif kpi[keys[3]] < 1:
                st.warning('**{}** : {}% || **{}** : {}'.format(keys[2], kpi[keys[2]], keys[3], kpi[keys[3]]))
            elif kpi[keys[3]] >= 1:
                st.success('**{}** : {}% || **{}** : {}'.format(keys[2], kpi[keys[2]], keys[3], kpi[keys[3]]))
                
            ## Risk Metrics
            st.info('**{}** (95) : {}% || **{}** (95) : {}% || **{}** : {}%'.format(keys[4], kpi[keys[4]], keys[5], kpi[keys[5]], keys[6], kpi[keys[6]]))
            
        ## Checkbox Assets to Plots
        with L2A:
            st.subheader('**Pilih Variabel untuk Divisualisasi**')
            var = np.zeros(num_stocks + 1)
            var[0] = st.checkbox('Portfolio', value = True)   
            for i in range(1,(num_stocks + 1)):
                var[i] = st.checkbox(myPicks[i-1])
            st.markdown('Gunakan slider dibawah plot untuk mengubah range waktu dari plot')
            
            ## Create Download Link
            if st.button('Download Data Return Kumulatif', key = 'fifth_df'):
                tmp_download_link = download_link(result[1], 'cumulative_returns.csv', 'DOWNLOAD!')
                st.markdown(tmp_download_link, unsafe_allow_html=True)
            
        ## Cumulative Returns Plot
        with L2B:
            my_var = ['Portfolio'] + result[5]
            my_key_var = [my_var[i] for i in range(0,len(my_var)) if var[i] == 1]
            if len(my_key_var) > 0:
                plot_cum_return = asset_cumulative_return(result[1], my_key_var)
                st.plotly_chart(plot_cum_return, use_container_width = True)
          
        ## Correlation Plot
        with L3A:
            st.markdown('''<p style="text-align:justify;">
            Hubungan antara satu saham individual dengan yang lainya juga dapat memainkan peran dalam menyusun portfolio anda.
            Anda dapat memilih saham yang berhubungan negatif untuk meminimalisir penurunan nilai portfolio anda.
            Anda juga dapat memilih saham yang berhubungan secara positif untuk memaksimalkan return yang anda bisa dapatkan.
            Tidak jarang juga, saham yang dipilih tidak memiliki hubungan apapun untuk meminimalkan resiko<br>
            <b>Strategi Ada Di Tangan Anda</b></p>''', unsafe_allow_html = True)
            plot_corr = asset_corr_plot(result[4], result[5])
            st.plotly_chart(plot_corr)
        
        with L3B:
            risk_plot = st.selectbox('Pilih Grafik untuk Menggambarkan Resiko Portfolio Anda',
                         ['Rolling Volatilitas Annual', 'VaR dan CVaR', 'Drawdown'], index = 1)
            
            ## Rolling Volatilitas Annual
            if risk_plot == 'Rolling Volatilitas Annual':
                st.markdown('''<p style="text-align:justify;">
                Rolling Volatilitas Annual merupakan suatu teknik untuk mengestimasi nilai volatilitas annual berdasarkan jangka waktu tertentu.
                Volatilias Annual sendiri merupakan ukuran yang digunakan untuk mengestimasi fluktuasi nilai return selama setahun.
                Semakin besar nilai volatilitas annual maka dapat dikatakan performa portfolio anda semakin tidak stabil.
                </p>''', unsafe_allow_html = True)
                window = st.slider('Pilih Rentang Waktu Rolling Volatilitas Annual', min_value = 2, max_value = 30,  value = 5)
                plot_rolling = rolling_volatility(result[2], window)
                st.plotly_chart(plot_rolling, use_container_width = True)
            
            ## Histogram VaR dan CVaR
            if risk_plot == 'VaR dan CVaR':
                alpha = st.slider('Pilih Level Kepercayaan Anda (%)', min_value = 90, max_value = 99,  value = 95)
                plot_hist, risk = var_cvar(result[2], alpha)
                st.markdown('''<p style="text-align:justify;">
                Nilai VaR dan CVaR merupakan ukuran yang digunakan untuk mengestimasi kemungkinan kerugian berdasarkan level kepercayaan tertentu. Sebagai contoh pada plot anda, nilai VaR pada level kepercayaan {}% menyatakan bahwa terdapat {}% kemungkinan nilai investasi anda turun lebih besar dari {}% dalam satu hari. Sedangkan nilai CVaR pada level kepercayaan yang sama menyatakan bahwa pada {}% kondisi terburuk, rata-rata kerugian anda sebesar {}% dalam satu hari.
                </p>'''.format(alpha, (100-alpha), round(-(risk[0]*100), 3), (100-alpha), round(-(risk[1]*100), 3)),
                unsafe_allow_html = True)
                st.plotly_chart(plot_hist, use_container_width = True)
                
            ## Max Drawdown
            if risk_plot == 'Drawdown':
                st.markdown('''<p style="text-align:justify;">
                Drawdown adalah penurunan nilai return kumulatif anda, atau penurunan nilai portfolio anda. Sedangkan Max Drawdown adalah penurunan maksimum nilai portfolio anda dari titik tertinggi ke titik terendak, sebelum bisa ke titik tertinggi lagi. Nilai ini dapat digunakan untuk mengetahui seberapa besar kerugian yang dapat kita terima dalam kondisi terbaik portfolio kita.
                </p>''', unsafe_allow_html = True)
                plot_drawdown = drawdown_vis(result[3])
                st.plotly_chart(plot_drawdown, use_container_width = True)

    ## Render Process for Second Page
    if section == 'Backtesting Portfolio':
        
        st.markdown('''<p style="text-align:center;">
        <em><b>Halaman ini bertujuan</b> untuk menentukan <b>komposisi portfolio</b> yang <b>tepat</b><br>
        Sesuai dengan <b>return</b> dan <b>resiko</b> yang diharapkan <b>berdasarkan performa di masa lalu</b><br>
        Ingat bahwa performa masa lalu <b>tidak mencerminkan hasil yang menjanjikan di masa depan</b><br>
        Selalu <b>berinvestasi</b> dengan <b>penuh pertimbangan</b></em></p>
        ''', unsafe_allow_html = True)
        
        ## Organize Layout
        L1A, L1B =  st.beta_columns([1.5,1])
        L2 = st.beta_container()
        
        with L1B:
            
            ## Ask for Input: Expected Return and Risk Free Rate
            st.subheader('**Masukkan Input Disini**')
            exp_value = st.number_input('Ekspektasi Nilai Return Annual', min_value = 0.0, max_value = 100.0, value = 20.0, step = 0.1)
            risk_free = st.number_input('Nilai Risk Free Return', min_value = 0.0, max_value = 100.0, value = 0.0, step = 0.1)
            
            ## Explain Strategy
            st.subheader('**Penjelasan Strategi Portfolio**')
            st.markdown('''<p style="text-align:justify;">
            Portfolio yang terdiri dari beberapa saham dapat memiliki performa yang berbeda berdasarkan komposisi persentaset setiap saham individual dibandingkan total kepemilikan saham. Maka dari itu, komposisi portfolio perlu disesuaikan dengan target investasi kita. Beberapa strategi yang biasanya digunakan yaitu:<ul>
            <li><b>Equal Weight (EW):</b> Setiap saham individual memiliki proporsi sama rata</li>
            <li><b>Market Cap Weight (MCap):</b> Setiap saham individual memiliki proporsi sebanding dengan nilai market keseluruhan mereka</li>
            <li><b>Max Sharpe Ratio (MSR):</b> Komposisi portfolio dioptimalkan dengan tujuan memaksimalkan nilai sharpe ratio</li>
            <li><b>Global Min Volatility (GMV):</b> Komposisi portfolio dioptimalkan dengan tujuan meminimalkan nilai volatilitas annual</li>
            <li><b>Efficient Frontier:</b> Kumpulan alternatif komposisi portfolio yang meminimalkan resiko untuk setiap return yang diinginkan</li>
            </ul></p>''', unsafe_allow_html = True)

        ## Calculation for Second Page
        if 'Portfolio' in recent_data.columns:
            recent_data = recent_data.drop(columns=['Portfolio'])
        with sh2:
            with st.spinner('Tunggu Proses Kalkulasi Ya!'):
                compiled_port = markowitz_portfolio(recent_data, max_exp = exp_value, rf = risk_free)
                ef_plot = visualize_ef(compiled_port)
        
        ## Displaying DataFrame
        with L1A:
            st.subheader('**Penjelasan Ukuran yang Digunakan**')
            st.markdown('''<p style="text-align:justify;">
            Dalam melakukan optimalisasi komposisi portfolio, tentunya perlu memiliki ukuran yang digunakan untuk menentukan apakah portfolio terebut bagus atau tidak. Berikut merupakan ukuran yang digunakan:<ul>
            <li><b>Return Annual:</b> Estimasi nilai rata-rata return dalam satu tahun</li>
            <li><b>Volatilitas Annual:</b> Estimasi nilai rata-rata volatilitas dalam satu tahun</li>
            <li><b>Sharpe Ratio:</b> Rasio perbandingan nilai risk adjusted return dengan volatilitas. Suatu portfolio dinyatakan baik jika nilai Sharpe Ratio lebih dari 1</li>
            </ul></p>''', unsafe_allow_html = True)
            st.subheader('**Strategi Portfolio Umum**')
            st.dataframe(compiled_port[1])
            if st.button('Download Data Strategi Portfolio', key = 'second_df'):
                tmp_download_link = download_link(compiled_port[1], 'portfolio_strategy.csv', 'DOWNLOAD!')
                st.markdown(tmp_download_link, unsafe_allow_html=True)
            st.subheader('**Portfolio Efficient Frontier**')
            st.dataframe(compiled_port[2])
            if st.button('Download Data Efficient Portfolio', key = 'third_df'):
                tmp_download_link = download_link(compiled_port[2], 'portfolio_strategy.csv', 'DOWNLOAD!')
                st.markdown(tmp_download_link, unsafe_allow_html=True)
        
        ## Place the Charts
        L2.subheader('**Visualisasi Performa Portfolio**')
        L2.markdown('''<p style="text-align:left;">
        Pada chart dibawah ini, anda dapat melihat <b>perbandingan return dari volatilitas</b> setiap strategi dan asset individual<br>
        Anda dapat memilih strategi dengan <b>return yang anda inginkan</b> namun tetap dengan <b>resiko yang bisa anda tolerir</b></p>
        ''', unsafe_allow_html = True)
        L2.plotly_chart(ef_plot, use_container_width = True)
        
        ## Strategy Comparation
        st.header('**Bandingkan Histori Performa Strategi Portfolio Anda**')
        st.markdown('''
        Gunakan komposisi portfolio anda sendiri untuk membuat strategi custom<br>
        Melalui plot dibawah, anda dapat membandingkan performa beberapa strategi sekaligus seiring waktu<br>
        Silahkan gunakan fitur interaktif seperti memilih strategi yang dimunculkan dengan klik legenda plot di sebelah kanan plot<br>
        Anda juga dapat mengamati rentang waktu yang anda inginkan melalui slider di bawah plot<br>
        atau rentang waktu tertentu pada tombol di kiri atas
        ''', unsafe_allow_html = True)
        
        ## Ask for Custom Weights
        st.subheader('**Tentukan Komposisi Portfolio Anda (%)**')
        max_ef = compiled_port[2].mul(100).iloc[-1,3:].tolist()
        inp_weight = st.beta_columns(num_stocks)
        custom_weight = np.zeros(num_stocks)
        for i in range(0,num_stocks):
            custom_weight[i] = inp_weight[i].number_input(myPicks[i], min_value = 0.0, max_value = 100.0, value = max_ef[i], step = 0.1)
                        
        if sum(custom_weight) != 100:
            warn = 'Pastikan Total Komposisi 100%! Komposisi Saat Ini : {}%'.format(sum(custom_weight))
            st.text(warn)
            return None

        
        ## Calculation for Comparation
        with sh2:
            with st.spinner('Tunggu Proses Kalkulasi Ya!'):
                custom_weight = [x/100 for x in custom_weight]
                str_df, str_fig = cumulative_performance(recent_data, compiled_port[1], custom_weight)
                
        ## Place the Charts
        L3A, L3B = st.beta_columns([2,1])
        L3A.plotly_chart(str_fig, use_container_width = True)
        with L3B:
            st.subheader('**Data Performa Strategi Portfolio**')
            
            ## Visualize DataFrame
            str_df.index = pd.to_datetime(str_df.index, format = '%m/%d/%Y').strftime('%Y-%m-%d')
            L3B.dataframe(str_df.style.applymap(negative_red))
            str_df.index = pd.DatetimeIndex(str_df.index)  
            
            ## Create Download Link
            if st.button('Download Data Return Kumulatif', key = 'fourth_df'):
                tmp_download_link = download_link(str_df, 'portfolio_cumulative_returns.csv', 'DOWNLOAD!')
                st.markdown(tmp_download_link, unsafe_allow_html=True)
        
        
if __name__ == '__main__':
    main()