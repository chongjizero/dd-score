#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Docker 이미지 빌드 스크립트 ===${NC}"

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo -e "${RED}오류: .env 파일이 없습니다!${NC}"
    echo -e "${YELLOW}.env 파일을 생성하고 다음 변수들을 설정해주세요:${NC}"
    echo "SENDER_EMAIL=your_email@gmail.com"
    echo "SENDER_PASSWORD=your_app_password"
    echo "RECEIVER_EMAIL=receiver1@gmail.com,receiver2@gmail.com"
    exit 1
fi

# .env 파일 로드
echo -e "${BLUE}환경변수 파일(.env) 로드 중...${NC}"
set -a
source .env
set +a

# 필수 환경변수 확인
if [ -z "$SENDER_EMAIL" ] || [ -z "$SENDER_PASSWORD" ] || [ -z "$RECEIVER_EMAIL" ]; then
    echo -e "${RED}오류: 필수 환경변수가 설정되지 않았습니다!${NC}"
    echo -e "${YELLOW}다음 변수들을 .env 파일에 설정해주세요:${NC}"
    echo "SENDER_EMAIL"
    echo "SENDER_PASSWORD"
    echo "RECEIVER_EMAIL"
    exit 1
fi

echo -e "${GREEN}환경변수 확인 완료:${NC}"
echo -e "  SENDER_EMAIL: ${SENDER_EMAIL}"
echo -e "  RECEIVER_EMAIL: ${RECEIVER_EMAIL}"
echo -e "  SENDER_PASSWORD: [HIDDEN]"

# 기존 이미지 확인 및 삭제
IMAGE_NAME="dd-score"
EXISTING_IMAGE=$(docker images -q $IMAGE_NAME)

if [ ! -z "$EXISTING_IMAGE" ]; then
    echo -e "${YELLOW}기존 이미지 '$IMAGE_NAME' 삭제 중...${NC}"
    docker rmi $IMAGE_NAME
fi

# Docker 이미지 빌드
echo -e "${GREEN}Docker 이미지 빌드 시작...${NC}"
docker build \
    --build-arg SENDER_EMAIL="$SENDER_EMAIL" \
    --build-arg SENDER_PASSWORD="$SENDER_PASSWORD" \
    --build-arg RECEIVER_EMAIL="$RECEIVER_EMAIL" \
    -t $IMAGE_NAME .

# 빌드 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}=== Docker 이미지 빌드 완료! ===${NC}"
    echo -e "${BLUE}빌드된 이미지:${NC}"
    docker images $IMAGE_NAME
else
    echo -e "${RED}=== Docker 이미지 빌드 실패! ===${NC}"
    exit 1
fi

# 사용하지 않는 이미지 정리 (선택사항)
echo ""
echo -e "${YELLOW}사용하지 않는 Docker 이미지를 정리하시겠습니까? (y/N): ${NC}"
read -r CLEANUP

if [[ $CLEANUP =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}사용하지 않는 이미지 정리 중...${NC}"
    docker image prune -f
    echo -e "${GREEN}정리 완료!${NC}"
fi

echo -e "${GREEN}빌드 스크립트 실행 완료!${NC}"