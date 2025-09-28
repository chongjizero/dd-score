import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 데이터 저장 파일 경로
DATA_FILE = '/app/data/nasdaq100_data.csv'
MIN_DD_FILE = '/app/data/min_dd_per_section.csv'

def update_data():
    """신규 데이터 수집"""
    try:
        data = pd.read_csv(DATA_FILE, index_col='Date', parse_dates=True)
        last_date = data.index.max()
        new_data = yf.download('^NDX', start=last_date + datetime.timedelta(days=1),multi_level_index=False)
        if last_date != new_data.index.max():
            # 기존 데이터와 병합
            updated_data = pd.concat([data, new_data])
            print("Data updated.")
            return updated_data, new_data
        else:
            print("No new data available.")
            return pd.DataFrame(), pd.DataFrame()
    except FileNotFoundError:
        print("Data file not found. Run initial script first.")
        return pd.DataFrame(), pd.DataFrame()

def calculate_drawdown_for_new(new_data, prev_peak):
    """신규 데이터의 DD 계산"""
    if new_data.empty:
        return new_data
    close = new_data['Close']
    peak = np.maximum(prev_peak, close.cummax())  # 이전 전고점 고려
    drawdown = (close - peak) / peak * 100
    new_data['Drawdown'] = drawdown
    return new_data, peak.max()  # 업데이트된 전고점 반환

def identify_sections_for_new(new_data, prev_section, prev_peak):
    """신규 데이터의 구간 구분 계산 및 전고점 갱신 여부 판단"""
    if new_data.empty:
        return new_data
    close = new_data['Close']
    current_peak = prev_peak
    new_peak_flags = []
    for c in close:
        if c > current_peak:
            new_peak_flags.append(True)
            current_peak = c
        else:
            new_peak_flags.append(False)
    new_data['New_Peak'] = new_peak_flags
    new_data['Section'] = prev_section + new_data['New_Peak'].cumsum()
    return new_data

def update_min_drawdown_per_section(updated_data, min_dd_per_section, new_data):
    """마지막 구간의 Min DD 재 계산 (신규 데이터로 인해 변경될 수 있음)"""
    if new_data.empty:
        return min_dd_per_section
    # 전체 데이터로 재계산 (안전하게)
    new_min_dd_per_section = updated_data.groupby('Section')['Drawdown'].min()
    new_min_dd_per_section.to_csv(MIN_DD_FILE)
    print("Min DD per section updated.")
    return new_min_dd_per_section

def calculate_percentile(min_dd_per_section, current_min_dd):
    """현재 구간의 Min DD와 퍼센타일 계산"""
    # 과거 구간들: 현재 구간 제외    
    if len(min_dd_per_section) == 0:
        return 100  # 과거 구간 없으면 0
    percentile = np.sum(min_dd_per_section <= current_min_dd) / len(min_dd_per_section) * 100
    return percentile

def send_email(stats):
    """통계 정보를 메일로 전송"""
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    receiver_emails_str = os.getenv('RECEIVER_EMAIL')

    if not all([sender_email, sender_password, receiver_emails_str]):
        print("Email configuration missing in environment variables.")
        return

    # 콤마로 구분된 이메일 주소들을 리스트로 변환
    receiver_emails = [email.strip() for email in receiver_emails_str.split(',')]

    subject = "나스닥 100 드로우다운 일일 리포트"

    # 한글로 이메일 내용 작성
    daily_change_str = f"{stats['daily_change']:.2f}%" if isinstance(stats['daily_change'], (int, float)) else str(stats['daily_change'])
    current_drawdown_str = f"{stats['current_drawdown']:.2f}%" if isinstance(stats['current_drawdown'], (int, float)) else str(stats['current_drawdown'])
    last_min_dd_str = f"{stats['last_min_dd']:.2f}%" if isinstance(stats['last_min_dd'], (int, float)) else str(stats['last_min_dd'])
    last_percentile_str = f"{stats['last_percentile']:.2f}%" if isinstance(stats['last_percentile'], (int, float)) else str(stats['last_percentile'])
    percentile_10_str = f"{stats['percentile_10']:.2f}%" if isinstance(stats['percentile_10'], (int, float)) else str(stats['percentile_10'])
    percentile_1_str = f"{stats['percentile_1']:.2f}%" if isinstance(stats['percentile_1'], (int, float)) else str(stats['percentile_1'])

    body = f"""
나스닥 100 지수 드로우다운 분석 결과를 알려드립니다.

📊 일일 현황
• 일간 등락률: {daily_change_str}
• 현재 드로우다운: {current_drawdown_str}

📈 구간별 분석
• 현재 구간 최소 드로우다운: {last_min_dd_str}
• 현재 구간 백분위수: {last_percentile_str}

📉 과거 비교 기준
• 10% 백분위수: {percentile_10_str}
• 1% 백분위수: {percentile_1_str}

※ 현재 구간 Drawdown 값이 10% 백분위수 보다 낮으면 나스닥 100 손절
   현재 구간 Drawdown 값이 1% 백분위수 보다 낮거나
   현재 구간 Drawdown 값이 10% 백분위수 보다 낮으면서 당일 Drawdown이 10% 백분위수 보다 높으면 재진입 

자동 생성된 리포트입니다.
    """.strip()

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail 예시, 다른 서버로 변경 가능
        server.starttls()
        server.login(sender_email, sender_password)

        # 각 수신자에게 개별적으로 이메일 전송
        for receiver_email in receiver_emails:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            print(f"Email sent successfully to {receiver_email}")

        server.quit()
        print(f"All emails sent successfully to {len(receiver_emails)} recipients.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# 메인 실행 로직
if __name__ == "__main__":
    # 신규 데이터 수집
    updated_data, new_data = update_data()
    if new_data.empty:
        exit()
    
    # 이전 정보 로드
    prev_data = updated_data.drop(new_data.index) if not new_data.empty else updated_data
    prev_peak = prev_data['Close'].max() if not prev_data.empty else 0
    prev_section = prev_data['Section'].max() if 'Section' in prev_data.columns and not prev_data.empty else 0
    min_dd_per_section = pd.read_csv(MIN_DD_FILE, index_col='Section')['Drawdown'] if pd.io.common.file_exists(MIN_DD_FILE) else pd.Series()
    
    # 신규 데이터의 DD 계산 및 전고점 업데이트
    new_data, updated_peak = calculate_drawdown_for_new(new_data, prev_peak)
    
    # 신규 데이터의 구간 구분
    new_data = identify_sections_for_new(new_data, prev_section, prev_peak)
    
    # 전체 업데이트 데이터
    if not new_data.empty:
        updated_data = pd.concat([prev_data, new_data])
    
    # min DD 재 계산
    min_dd_per_section = update_min_drawdown_per_section(updated_data, min_dd_per_section, new_data)
    
    # 일간 등락률 계산
    daily_change = 'N/A'
    if len(updated_data) >= 2:
        latest_close = updated_data['Close'].iloc[-1]
        previous_close = updated_data['Close'].iloc[-2]
        daily_change = ((latest_close - previous_close) / previous_close) * 100

    # 현재 드로우다운
    current_drawdown = updated_data['Drawdown'].iloc[-1] if not updated_data.empty else 'N/A'

    # 현재 구간의 min DD
    current_section = updated_data['Section'].max()
    current_min_dd = min_dd_per_section[current_section]

    # 퍼센타일 계산
    filtered_min_dd = min_dd_per_section[min_dd_per_section != 0]
    percentile = calculate_percentile(filtered_min_dd, current_min_dd)
    print(f"Current percentile: {percentile:.2f}%")

    # 1%, 10% 퍼센타일 계산
    percentile_1 = np.percentile(filtered_min_dd, 1) if not filtered_min_dd.empty else 'N/A'
    percentile_10 = np.percentile(filtered_min_dd, 10) if not filtered_min_dd.empty else 'N/A'

    # 모든 통계 정보를 포함하여 이메일 전송
    email_stats = {
        'daily_change': daily_change,
        'current_drawdown': current_drawdown,
        'last_min_dd': current_min_dd,
        'last_percentile': percentile,
        'percentile_10': percentile_10,
        'percentile_1': percentile_1
    }
    send_email(email_stats)
    
    # 업데이트된 데이터 저장
    updated_data.to_csv(DATA_FILE)
    print("Update script completed.")