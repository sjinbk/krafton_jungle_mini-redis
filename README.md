# krafton_jungle_mini-redis

`Mini Redis` 팀 프로젝트 저장소입니다. 이 문서는 프로젝트를 소개하고, 구현 결과와 데모 내용을 정리하는 소개 문서입니다.

## 한 줄 소개
해시 테이블 기반 인메모리 키-값 저장소를 구현하고, TTL, DB 더미 데이터 캐싱, 테스트, 성능 비교까지 포함해 설명 가능한 `Mini Redis`를 만든다.

## 문서 구조
- [Project Spec](docs/spec/PROJECT_SPEC.md)
- [API Contract](docs/spec/API_CONTRACT.md)
- [System Design](docs/architecture/SYSTEM_DESIGN.md)
- [Test Strategy](docs/process/TEST_STRATEGY.md)

## 우선 구현 항목
- KV 저장, 조회, 삭제가 되는 기본 API
- TTL 설정과 TTL 조회
- lazy expiration 동작
- 단위 테스트와 기능 테스트
- 캐시 hit / no-cache 성능 비교

## 프로젝트 목표
- 하루 안에 팀 단위 `Mini Redis`를 구현한다.
- AI를 적극 활용하되, 핵심 로직은 팀원이 직접 설명할 수 있어야 한다.
- 결과물뿐 아니라 테스트와 검증 과정을 함께 보여준다.

## 기술 선택 근거
- 과제 기준상 프레임워크 선택은 자유다.
- 이 저장소는 빠른 HTTP API 구현, validation, 테스트 재현성을 위해 `FastAPI`를 선택했다.
- 캐싱 데모의 origin은 외부 API 대신 `MongoDB seeded dummy data`로 고정해 데모와 테스트를 반복 가능하게 맞췄다.

## 구현 범위
- `SET`, `GET`, `DELETE`, `EXPIRE/TTL`
- lazy expiration 기반 TTL 처리
- HTTP JSON 기반 공개 API
- 단위 테스트와 기능 테스트
- DB 더미 데이터 캐싱 시나리오
- 캐시 hit / no-cache 성능 비교

## 구현 전에 꼭 채워야 할 값
아래 값은 구현 전 [Project Spec](docs/spec/PROJECT_SPEC.md)에서 먼저 확정한다.

| 항목 | 현재 상태 |
|------|-----------|
| runtime | python 3.11 |
| framework | FastAPI |
| package manager | pip |
| app port | FastAPI default value |
| default TTL | 15초 |

## 설계 요약
- 저장소는 해시 테이블 기반 인메모리 구조로 설계한다.
- 서비스 계층이 명령 규칙과 TTL 정책을 책임진다.
- API 계층은 외부 요청과 응답 형식을 담당한다.
- 만료 정책은 `lazy expiration`을 기본값으로 사용한다.

세부 설계 기준은 [System Design](docs/architecture/SYSTEM_DESIGN.md) 문서를 따른다.

## 핵심 동작
### `SET`
- 키를 저장하거나 기존 값을 덮어쓴다.
- 필요하면 TTL을 함께 설정한다.
- TTL 없이 덮어쓰면 기존 만료 정보는 제거한다.

### `GET`
- 키가 살아 있으면 값을 반환한다.
- 만료되었으면 조회 시점에 제거하고 miss로 처리한다.

### `DELETE`
- 키를 삭제하고 삭제 여부를 반환한다.

### `EXPIRE` / `TTL`
- 키의 만료 시간을 설정하거나 남은 TTL을 확인한다.
- TTL 단위는 초이며 `0`은 허용하지 않는다.

세부 동작 계약은 [API Contract](docs/spec/API_CONTRACT.md) 문서를 따른다.

## 발표 기준 정리
- 해시 테이블을 선택한 이유:
  - 문자열 key 기준 조회, 저장, 삭제를 빠르게 처리할 수 있어 Mini Redis 핵심 구조에 맞다.
- 내부 구조 설명 포인트:
  - 인메모리 `Map<Key, Entry>` 구조
  - `Entry = { value, expiresAt | null }`
  - `set/get/delete/expire/ttl`가 각각 어떤 상태를 바꾸는지
- 데모 순서:
  - `POST /kv` 저장
  - `GET /kv/{key}` 조회
  - `POST /kv/{key}/expire` 후 만료 전/후 비교
  - `GET /demo/data-cache?key=sample` 첫 호출과 재호출 비교
  - 동시성 기준 설명
- 테스트와 성능 비교:
  - 단위 테스트로 저장/조회/삭제/TTL 핵심 동작을 검증한다.
  - 기능 테스트로 외부 API 사용 흐름과 캐싱 데모를 검증한다.
  - 벤치마크로 cache hit vs no-cache 차이를 설명한다.

## 데모 시나리오
- `SET`, `GET`, `DELETE` 기본 흐름을 시연한다.
- TTL이 있는 데이터를 저장한 뒤 만료 전후 차이를 보여준다.
- MongoDB `dummy_items` 조회 결과를 캐싱한 뒤, 같은 `key` 재요청에서 캐시 hit가 나는 흐름을 보여준다.
- 같은 `key` 요청은 순차 처리하고, 다른 `key` 요청은 병렬 처리하는 동시성 기준을 설명한다.

## 실행 방법
구현이 완료되면 아래 정보만 채운다.
- 설치 방법
- API 서버 실행 명령
- 테스트 실행 명령
- 벤치마크 실행 명령

## 상세 문서
- [Project Spec](docs/spec/PROJECT_SPEC.md)
- [API Contract](docs/spec/API_CONTRACT.md)
- [System Design](docs/architecture/SYSTEM_DESIGN.md)
- [Team Conventions](docs/process/TEAM_CONVENTIONS.md)
- [Test Strategy](docs/process/TEST_STRATEGY.md)
- [Workstream Plan](docs/planning/WORKSTREAM_PLAN.md)
- [Decision Log](docs/decisions/DECISION_LOG.md)
