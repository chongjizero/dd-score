#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Docker 컨테이너 중지 스크립트 ===${NC}"

# 실행 중인 컨테이너 확인
CONTAINER_NAME="dd-score"
RUNNING_CONTAINER=$(docker ps -q -f name=$CONTAINER_NAME)

if [ -z "$RUNNING_CONTAINER" ]; then
    echo -e "${YELLOW}실행 중인 '$CONTAINER_NAME' 컨테이너가 없습니다.${NC}"
else
    echo -e "${GREEN}컨테이너 '$CONTAINER_NAME' 중지 중...${NC}"
    docker stop $CONTAINER_NAME
    echo -e "${GREEN}컨테이너가 중지되었습니다.${NC}"
fi

# 컨테이너 제거
STOPPED_CONTAINER=$(docker ps -a -q -f name=$CONTAINER_NAME)
if [ ! -z "$STOPPED_CONTAINER" ]; then
    echo -e "${GREEN}컨테이너 '$CONTAINER_NAME' 제거 중...${NC}"
    docker rm $CONTAINER_NAME
    echo -e "${GREEN}컨테이너가 제거되었습니다.${NC}"
fi

# 로컬 데이터 디렉토리 삭제 여부 확인
echo ""
echo -e "${YELLOW}로컬 데이터 디렉토리(./data)를 삭제하시겠습니까?${NC}"
echo -e "${RED}주의: 삭제하면 저장된 모든 데이터(nasdaq100_data.csv, min_dd_per_section.csv)가 삭제됩니다!${NC}"
echo -e "${YELLOW}y/N (기본값: N): ${NC}"
read -r DELETE_DATA

if [[ $DELETE_DATA =~ ^[Yy]$ ]]; then
    if [ -d "./data" ]; then
        echo -e "${RED}로컬 데이터 디렉토리 './data' 삭제 중...${NC}"
        rm -rf ./data
        echo -e "${RED}데이터 디렉토리가 삭제되었습니다.${NC}"
    else
        echo -e "${YELLOW}삭제할 데이터 디렉토리가 없습니다.${NC}"
    fi
else
    echo -e "${GREEN}데이터 디렉토리를 보존합니다. 데이터가 유지됩니다.${NC}"
fi

# Docker 볼륨 정리 (사용하지 않는 볼륨들)
echo ""
echo -e "${YELLOW}사용하지 않는 Docker 볼륨을 정리하시겠습니까? (y/N): ${NC}"
read -r CLEANUP_VOLUMES

if [[ $CLEANUP_VOLUMES =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}사용하지 않는 볼륨 정리 중...${NC}"
    docker volume prune -f
    echo -e "${GREEN}볼륨 정리 완료!${NC}"
fi

echo -e "${GREEN}Docker 중지 작업이 완료되었습니다.${NC}"