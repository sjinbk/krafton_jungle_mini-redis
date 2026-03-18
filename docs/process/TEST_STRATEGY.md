# Test Strategy

이 문서는 구현 전 고정되는 테스트 기준의 원본이다.

## 테스트 계층
- 단위 테스트
  - store / ttl
  - kv service
  - demo cache service
  - seat reservation demo service
  - performance benchmark helper
- 기능 테스트
  - FastAPI HTTP API end-to-end
  - 데모 페이지 HTML 노출 확인

## 필수 검증 항목
- KV 저장/조회/삭제
- TTL 설정, 조회, 만료, lazy expiration
- MongoDB origin -> cache write -> cache hit
- empty origin result 미캐시 처리
- cache compare API 응답 구조
- seat reservation API 응답 구조
- single-thread executor 공유에 따른 직렬 처리 보장

## Seat Reservation Demo Tests
- `50석 / 100요청`에서 `reservedCount == 50`
- `50석 / 100요청`에서 `soldOutCount == 50`
- 성공 항목의 `seatNumber`는 `1..50` 범위에서 중복 없이 배정된다
- 모든 timeline 항목은 `queueOrder`를 가진다
- timeline은 queue 순서대로 직렬 실행 흔적을 보여준다
- `seatLimit`, `requestCount` validation error를 반환한다

## Integration Tests
- `POST /demo/concurrency/seat-reservation` 기본값 호출
- custom `seatLimit`, `requestCount` 호출
- 결과 timeline 길이 == `requestCount`
- 성공 항목은 `statusCode == 200`
- 실패 항목은 `statusCode == 409`
- 데모 페이지에 좌석 예약 동시성 UI가 노출된다

## Regression Scope
- `POST /demo/performance/cache-compare`는 기존처럼 유지한다
- KV API와 demo cache API는 기존 시나리오를 계속 통과해야 한다
