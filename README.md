# NASDAQ-100 드로우다운 분석 시스템

NASDAQ-100 지수의 드로우다운을 분석하고 모니터링하는 시스템입니다. 웹 대시보드와 일일 이메일 리포트를 제공합니다.

## 기능

- **실시간 데이터 수집**: NASDAQ-100 지수 데이터 자동 업데이트
- **드로우다운 분석**: 전고점 기준 드로우다운 계산 및 구간별 분석
- **웹 대시보드**: 실시간 차트와 통계 정보 제공
- **이메일 알림**: 매일 오전 9시 자동 리포트 전송
- **다중 수신자**: 여러 이메일 주소로 동시 전송

## 시스템 구성

### 핵심 파일
- `initial_script.py`: 최초 과거 데이터 수집 및 분석
- `update_script.py`: 일일 데이터 업데이트 및 이메일 전송
- `app.py`: Flask 웹 대시보드

### Docker 관리 스크립트
- `docker-stop.sh`: 컨테이너 중지 (Docker 볼륨 삭제 옵션)
- `docker-build.sh`: 이미지 빌드 (환경변수 자동 반영)
- `docker-start.sh`: 컨테이너 시작 (Docker 볼륨 마운트)

## 설치 및 실행

### 1. 환경변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```bash
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECEIVER_EMAIL=receiver1@gmail.com,receiver2@gmail.com
```

### 2. Docker로 실행

```bash
# 이미지 빌드
./docker-build.sh

# 컨테이너 시작
./docker-start.sh

# 최초 실행 시 초기 데이터 수집
docker exec -it dd-score python /app/initial_script.py
```

### 3. 대시보드 접속
http://localhost:5000

## 대시보드 정보

### 통계 정보 (6개 항목)
1. **Daily Change**: 일간 등락률
2. **Current Drawdown**: 현재 드로우다운
3. **Last Section Min-DD**: 현재 구간 최소 드로우다운
4. **Last Section Percentile**: 현재 구간 백분위
5. **10th Percentile**: 10% 백분위수
6. **1st Percentile**: 1% 백분위수

### 차트
- NASDAQ-100 지수 가격 차트
- 드로우다운 차트 (10% 백분위수, 1% 백분위수 기준선 포함)

## 이메일 리포트

매일 오전 9시에 다음 정보가 포함된 한글 리포트가 전송됩니다:

- 📊 일일 현황 (등락률, 현재 드로우다운)
- 📈 구간별 분석 (최소 드로우다운, 백분위)
- 📉 과거 비교 기준 (1%, 10% 백분위수)

## 데이터 보존

- Docker 볼륨(`dd-score-data`)을 사용하여 데이터 영구 보존
- 컨테이너 재시작/삭제 시에도 Docker 볼륨에 데이터 자동 보존
- Docker 볼륨 삭제는 `docker-stop.sh` 실행 시 선택 가능
- 볼륨 데이터 확인: `docker volume inspect dd-score-data`

## 주의사항

- Gmail 사용 시 앱 비밀번호 설정 필요
- 최초 실행 시 `initial_script.py` 반드시 실행
- 환경변수 파일(`.env`)과 데이터 파일(`data/`)은 Git에서 제외됨

## 문제 해결

```bash
# 컨테이너 로그 확인
docker logs -f dd-score

# 컨테이너 내부 접속
docker exec -it dd-score /bin/bash

# 수동 업데이트 실행
docker exec -it dd-score python /app/update_script.py
```