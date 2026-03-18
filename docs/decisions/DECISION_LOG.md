# Decision Log

이 문서는 고정된 판단의 이유만 기록한다. 현재 운영 기준 자체는 `PROJECT_SPEC`, `API_CONTRACT`, `SYSTEM_DESIGN`, `TEAM_CONVENTIONS`를 원본으로 본다.

## Accepted
### D-001 기본 아키텍처는 3계층으로 분리한다
- 내용:
  - `api -> service -> store` 구조를 기본으로 한다
- 이유:
  - 책임 경계를 분리해야 팀 병합 비용을 낮출 수 있다
- 원본 문서:
  - `docs/architecture/SYSTEM_DESIGN.md`

### D-002 기본 만료 정책은 lazy expiration이다
- 내용:
  - 조회 또는 접근 시 만료 여부를 검사한다
  - 만료되었으면 즉시 제거하고 miss로 처리한다
- 이유:
  - 구현 복잡도를 낮추면서 요구사항을 충족할 수 있다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/architecture/SYSTEM_DESIGN.md`

### D-003 v1 공개 인터페이스는 HTTP JSON API다
- 내용:
  - 라이브러리 API나 CLI가 아니라 HTTP JSON API를 외부 데모 표면으로 사용한다
- 이유:
  - 외부 사용성과 데모 재현성이 높다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`

### D-004 TTL 단위는 초이며 0은 invalid다
- 내용:
  - 음수와 `0`은 모두 `INVALID_TTL`로 처리한다
- 이유:
  - 즉시 만료와 validation 오류가 섞이는 것을 막는다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`

### D-005 SET 덮어쓰기에서 TTL이 없으면 기존 만료는 제거한다
- 내용:
  - 같은 키에 새 값을 TTL 없이 저장하면 expiration metadata를 초기화한다
- 이유:
  - 구현 판단이 갈릴 수 있는 지점을 미리 잠가 일관성을 유지한다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`

### D-006 v1은 단일 프로세스만 지원한다
- 내용:
  - 멀티 프로세스, 분산 노드, 복제는 다루지 않는다
- 이유:
  - 과제 범위를 넘지 않으면서 동시성 문제를 최소 수준으로 통제할 수 있다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/architecture/SYSTEM_DESIGN.md`

### D-007 뉴스 캐싱 데모는 DB 적재 dummy headline 기반 cache-aside로 고정한다
- 내용:
  - `GET /demo/headlines-cache?topic={ai|gaming|economy}` 형태를 사용한다
  - origin 데이터는 외부 API가 아니라 DB에 사전 적재한 dummy headline document를 조회한다
  - 내부 캐시 키는 `news:{topic}:kr`, TTL은 `15`초로 고정한다
- 이유:
  - 외부 네트워크 의존 없이 캐시 hit / TTL 만료 / origin 재조회 흐름을 짧고 명확하게 보여주기 쉽다
  - 데모와 테스트를 재현 가능하게 유지할 수 있다
- 원본 문서:
  - `docs/spec/API_CONTRACT.md`
  - `docs/spec/PROJECT_SPEC.md`

### D-008 뉴스 캐싱 데모용 origin DB는 MongoDB로 고정한다
- 내용:
  - headline dummy data는 MongoDB collection에 저장한다
  - 조회 기준은 `topic`, `locale`이며 문서형 데이터를 그대로 다룬다
- 이유:
  - 기사 목록 형태 데이터를 다루기 쉽고 seed fixture 관리가 단순하다
  - cache-aside 데모에서 origin read model을 명확하게 분리할 수 있다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`
  - `docs/architecture/SYSTEM_DESIGN.md`

### D-009 HTTP 서버 엔진은 FastAPI로 고정한다
- 내용:
  - 공개 API는 FastAPI 라우트로 제공한다
  - 기본 실행 포트는 Uvicorn 기본값 `8000`을 따른다
- 이유:
  - Python 3.11 기준 JSON API, validation, 테스트 경로를 단순하게 유지할 수 있다
  - 문서 계약과 구현 책임 경계를 빠르게 맞추기 쉽다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/architecture/SYSTEM_DESIGN.md`

## Deferred
### D-101 영속성 방식
- 후보:
  - append-only log
  - snapshot
  - hybrid
- 다시 결정할 시점:
  - 핵심 기능과 테스트가 안정화된 뒤

### D-102 주기적 cleanup worker
- 후보:
  - 없음
  - fixed interval sweep
- 다시 결정할 시점:
  - lazy expiration 구현 후 메모리 정리 필요성이 명확해졌을 때

### D-103 추가 명령 지원
- 후보:
  - `TTL`
  - `INCR`
  - `MGET`
- 다시 결정할 시점:
  - v1 범위가 모두 완료된 뒤
