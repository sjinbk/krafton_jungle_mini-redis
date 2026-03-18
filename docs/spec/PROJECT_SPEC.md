# Project Spec

이 문서는 프로젝트 목표, 범위, 요구사항, 수용 기준, 고정 정책의 원본이다.  
제품 범위 판단은 `README.md`보다 이 문서를 우선한다.

## 목표
- 해시 테이블 기반 인메모리 `Mini Redis`를 구현한다.
- FastAPI 기반 HTTP JSON API를 제공한다.
- TTL, MongoDB 기반 cache-aside, 단일 스레드 직렬 처리 시연까지 포함한다.
- 발표에서 내부 로직과 동시성 처리 방식을 직접 설명할 수 있어야 한다.

## v1 범위
- 지원 명령
  - `SET`
  - `GET`
  - `DELETE`
  - `EXPIRE`
  - `TTL`
- FastAPI 기반 HTTP JSON 공개 API
- 루트 경로(`/`)에서 제공하는 단일 HTML 데모 페이지
- MongoDB seeded dummy data를 origin으로 사용하는 cache-aside 시나리오
- 단위 테스트
- 기능 테스트
- cache hit / no-cache 성능 비교
- 좌석 예약 기반 동시성 시연
- README 기반 소개 및 데모 정리

## 제외 범위
- Redis 프로토콜 호환
- 분산 처리, 복제, 샤딩
- 디스크 persistence 필수 구현
- 외부 API 연동
- background cleanup worker
- 추가 명령(`INCR`, `MGET`) 확장

## 핵심 요구사항
- 문자열 key 기준으로 값을 저장, 조회, 삭제할 수 있어야 한다.
- TTL을 설정하고 조회할 수 있어야 한다.
- 만료된 키는 조회 시점에 제거되어야 한다.
- 공개 인터페이스는 FastAPI 기반 HTTP JSON API여야 한다.
- 캐시 시나리오는 외부 API 없이 MongoDB seeded data를 origin으로 사용해야 한다.
- 캐시 데모는 첫 조회와 재조회에서 `origin`과 `cache` 흐름을 구분해 보여줘야 한다.
- 단일 페이지 데모 UI에서 KV, cache demo, performance, concurrency 흐름을 바로 실행할 수 있어야 한다.
- 동시성 시연은 `50석 제한 + 100요청`에서 싱글 스레드 직렬 처리로 50개만 예약 성공하고 50개는 매진 실패로 끝나는 흐름을 보여줘야 한다.

## 제약
- 구현은 단일 프로세스 기준으로 동작한다.
- Mini Redis store는 인메모리 해시 테이블 구조를 사용한다.
- MongoDB는 cache-aside 시나리오의 origin 저장소 역할만 맡는다.
- 병합 충돌 위험이 큰 파일 수정은 최소화한다.
- 테스트 없이 구현 완료로 간주하지 않는다.

## 고정 정책
- 공개 인터페이스는 FastAPI HTTP JSON API로 고정한다.
- TTL 단위는 초(`seconds`)다.
- `ttlSeconds = 0`은 허용하지 않고 `INVALID_TTL`로 처리한다.
- cache demo 기본 TTL은 `15초`다.
- 동시성 시연과 주요 서비스 명령은 하나의 shared command executor thread에서 순차 처리한다.
- 좌석 예약 시연 기본값은 `seatLimit = 50`, `requestCount = 100`이다.
- 좌석 예약 시연에서 초과 요청은 큐 미진입이 아니라 `soldOut` 실패로 종료한다.

## Definition of Done
- KV API와 TTL API가 계약대로 동작한다.
- cache 시나리오가 DB origin과 cache hit를 구분해 보여준다.
- 좌석 예약 동시성 데모가 순차 처리 결과를 `timeline`으로 보여준다.
- 단위 테스트와 기능 테스트가 준비되어 있다.
- README에 실행 방법, 데모 흐름, 성능 비교, 동시성 시연이 반영되어 있다.

## 수용 기준
- `AC-01`: `POST /kv`로 값을 저장할 수 있다.
- `AC-02`: `GET /kv/{key}`로 값을 조회할 수 있다.
- `AC-03`: `DELETE /kv/{key}`로 값을 삭제할 수 있다.
- `AC-04`: `POST /kv/{key}/expire`로 TTL을 설정할 수 있다.
- `AC-05`: 만료 후 조회 시 `404` miss를 반환하고 내부 저장소에서도 제거된다.
- `AC-06`: `GET /demo/data-cache` 첫 요청은 `source = origin`을 반환한다.
- `AC-07`: TTL 이내 재요청은 `source = cache`를 반환한다.
- `AC-08`: TTL 만료 후 재요청은 다시 `source = origin`을 반환한다.
- `AC-09`: 잘못된 입력은 `400` validation error로 처리한다.
- `AC-10`: origin 결과가 비어 있으면 `200`과 빈 `items`를 반환하고 캐시하지 않는다.
- `AC-11`: `POST /demo/performance/cache-compare`는 cold origin vs warm cache 비교 결과를 반환한다.
- `AC-12`: `POST /demo/concurrency/seat-reservation`는 기본값 호출 시 `reservedCount = 50`, `soldOutCount = 50`을 반환한다.
- `AC-13`: 좌석 예약 `timeline`은 `requestCount` 길이와 같은 결과를 포함한다.
- `AC-14`: 성공 항목은 `seatNumber`를 갖고 실패 항목은 `seatNumber = null`이다.
- `AC-15`: README와 데모 페이지가 좌석 예약 동시성 시연 흐름을 설명한다.
