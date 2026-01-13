# 브랜치 작업 워크플로우 가이드

## 📌 현재 상태

현재 `main` 브랜치는 최신 상태이며, 다음 작업들이 완료되었습니다:
- ✅ Frontend 설정 (React + Upstage Solar Pro 2)
- ✅ 환경 변수 통합 (.env.local)
- ✅ README 및 문서화 완료
- ✅ 모든 변경사항 커밋 및 push 완료

## 🚀 새로운 기능 개발 시작하기

### 1. 항상 최신 main에서 시작

```bash
# main 브랜치로 이동
git checkout main

# 최신 변경사항 가져오기
git pull origin main
```

### 2. Feature 브랜치 생성

브랜치 네이밍 규칙: `<type>/<issue-number>-<short-description>`

```bash
# 예시: 새로운 기능 추가
git checkout -b feat/001-add-chart-visualization

# 예시: 버그 수정
git checkout -b fix/002-api-error-handling

# 예시: 리팩토링
git checkout -b refactor/003-optimize-llm-calls
```

### 3. 작업 및 커밋

```bash
# 파일 수정 후...
git add .

# 커밋 메시지 규칙에 따라 커밋
git commit -m "feat: Add chart visualization component"
```

### 4. 작업 중 main 브랜치 변경사항 반영

다른 팀원이 main에 변경사항을 push한 경우:

```bash
# 최신 main 가져오기
git fetch origin

# 현재 브랜치에 main의 변경사항 반영
git rebase origin/main

# 충돌 발생 시 해결 후
git add .
git rebase --continue
```

### 5. 원격에 브랜치 push

```bash
# 처음 push할 때
git push -u origin feat/001-add-chart-visualization

# 이후 push
git push origin feat/001-add-chart-visualization

# rebase 후 push (이미 push한 브랜치인 경우)
git push origin feat/001-add-chart-visualization --force-with-lease
```

### 6. Pull Request 생성

GitHub에서 Pull Request를 생성하고 팀원들에게 리뷰 요청

### 7. 병합 후 정리

```bash
# main으로 돌아가기
git checkout main

# 최신 상태로 업데이트
git pull origin main

# 로컬 브랜치 삭제
git branch -d feat/001-add-chart-visualization

# 원격 브랜치 삭제 (GitHub에서 자동으로 삭제되지 않은 경우)
git push origin --delete feat/001-add-chart-visualization
```

## 📋 빠른 참조 명령어

### 새 기능 시작
```bash
git checkout main
git pull origin main
git checkout -b feat/XXX-feature-name
```

### 작업 중 main 업데이트 반영
```bash
git fetch origin
git rebase origin/main
```

### 작업 완료 후
```bash
git push origin feat/XXX-feature-name
# GitHub에서 PR 생성
```

## 🔥 자주 사용하는 시나리오

### 시나리오 1: 작업 중 main이 업데이트된 경우

```bash
# 1. 현재 작업 확인
git status

# 2. 작업 중이면 커밋 또는 stash
git stash  # 또는 git commit

# 3. main 업데이트 반영
git fetch origin
git rebase origin/main

# 4. stash했다면 복원
git stash pop

# 5. 충돌 해결 후 계속
git add .
git rebase --continue
```

### 시나리오 2: 실수로 main에서 작업한 경우

```bash
# 1. 새 브랜치 생성 (현재 변경사항 유지)
git checkout -b feat/XXX-your-feature

# 2. main을 원래 상태로 되돌리기
git checkout main
git reset --hard origin/main
```

### 시나리오 3: 여러 커밋을 하나로 합치기

```bash
# 최근 3개 커밋을 하나로 합치기
git rebase -i HEAD~3

# 에디터에서:
# 첫 번째는 'pick'으로 유지
# 나머지는 'squash' 또는 's'로 변경
```

## 📝 커밋 메시지 템플릿

```
<type>: <subject>

<body>

<footer>
```

### Type 종류
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정 변경

### 예시
```
feat: Add investment chart visualization

- Implement line chart for stock price history
- Add interactive tooltips
- Support multiple stock comparison

Closes #123
```

## ⚠️ 주의사항

1. **절대 main 브랜치에 직접 push 금지**
   - 항상 feature 브랜치에서 작업
   - PR을 통해서만 main에 병합

2. **Force push 사용 시 주의**
   - `--force` 대신 `--force-with-lease` 사용
   - 다른 사람과 공유하는 브랜치에서는 가급적 사용 안 함

3. **작업 시작 전 항상 pull**
   - 최신 main에서 브랜치 생성
   - 충돌 최소화

4. **커밋은 작고 명확하게**
   - 하나의 커밋은 하나의 목적
   - 의미 있는 단위로 커밋

## 🛠 트러블슈팅

### rebase 중 충돌이 너무 복잡한 경우
```bash
# rebase 취소
git rebase --abort

# merge 방식으로 전환
git merge origin/main
```

### 실수로 push한 경우
```bash
# 마지막 커밋 취소 (로컬만)
git reset --soft HEAD~1

# 원격도 되돌리기 (주의!)
git push origin feat/XXX --force-with-lease
```

### 브랜치 목록 정리
```bash
# 로컬 브랜치 목록
git branch

# 병합된 브랜치 삭제
git branch -d branch-name

# 강제 삭제
git branch -D branch-name

# 원격에서 삭제된 브랜치 로컬에서도 정리
git fetch --prune
```

## 📚 추가 리소스

- [Git Collaboration Guide](GIT_COLLABORATION_GUIDE.md) - 전체 협업 가이드
- [README.md](README.md) - 프로젝트 설정 가이드
- [GitHub Flow](https://guides.github.com/introduction/flow/) - GitHub 공식 워크플로우

---

**현재 프로젝트 상태**: ✅ Main 브랜치 최신화 완료
**다음 단계**: Feature 브랜치를 생성하여 작업 시작
