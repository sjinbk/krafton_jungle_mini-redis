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
