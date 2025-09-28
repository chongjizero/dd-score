# initial_script.py: 최초 수행 스크립트
# - 최초 과거 데이터 수집
# - Drawdown 계산
# - 구간 구분
# - 구간별 min DD 계산 (저장까지)

import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# 데이터 저장 파일 경로
DATA_FILE = '/app/data/nasdaq100_data.csv'
MIN_DD_FILE = '/app/data/min_dd_per_section.csv'  # 구간별 min DD 저장 파일

def fetch_initial_data():
    """최초 나스닥100의 과거 지수 시계열 전체를 받아서 저장"""
    # Nasdaq-100 지수 티커: ^NDX
    data = yf.download('^NDX', start='1900-01-01', multi_level_index=False)  # 가능한 가장 이른 날짜부터
    data.to_csv(DATA_FILE)
    print("Initial data fetched and saved.")
    return data

def calculate_drawdown(data):
    """Draw Down 계산 (종가 사용)"""
    close = data['Close']
    peak = close.cummax()  # 누적 최대값 (전고점)
    drawdown = (close - peak) / peak * 100  # 퍼센트로 계산
    data['Drawdown'] = drawdown
    return data

def identify_sections(data):
    """전고점이 갱신 되는 시점을 기준으로 구간 구분"""
    close = data['Close']
    peak = close.cummax()
    # 전고점이 갱신되는 시점: peak.shift(1) < peak
    data['New_Peak'] = (peak.shift(1) < peak)
    # 구간 번호 할당: 누적 합으로 구간 구분
    data['Section'] = data['New_Peak'].cumsum()
    return data

def calculate_min_drawdown_per_section(data):
    """구간의 Minimum Draw Down 계산"""
    min_dd_per_section = data.groupby('Section')['Drawdown'].min()
    min_dd_per_section.to_csv(MIN_DD_FILE)
    print("Min DD per section calculated and saved.")
    return min_dd_per_section

# 메인 실행 로직
if __name__ == "__main__":
    # 최초 데이터 수집
    data = fetch_initial_data()
    
    # Drawdown 계산
    data = calculate_drawdown(data)
    
    # 구간 구분
    data = identify_sections(data)
    
    # 구간별 min DD 계산 및 저장
    min_dd_per_section = calculate_min_drawdown_per_section(data)
    
    # 업데이트된 데이터 저장
    data.to_csv(DATA_FILE)
    print("Initial script completed.")