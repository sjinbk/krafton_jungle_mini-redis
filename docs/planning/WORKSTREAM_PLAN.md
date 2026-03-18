# Workstream Plan

이 문서는 팀 바이브코딩을 위한 구현 순서, workstream, 브랜치 단위 산출물을 고정한다.

## 권장 순서
1. `WS-01` 계약 고정
2. `WS-02` 저장소 핵심 구현
3. `WS-03` TTL 구현
4. `WS-04` HTTP API 구현
5. `WS-05` 테스트와 벤치마크
6. `WS-06` README 반영

## Workstreams
### `WS-01` 계약 고정
- 권장 브랜치 주제:
  - `docs/repo-contract-lock-<initials>`
- 입력 문서:
  - `README.md`
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`
  - `docs/decisions/DECISION_LOG.md`
- 산출물:
  - FastAPI / MongoDB / dummy data 전제가 반영된 잠긴 API 계약
  - 필요한 결정 로그 업데이트
- 완료 기준:
  - 공개 계약 관련 미해결 결정이 남아 있지 않다

### `WS-02` 저장소 핵심 구현
- 권장 브랜치 주제:
  - `feature/store-core-map-<initials>`
- 입력 문서:
  - `docs/architecture/SYSTEM_DESIGN.md`
  - `docs/spec/PROJECT_SPEC.md`
- 산출물:
  - key/value 저장 구조
  - set/get/delete primitive
- 완료 기준:
  - 단위 테스트 가능한 store 계층이 준비된다

### `WS-03` TTL 구현
- 권장 브랜치 주제:
  - `feature/ttl-expire-flow-<initials>`
- 입력 문서:
  - `docs/architecture/SYSTEM_DESIGN.md`
  - `docs/decisions/DECISION_LOG.md`
  - `docs/process/TEST_STRATEGY.md`
- 산출물:
  - expiresAt 처리
  - lazy expiration
  - 만료 관련 테스트
- 완료 기준:
  - 만료 정책이 문서와 같은 방식으로 동작한다

### `WS-04` HTTP API 구현
- 권장 브랜치 주제:
  - `feature/api-fastapi-cache-demo-<initials>`
- 입력 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`
  - `docs/architecture/SYSTEM_DESIGN.md`
  - `docs/decisions/DECISION_LOG.md`
- 산출물:
  - FastAPI HTTP 엔드포인트
  - 요청/응답 형식
  - MongoDB origin 조회 협력 로직
  - 뉴스 헤드라인 캐싱 데모 엔드포인트
- 완료 기준:
  - 기능 테스트를 붙일 수 있는 공개 API가 준비된다

### `WS-05` 테스트와 벤치마크
- 권장 브랜치 주제:
  - `feature/test-benchmark-<initials>`
- 입력 문서:
  - `docs/process/TEST_STRATEGY.md`
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`
- 산출물:
  - 단위 테스트
  - 기능 테스트
  - MongoDB dummy seed 기반 테스트 fixture
  - 성능 비교 스크립트
- 완료 기준:
  - 수용 기준에 대응되는 테스트가 존재한다

### `WS-06` README 반영
- 권장 브랜치 주제:
  - `docs/repo-readme-demo-<initials>`
- 입력 문서:
  - `README.md`
  - 테스트 결과
  - 성능 비교 결과
- 산출물:
  - 실행 방법
  - API 예시
  - MongoDB 더미 데이터 데모 설명
  - 테스트 결과
  - 성능 비교 결과
- 완료 기준:
  - README만으로 프로젝트 소개와 데모 흐름 설명이 가능하다

## 공통 규칙
- 한 브랜치에서 한 workstream만 크게 수정한다
- 공통 계약 변경은 코드보다 문서를 먼저 수정한다
- 고충돌 파일 변경은 별도 브랜치에서 짧게 끝낸다
- 머지 전에는 관련 테스트 또는 최소 검증 근거를 남긴다
