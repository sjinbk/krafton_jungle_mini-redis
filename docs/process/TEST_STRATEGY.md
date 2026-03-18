# Test Strategy

이 문서는 구현 전 고정되는 테스트 기준의 원본이다.

## 테스트 계층
- 단위 테스트
  - store / ttl
  - kv service
  - demo cache service
  - performance benchmark helper
  - seat reservation demo service
- 기능 테스트
  - FastAPI HTTP API end-to-end
  - 데모 페이지 HTML 노출 확인
  - shared executor 직렬 처리 보장 확인

## 필수 검증 항목
- KV 저장/조회/삭제
- TTL 설정, 조회, 만료, lazy expiration
- TTL 없이 덮어쓰기 시 기존 만료 정보 제거
- MongoDB origin -> cache write -> cache hit
- empty origin result 미캐시 처리
- cache compare API 응답 구조
- seat reservation API 응답 구조
- KV와 cache demo 요청이 같은 single-thread executor를 공유하는지 확인

## KV / TTL Tests
- 새 key 저장 시 `201`, 기존 key 갱신 시 `200`
- 만료된 key는 조회 시 `KEY_NOT_FOUND`
- `GET /kv/{key}/ttl`은 TTL 유무와 남은 시간을 반환
- invalid key, invalid ttl은 각각 올바른 에러 코드를 반환

## Cache Demo Tests
- `GET /demo/data-cache?key=sample` 첫 호출은 `source = origin`
- 같은 key 재호출은 `source = cache`
- TTL 만료 뒤 다시 호출하면 `source = origin`
- origin 결과가 비어 있으면 `items = []`를 반환하고 캐시하지 않는다

## Performance Compare Tests
- 기본 호출은 `scenario = "cacheCompare"`를 반환한다
- 기본 `key = sample`, `iterations = 20`을 사용한다
- `apiTiming`, `serviceTiming` 모두 평균 시간과 speedup 필드를 포함한다
- benchmark 대상 데이터가 없을 때는 실패를 반환할 수 있다

## Seat Reservation Demo Tests
- `50석 / 100요청`에서 `reservedCount == 50`
- `50석 / 100요청`에서 `soldOutCount == 50`
- 성공 항목의 `seatNumber`는 `1..50` 범위에서 중복 없이 배정된다
- 실패 항목의 `seatNumber`는 `null`이다
- 모든 `timeline` 항목은 `queueOrder`를 가진다
- `timeline`은 queue 순서대로 직렬 실행 흔적을 보여준다
- `seatLimit`, `requestCount` validation error를 반환한다

## Demo Page Tests
- 루트 경로 `/`가 HTML 페이지를 반환한다
- 페이지에 KV, cache demo, performance, seat reservation 섹션이 노출된다
- 제거된 구형 시나리오 문구가 남아 있지 않아야 한다

## Regression Scope
- `POST /demo/performance/cache-compare`는 기존 계약을 유지한다
- KV API와 demo cache API는 기존 시나리오를 계속 통과해야 한다
- 직렬 executor 공유 보장은 회귀 없이 유지되어야 한다
