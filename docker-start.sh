#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Docker 컨테이너 시작 스크립트 ===${NC}"

# 이미지 확인
IMAGE_NAME="dd-score"
CONTAINER_NAME="dd-score"

if [ -z "$(docker images -q $IMAGE_NAME)" ]; then
    echo -e "${RED}오류: '$IMAGE_NAME' 이미지가 없습니다!${NC}"
    echo -e "${YELLOW}먼저 './docker-build.sh' 스크립트를 실행해주세요.${NC}"
    exit 1
fi

# 실행 중인 컨테이너 확인
if [ ! -z "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo -e "${YELLOW}컨테이너 '$CONTAINER_NAME'가 이미 실행 중입니다.${NC}"
    echo -e "${BLUE}컨테이너 상태:${NC}"
    docker ps -f name=$CONTAINER_NAME
    exit 0
fi

# 중지된 컨테이너 제거
STOPPED_CONTAINER=$(docker ps -a -q -f name=$CONTAINER_NAME)
if [ ! -z "$STOPPED_CONTAINER" ]; then
    echo -e "${YELLOW}기존 컨테이너 '$CONTAINER_NAME' 제거 중...${NC}"
    docker rm $CONTAINER_NAME
fi

# .env 파일 확인 및 로드
if [ ! -f ".env" ]; then
    echo -e "${RED}오류: .env 파일이 없습니다!${NC}"
    exit 1
fi

echo -e "${BLUE}환경변수 파일(.env) 로드 중...${NC}"
set -a
source .env
set +a

# Docker 볼륨 확인 및 생성
VOLUME_NAME="dd-score-data"
echo -e "${BLUE}Docker 볼륨 확인 중...${NC}"
if [ -z "$(docker volume ls -q -f name=$VOLUME_NAME)" ]; then
    echo -e "${GREEN}Docker 볼륨 '$VOLUME_NAME' 생성 중...${NC}"
    docker volume create $VOLUME_NAME
    echo -e "${GREEN}Docker 볼륨이 생성되었습니다.${NC}"
else
    echo -e "${GREEN}기존 Docker 볼륨 '$VOLUME_NAME' 사용 (데이터 보존됨)${NC}"
fi

# 컨테이너 시작
echo -e "${GREEN}컨테이너 '$CONTAINER_NAME' 시작 중...${NC}"
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p 5000:5000 \
    -v $VOLUME_NAME:/app/data \
    -e SENDER_EMAIL="$SENDER_EMAIL" \
    -e SENDER_PASSWORD="$SENDER_PASSWORD" \
    -e RECEIVER_EMAIL="$RECEIVER_EMAIL" \
    -e TZ=Asia/Seoul \
    $IMAGE_NAME

# 시작 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}=== 컨테이너 시작 완료! ===${NC}"
    echo ""
    echo -e "${BLUE}컨테이너 정보:${NC}"
    docker ps -f name=$CONTAINER_NAME
    echo ""
    echo -e "${GREEN}서비스 정보:${NC}"
    echo -e "  대시보드 URL: ${BLUE}http://localhost:5000${NC}"
    echo -e "  데이터 볼륨: ${BLUE}$VOLUME_NAME${NC} (Docker 볼륨에 데이터 보존됨)"
    echo -e "  자동 업데이트: ${BLUE}매일 오전 9시${NC}"
    echo ""
    echo -e "${YELLOW}컨테이너 로그 확인: ${NC}docker logs -f $CONTAINER_NAME"
    echo -e "${YELLOW}컨테이너 중지: ${NC}./docker-stop.sh"
else
    echo -e "${RED}=== 컨테이너 시작 실패! ===${NC}"
    exit 1
fi

# 초기 데이터 설정 안내
echo ""
echo -e "${YELLOW}=== 초기 설정 안내 ===${NC}"
echo -e "${BLUE}최초 실행 시 다음 작업을 수행해주세요:${NC}"
echo -e "1. 컨테이너 내부에서 초기 데이터 스크립트 실행:"
echo -e "   ${GREEN}docker exec -it $CONTAINER_NAME python /app/initial_script.py${NC}"
echo -e "2. 웹 대시보드 접속: ${BLUE}http://localhost:5000${NC}"
echo ""
echo -e "${GREEN}스크립트 실행 완료!${NC}"