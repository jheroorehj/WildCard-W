# DB Schema Guide

이 폴더는 Supabase DB 스키마/정책 변경을 기록하는 용도입니다.
실제 반영은 Supabase 콘솔의 SQL Editor에서 실행합니다.

## 폴더 구조
- migrations/: 버전별 SQL 변경 (절대 수정하지 말고 새 파일 추가)
- seed/: 샘플/더미 데이터
- docs/: 스키마 설명서

## 작업 흐름
1) migrations/에 새 SQL 파일 추가 (예: 001_create_tables.sql)
2) Supabase SQL Editor에 붙여넣고 실행
3) 실행 결과를 docs/schema.md에 기록

## 실행 순서
파일명 숫자 오름차순으로 실행합니다.
