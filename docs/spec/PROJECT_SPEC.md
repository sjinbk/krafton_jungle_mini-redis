# Project Spec

이 문서는 프로젝트 목표, 범위, 요구사항, 수용 기준, 고정 정책의 단일 원본이다. 제품 수준의 판단은 이 문서를 기준으로 한다.

## 목표
- 해시 테이블 기반 인메모리 `Mini Redis`를 구현한다.
- FastAPI 기반 HTTP JSON API를 제공한다.
- TTL, MongoDB 더미 뉴스 헤드라인 캐싱, 테스트, 성능 비교까지 포함해 데모 가능한 결과를 만든다.
- 팀원이 핵심 로직과 캐시 흐름을 설명할 수 있어야 한다.

## v1 범위
- 핵심 명령:
  - `SET`
  - `GET`
  - `DELETE`
  - `EXPIRE`
  - `TTL`
- FastAPI 기반 HTTP JSON 공개 API
- MongoDB에 미리 적재한 더미 뉴스 헤드라인을 origin으로 사용하는 캐싱 데모
- 단위 테스트
- 기능 테스트
- 캐시 hit / MongoDB no-cache 성능 비교
- README 기반 소개 및 데모 정리

## 제외 범위
- Redis 프로토콜 완전 호환
- 분산 처리, 복제, 샤딩
- Mini Redis 저장소의 영속성 필수 구현
- 외부 뉴스 API 연동
- 주기적 데이터 수집 파이프라인
- 추가 명령(`INCR`, `MGET` 등) 확장

## 핵심 요구사항
- 문자열 키 기준으로 값을 저장, 조회, 삭제할 수 있어야 한다.
- 키별 TTL을 설정하고 조회할 수 있어야 한다.
- 만료된 키는 조회 시점에 제거되어야 한다.
- 외부 공개 인터페이스는 FastAPI 기반 HTTP JSON API여야 한다.
- MongoDB 더미 데이터 조회 결과를 Mini Redis에 저장해 재사용하는 데모 흐름이 있어야 한다.
- 뉴스 캐싱 데모는 동일 topic 재요청 시 `origin`과 `cache`를 구분해 보여줘야 한다.
- 단위 테스트와 기능 테스트가 있어야 한다.
- 캐시 사용 전후 성능 차이를 비교할 수 있어야 한다.

## 핵심 제약
- 구현은 단일 프로세스 기준으로 동작해야 한다.
- Mini Redis cache store는 인메모리 해시 테이블 구조를 기준으로 한다.
- MongoDB는 뉴스 캐싱 데모의 origin 데이터 소스 역할만 맡는다.
- origin 데이터는 외부 API 호출이 아니라 사전에 적재한 dummy document로 준비한다.
- 병합 충돌이 큰 파일 수정은 최소화해야 한다.
- 핵심 로직은 팀원이 설명 가능해야 한다.
- 선택 과제는 v1 핵심 경로와 분리해야 한다.
- 테스트 없이 핵심 로직을 완료로 간주하지 않는다.

## 고정된 제품 정책
- 공개 인터페이스는 FastAPI 기반 HTTP JSON API로 고정한다.
- TTL 단위는 초(`seconds`)로 고정한다.
- `ttlSeconds = 0`은 허용하지 않고 `INVALID_TTL`로 처리한다.
- 기존 키에 `SET`을 TTL 없이 다시 수행하면 기존 만료 정보는 제거한다.
- 만료된 키는 반환하지 않고 miss로 처리한다.
- 뉴스 캐싱 데모의 origin 데이터는 MongoDB 컬렉션의 dummy headline document로 고정한다.
- 뉴스 캐시 키는 `news:{topic}:kr` 형식을 사용하고 기본 TTL은 `15`초로 고정한다.
- 뉴스 캐싱 데모의 topic 허용 범위는 `ai`, `gaming`, `economy`로 고정한다.

상세 요청/응답 계약은 [API_CONTRACT.md](API_CONTRACT.md)를 기준으로 한다.

## 현재 고정된 구현 결정
| 항목 | 현재 상태 | 메모 |
|------|-----------|------|
| runtime | `python 3.11` | HTTP 서버 및 테스트 런타임 |
| framework | `FastAPI` | 공개 HTTP JSON API 제공 |
| package manager | `pip` | 기본 의존성 관리 방식 |
| app port | `8000` | Uvicorn / FastAPI 기본 포트 |
| database | `MongoDB` | 뉴스 더미 데이터 보관 |
| origin source | seeded dummy headlines | 외부 API 연동 없음 |
| default TTL | `15초` | 뉴스 캐시 기본 TTL |
| allowed topics | `ai`, `gaming`, `economy` | 데모 범위 기준 |

## 지금 미뤄도 되는 항목
- persistence
- cleanup worker
- 추가 명령
- 프론트엔드

## Definition of Done
- KV API와 TTL API가 계약대로 동작한다.
- `GET /demo/headlines-cache`가 MongoDB origin과 cache hit를 구분해 보여준다.
- 최소 단위 테스트와 기능 테스트가 준비된다.
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
  - `GET /demo/headlines-cache?topic=ai` 첫 요청은 MongoDB에서 읽고 `source = origin`을 반환한다.
- `AC-07`
  - 같은 topic을 TTL 안에 다시 요청하면 `source = cache`를 반환한다.
- `AC-08`
  - TTL 만료 후 같은 topic을 다시 요청하면 MongoDB를 다시 읽고 payload를 갱신한다.
- `AC-09`
  - 지원하지 않는 `topic`은 `400`과 `INVALID_TOPIC`으로 처리된다.
- `AC-10`
  - 유효한 `topic`인데 MongoDB 결과가 비어 있으면 `200`과 빈 `articles`를 반환하고 캐시에 저장하지 않는다.
- `AC-11`
  - 테스트가 주요 정상, 실패, 만료 시나리오를 커버한다.
- `AC-12`
  - README에 실행 방법, 데모 흐름, 테스트, 성능 비교가 반영된다.
