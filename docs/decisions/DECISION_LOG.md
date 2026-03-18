# Decision Log

이 문서는 고정된 판단의 이유만 기록한다.  
현재 운영 기준 자체는 `PROJECT_SPEC`, `API_CONTRACT`, `SYSTEM_DESIGN`, `TEAM_CONVENTIONS`를 원본으로 본다.

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
  - 같은 key에 새 값을 TTL 없이 저장하면 expiration metadata를 초기화한다
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

### D-007 캐싱 데이터는 외부 API가 아니라 DB 적재 더미 데이터를 사용한다
- 내용:
  - 캐싱 시나리오의 origin 데이터는 외부 API에서 가져오지 않는다
  - 데모와 테스트에 사용할 dummy document는 DB에 사전 적재한다
- 이유:
  - 외부 네트워크 의존 없이 캐시 흐름을 재현 가능하게 유지할 수 있다
  - 데모와 테스트를 안정적으로 반복할 수 있다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`

### D-008 캐싱 시나리오의 origin DB는 MongoDB로 고정한다
- 내용:
  - 더미 데이터는 MongoDB `dummy_items` collection에 저장한다
  - 서비스 계층은 MongoDB 조회 결과를 읽어 캐시 payload로 변환한다
- 이유:
  - 문서형 데이터 구조에 맞고 seed fixture 관리가 단순하다
  - cache-aside 데모에서 origin 저장소 역할을 분리하기 쉽다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`
  - `docs/architecture/SYSTEM_DESIGN.md`

### D-009 HTTP 서버 엔진은 FastAPI로 고정한다
- 내용:
  - 공개 API는 FastAPI 라우트로 제공한다
  - 기본 실행 포트는 Uvicorn 기본값 `8000`을 따른다
- 이유:
  - JSON API, validation, 테스트 경로를 단순하게 유지할 수 있다
  - 문서 계약과 구현 책임 경계를 빠르게 맞추기 쉽다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/architecture/SYSTEM_DESIGN.md`

### D-010 v1 동시성 보장은 key 단위 직렬화로 제한한다
- 내용:
  - 같은 `key`에 대한 요청은 서비스 계층에서 순차 처리한다
  - 다른 `key`에 대한 요청은 병렬 처리를 허용한다
  - same-key 요청의 일관성만 보장하고, origin 조회 최적화는 v1 계약에 포함하지 않는다
- 상태:
  - superseded by `D-013`
- 이유:
  - same-key 경쟁 상태를 단순한 기준으로 통제할 수 있다
  - 전역 락 없이도 핵심 일관성 요구를 충족할 수 있다
  - 중복 origin 조회 최적화까지 묶으면 구현과 문서 복잡도가 불필요하게 커진다
- 원본 문서:
  - `docs/architecture/SYSTEM_DESIGN.md`
  - `docs/process/TEST_STRATEGY.md`

### D-011 v1 무효화 전략은 명시적 삭제와 TTL 기반 만료로 제한한다
- 내용:
  - 사용자 무효화 수단은 `DELETE`, `EXPIRE`, TTL 만료, 같은 key overwrite로 한정한다
  - 별도 `deprecated` 상태나 soft delete는 도입하지 않는다
- 이유:
  - v1 요구사항을 충족하는 최소 수단만 남겨 설명과 구현 복잡도를 낮춘다
  - 공개 API 계약과 테스트 기준을 단순하게 유지할 수 있다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`
  - `docs/spec/API_CONTRACT.md`

### D-012 optional persistence는 후보 검토만 하고 v1 구현 범위에서는 제외한다
- 내용:
  - 후보는 `append-only log`, `snapshot`, `hybrid`다
  - v1에서는 persistence를 필수 구현에 넣지 않고 검토 결과만 남긴다
- 이유:
  - 과제 범위에서는 핵심 기능, 테스트, README 데모 완성도가 우선이다
  - 서버 다운 대응은 중요하지만 optional 항목으로 남겨도 과제 목표를 해치지 않는다
- 원본 문서:
  - `docs/spec/PROJECT_SPEC.md`

### D-013 v1 명령 실행은 전역 싱글 실행 스레드로 직렬화한다
- 내용:
  - 모든 명령은 하나의 shared command executor thread에서 순차 실행한다
  - 같은 `key`, 다른 `key`, 다른 서비스 조합 모두 동시에 실행하지 않는다
  - 요청 수신과 응답 대기는 동시일 수 있지만 실제 서비스 로직 실행은 전역 직렬화한다
- 이유:
  - Redis식 명령 실행 모델에 더 가깝게 맞출 수 있다
  - 발표 시 동시성 기준과 실행 순서를 더 단순하게 설명할 수 있다
  - KV, cache, origin fetch를 포함한 전체 명령 경로의 일관성을 동일한 기준으로 보장할 수 있다
- 원본 문서:
  - `docs/architecture/SYSTEM_DESIGN.md`
  - `docs/process/TEST_STRATEGY.md`

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
