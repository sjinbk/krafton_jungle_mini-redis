# Project Spec

이 문서는 프로젝트 목표, 범위, 요구사항, 수용 기준, 고정 정책의 단일 원본이다. 제품 수준의 판단은 README와 이 문서를 기준으로 하며, 구현 상세보다 범위와 정책을 먼저 잠근다.

## 목표
- 해시 테이블 기반 인메모리 `Mini Redis`를 구현한다.
- FastAPI 기반 HTTP JSON API를 제공한다.
- TTL, DB 더미 데이터 캐싱, 테스트, 성능 비교까지 포함해 데모 가능한 결과를 만든다.
- 팀원이 핵심 로직과 캐시 흐름을 직접 설명할 수 있어야 한다.

## 기술 선택 근거
- 과제 기준상 프레임워크 선택은 자유다.
- v1은 구현 속도, validation, 테스트 단순성을 위해 `FastAPI`를 선택한다.
- 과제의 "API 응답 값을 Mini Redis에 저장" 요구는 재현 가능한 데모와 테스트 중심으로 해석한다.
- 따라서 v1 캐싱 시나리오의 origin은 외부 API 대신 MongoDB에 사전 적재한 dummy data로 단순화한다.

## v1 범위
- 핵심 명령:
  - `SET`
  - `GET`
  - `DELETE`
  - `EXPIRE`
  - `TTL`
- FastAPI 기반 HTTP JSON 공개 API
- FastAPI 내부 경로에서 제공하는 단일 HTML 데모 페이지
- MongoDB에 미리 적재한 더미 데이터를 origin으로 사용하는 캐싱 시나리오
- 단위 테스트
- 기능 테스트
- 캐시 hit / no-cache 성능 비교
- 동시 GET burst 성능 비교
- README 기반 소개 및 데모 정리

## 제외 범위
- Redis 프로토콜 완전 호환
- 분산 처리, 복제, 샤딩
- Mini Redis 저장소의 영속성 필수 구현
- 외부 API 연동
- 주기적 데이터 수집 파이프라인
- 추가 명령(`INCR`, `MGET` 등) 확장

## 핵심 요구사항
- 문자열 키 기준으로 값을 저장, 조회, 삭제할 수 있어야 한다.
- 키별 TTL을 설정하고 조회할 수 있어야 한다.
- 만료된 키는 조회 시점에 제거되어야 한다.
- 외부 공개 인터페이스는 FastAPI 기반 HTTP JSON API여야 한다.
- 캐싱 시나리오는 외부 API 호출 없이 DB에 적재된 더미 데이터를 origin으로 사용해야 한다.
- 캐싱 데모는 첫 조회와 재조회에서 origin과 cache 흐름을 구분해 보여줘야 한다.
- 단위 테스트와 기능 테스트가 있어야 한다.
- 캐시 사용 전후 성능 차이를 비교할 수 있어야 한다.
- 사용자가 저장 데이터를 무효화할 수 있는 방법이 문서와 API 계약에 정의되어야 한다.

## 핵심 제약
- 구현은 단일 프로세스 기준으로 동작해야 한다.
- Mini Redis cache store는 인메모리 해시 테이블 구조를 기준으로 한다.
- MongoDB는 캐싱 시나리오의 origin 데이터 저장소 역할만 맡는다.
- origin 데이터는 외부 API 호출이 아니라 사전에 적재한 dummy document로 준비한다.
- 병합 충돌이 큰 파일 수정은 최소화해야 한다.
- 핵심 로직은 팀원이 설명 가능해야 한다.
- 테스트 없이 핵심 로직을 완료로 간주하지 않는다.

## 고정된 제품 정책
- 공개 인터페이스는 FastAPI 기반 HTTP JSON API로 고정한다.
- TTL 단위는 초(`seconds`)로 고정한다.
- `ttlSeconds = 0`은 허용하지 않고 `INVALID_TTL`로 처리한다.
- 기존 키에 `SET`을 TTL 없이 다시 수행하면 기존 만료 정보는 제거한다.
- 만료된 키는 반환하지 않고 miss로 처리한다.
- v1 무효화 수단은 `DELETE`, `EXPIRE`, TTL 만료, `SET` overwrite로 한정한다.
- 별도 `deprecated` 상태나 soft delete 상태 전이는 도입하지 않는다.
- 캐싱 시나리오의 origin 데이터는 MongoDB 컬렉션의 dummy document로 고정한다.
- 캐싱 시나리오의 origin collection 이름은 `dummy_items`로 고정한다.
- 캐싱 시나리오의 기본 TTL은 `15`초를 기준으로 한다.

상세 요청/응답 계약은 [API_CONTRACT.md](API_CONTRACT.md)를 기준으로 한다.

## 현재 고정된 구현 결정
| 항목 | 현재 상태 | 메모 |
|------|-----------|------|
| runtime | `python 3.11` | HTTP 서버 및 테스트 런타임 |
| framework | `FastAPI` | 공개 HTTP JSON API 제공 |
| package manager | `pip` | 기본 의존성 관리 방식 |
| app port | `8000` | Uvicorn / FastAPI 기본 포트 |
| database | `MongoDB` | 캐싱용 더미 데이터 보관 |
| origin source | seeded dummy data | 외부 API 연동 없음 |
| default TTL | `15초` | 기본 TTL 기준값 |

## 지금 미뤄도 되는 항목
- persistence
- cleanup worker
- 추가 명령

## Optional 검토 항목
- persistence
  - 후보: `append-only log`, `snapshot`, `hybrid`
  - v1에서는 구현하지 않고 검토 결과만 남긴다.
  - 이유: 하루 과제 범위에서 핵심 기능, 테스트, 데모 완성도를 우선한다.

## Definition of Done
- KV API와 TTL API가 계약대로 동작한다.
- 캐싱 시나리오가 DB origin과 cache hit를 구분해 보여준다.
- 최소 단위 테스트와 기능 테스트가 준비된다.
- 단일 페이지 데모 UI에서 KV, cache demo, performance, concurrency 흐름을 바로 실행할 수 있다.
- 성능 비교 결과를 README에 기록할 수 있다.

## 수용 기준
- `AC-01`
  - `POST /kv`로 값을 저장할 수 있다.
- `AC-02`
  - `GET /kv/{key}`로 값을 조회할 수 있다.
- `AC-03`
  - `DELETE /kv/{key}`로 값을 삭제할 수 있다.
- `AC-04`
  - `POST /kv/{key}/expire`로 TTL을 설정할 수 있다.
- `AC-05`
  - 만료된 키 조회 시 404 계열 miss 응답과 함께 내부에서 제거된다.
- `AC-06`
  - 캐싱 시나리오 첫 요청은 DB origin에서 읽고 `source = origin`을 반환한다.
- `AC-07`
  - 같은 조건으로 TTL 안에 다시 요청하면 `source = cache`를 반환한다.
- `AC-08`
  - TTL 만료 후 다시 요청하면 DB origin을 다시 읽고 payload를 갱신한다.
- `AC-09`
  - 잘못된 요청 값은 `400` 계열 validation 오류로 처리된다.
- `AC-10`
  - origin 결과가 비어 있으면 `200`과 빈 `items`를 반환하고 캐시에 저장하지 않는다.
- `AC-11`
  - 테스트가 주요 정상, 실패, 만료 시나리오를 커버한다.
- `AC-12`
  - README에 실행 방법, 데모 흐름, 테스트, 성능 비교가 반영된다.
- `AC-13`
  - 데이터 무효화 방식이 `DELETE`, `EXPIRE`, TTL 만료, overwrite 기준으로 문서화된다.
- `AC-14`
  - optional persistence는 구현 여부가 아니라 검토 결과와 제외 이유가 문서에 정리된다.
